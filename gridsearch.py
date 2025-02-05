import configurable_classification
import lib.scripts.make_settings
import matlab.engine

parameters_to_modify = {
    'quality_factors': [[3, 2], [3, 3]],
}

for parameter in parameters_to_modify:
    for value in parameters_to_modify[parameter]:
        print('Classification model with {} = {}'.format(parameter, value))
        lib.scripts.make_settings.edit_parameter(parameter, value)
        configurable_classification.classify()