import numpy as np
import torch, os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from CNN_128x128 import CNN_128x128
from NN_128x128 import NN_128x128
from utils import compute_metrics
import matplotlib.pyplot as plt
import sys
import seaborn as sns

import utils_our
import kymatio.torch as kt

# test
import yaml
with open('parameters.yaml', 'r') as f:
    settings = yaml.load(f, Loader=yaml.loader.FullLoader)
print(settings)

data_path = settings['data_path']
model_train_path = settings['model_train_path']
if not os.path.exists(model_train_path):                 # create a directory where to save the best model
    os.makedirs(model_train_path)
test_perc = settings['test_perc']
batch_size = settings['batch_size']
learning_rate = settings['learning_rate']
momentum = settings['momentum']
num_epochs = settings['num_epochs']
J = settings['J']
imageSize = settings['imageSize']
order = settings['order']      
lab_classes = settings['lab_classes']

# Set device where to run the model. GPU if available, otherwise cpu (very slow with deep learning models)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print('Available device: ', device)

### DATA LOADING ###

def train(trainset):
    ### MODEL VARIABLES ###
    # Define useful variables
    best_acc = 0.0

    # Variables to store the results
    losses = []
    acc_train = []
    pred_label_train = torch.empty((0)).to(device)    # .to(device) to move the data/model on GPU or CPU (default)
    true_label_train = torch.empty((0)).to(device)


    ### CREATE MODEL ###

    # Model
    model = NN_128x128(input_channel=3, num_classes=len(lab_classes) ).to(device)

    # Optimizer
    optim = torch.optim.SGD(model.parameters(), lr = learning_rate, momentum=momentum)

    # Loss function
    criterion = torch.nn.CrossEntropyLoss()



    ### FIT MODEL ###
    for epoch in range(num_epochs):
        # Train step
        model.train()                                                   # tells to the model you are in training mode (batchnorm and dropout layers work)
        for data_tr in trainset:
            optim.zero_grad()

            x,y = data_tr                        # unlist the data from the train set  
            x = x.to(device)      
            y = y.to(device)

            y_pred = model(x)                                        # run the model
            loss = criterion(y_pred,y)                               # compute loss
            _,pred = y_pred.max(1)                                      # get the index == class of the output along the rows (each sample)
            pred_label_train = torch.cat((pred_label_train,pred),dim=0)
            true_label_train = torch.cat((true_label_train,y),dim=0)
            loss.backward()                                             # compute backpropagation
            optim.step()                                                # parameter update

        losses.append(loss.cpu().detach().numpy())
        acc_t = accuracy_score(true_label_train.cpu(),pred_label_train.cpu())
        acc_train.append(acc_t)
        print("Epoch: {}/{}, loss = {:.4f} - acc = {:.4f}".format(epoch + 1, num_epochs, loss, acc_t))
        if acc_t > best_acc:                                                            # save the best model (the highest accuracy in validation)
            torch.save(model.state_dict(), model_train_path + 'NN_128x128_best_model_trained.pt')
            best_acc = acc_t

        # Reinitialize the variables to compute accuracy
        pred_label_train = torch.empty((0)).to(device)
        true_label_train = torch.empty((0)).to(device)

def test(testset):
    ### TEST MODEL ###
    model_test = NN_128x128(input_channel=3,num_classes=len(lab_classes) ).to(device)                # Initialize a new model
    model_test.load_state_dict(torch.load(model_train_path+'NN_128x128_best_model_trained.pt'))   # Load the model

    pred_label_test = torch.empty((0,len(lab_classes) )).to(device)
    true_label_test = torch.empty((0)).to(device)

    with torch.no_grad():
        for data in testset:
            X_te, y_te = data
            X_te = X_te.to(device)
            y_te = y_te.to(device)
            output_test = model_test(X_te)
            pred_label_test = torch.cat((pred_label_test,output_test),dim=0)
            true_label_test = torch.cat((true_label_test,y_te),dim=0)

    return compute_metrics(y_true=true_label_test,y_pred=pred_label_test,lab_classes=lab_classes)    # function to compute the metrics (accuracy and confusion matrix)


if __name__ == "__main__":
    # Split in train and test set
    trainset, testset = utils_our.batcher(batch_size = batch_size, *train_test_split(*utils_our.loadData(data_path, lab_classes), test_size=test_perc))

    ### SCATTERING DATA ###
    scatter = kt.Scattering2D(J, shape = imageSize, max_order = order)
    scatter = scatter.to(device)    

    print(f'Calculating scattering coefficients of data in {len(trainset)} batches of {batch_size} elements each for training')
    training_scatters, train_lbls = utils_our.scatter_mem(batch_size,device,scatter,trainset)
    if training_scatters is None:
        print('Error during scatter_mem!')
        sys.exit()
    print(f'Calculating scattering coefficients of data in {len(testset)} batches of {batch_size} elements each for testing')
    testing_scatters, test_lbls = utils_our.scatter_mem(batch_size,device,scatter,testset)
    if testing_scatters is None:
        print('Error during scatter_mem!')
        sys.exit()


    trainset, testset = utils_our.batcher(training_scatters, testing_scatters, train_lbls, test_lbls, batch_size = batch_size)

    train(trainset)
    confmat = test(testset)       
        
    plt.figure(figsize=(7,5))
    sns.heatmap(confmat,annot=True)
    plt.title('confusion matrix: test set')
    plt.xlabel('predicted')
    plt.ylabel('true')
    plt.show()
'''
# Plot the results
plt.figure(figsize=(8,5))
plt.plot(list(range(num_epochs)), losses)
plt.title("Learning curve")
plt.xlabel("Epochs")
plt.ylabel("Loss")
plt.tight_layout()
plt.show()

plt.figure(figsize=(8,5))
plt.plot(list(range(num_epochs)), acc_train)
plt.title("Accuracy curve")
plt.xlabel("Epochs")
plt.ylabel("Accuracy")
plt.tight_layout()
plt.show()'''