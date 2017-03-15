"""
Test cell model creation.

Reading of model dictionaries from given python files
and creation of the SBML.
"""
from __future__ import print_function

from sbmlutils.examples.models.basic import factory as basic_factory
from sbmlutils.examples.models.demo import factory as demo_factory
from sbmlutils.examples.models.glucose import factory as glucose_factory

from sbmlutils.modelcreator.creator import CoreModel, Preprocess
from sbmlutils.examples.models.assignment import factory as assignment_factory


def test_create_assignment():
    """ Create assignment model.
    :return:
    """
    assignment_factory.create(tmp=True)


def test_create_basic():
    """ Create basic model.
    :return:
    """
    basic_factory.create(tmp=True)


def test_create_demo():
    """ Create demo model.
    :return:
    """
    demo_factory.create(tmp=True)


def test_create_glucose():
    """ Create glucose model.
    :return:
    """
    glucose_factory.create(tmp=True)


def test_demo():
    """ Create demo model.
    :return:
    """
    model_dict = Preprocess.dict_from_modules(['sbmlutils.examples.models.demo.Cell'])
    cell_model = CoreModel.from_dict(model_dict)
    cell_model.create_sbml()


def test_galactose():
    """
    Create galactose model.
    :return:
    """
    model_dict = Preprocess.dict_from_modules(
        [
            'sbmlutils.examples.models.hepatocyte',
            'sbmlutils.examples.models.galactose'
        ])

    cell_model = CoreModel.from_dict(model_dict)
    cell_model.create_sbml()
