"""
Create all the example models.
"""
from __future__ import print_function, division
import os
from sbmlutils import modelcreator

models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
model_module = 'sbmlutils.examples.models'


def create_AssignmentTest():
    """ Test model for assignments in PKPD models. """
    name = 'AssignmentTest'
    return modelcreator.create_model(target_dir=os.path.join(models_dir, name, 'results'),
                                     model_inf=['{}.AssignmentTest'.format(model_module)])


def create_demo():
    """ Create demo network. """
    base_dir = os.path.join(models_dir, 'demo')
    target_dir = os.path.join(base_dir, 'results')
    f_annotations = os.path.join(base_dir, 'demo_annotations.xlsx')

    # python model info
    model_info = ['{}.demo'.format(model_module)]

    modelcreator.create_model(target_dir, model_info, f_annotations=None, suffix='_no_annotations')
    return modelcreator.create_model(target_dir, model_info, f_annotations)


def create_test():
    """ Create test model. """
    name = 'test'
    return modelcreator.create_model(target_dir=os.path.join(models_dir, name, 'results'),
                                     model_info=['{}.{}'.format(model_module, 'hepatocyte'),
                                                 '{}.{}'.format(model_module, name)])


#########################################################################
if __name__ == "__main__":
    # ------------------------------------------
    # Test models
    # ------------------------------------------
    # [cell_dict, cell_model] = create_test()
    [cell_dict, cell_model] = create_demo()

    # ------------------------------------------
    # PKPD models
    # ------------------------------------------
    # [cell_dict, cell_model] = create_AssignmentTest()


