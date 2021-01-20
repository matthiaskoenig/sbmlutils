"""
Test cell model creation.

Reading of model dictionaries from given python files
and creation of the SBML.
"""
import pytest

from sbmlutils.examples.models.annotation import annotation_example
from sbmlutils.examples.models.assignment import assignment_example
from sbmlutils.examples.models.basic import basic_example1, basic_example2
from sbmlutils.examples.models.demo import factory as demo_factory
from sbmlutils.examples.models.distrib import distributions_example, distrib_comp_example, uncertainty_example
from sbmlutils.examples.models.fbc import factory as fbc_factory
from sbmlutils.examples.models.mass_charge_balance import factory as mass_charge_factory
from sbmlutils.examples.models.tiny_model import factory as tiny_factory
from sbmlutils.modelcreator.creator import CoreModel, Preprocess


def test_create_mass_charge():
    mass_charge_factory.create(tmp=True)


def test_create_annotation():
    annotation_example.create(tmp=True)


def test_create_distrib():
    distrib_comp_example.create(tmp=True)
    distributions_example.create(tmp=True)
    uncertainty_example.create(tmp=True)


def test_create_assignment():
    assignment_example.create(tmp=True)


def test_create_basic():
    basic_example1.create(tmp=True)
    basic_example2.create(tmp=True)


def test_create_demo():
    """Create demo model.
    :return:
    """
    demo_factory.create(tmp=True)


def test_demo():
    """Create demo model.
    :return:
    """
    model_dict = Preprocess.dict_from_modules(["sbmlutils.examples.models.demo.model"])
    cell_model = CoreModel.from_dict(model_dict)
    cell_model.create_sbml()


def test_create_example1():
    example1_factory.create(tmp=True)


def test_create_fbc():
    fbc_factory.create(tmp=True)


def test_create_tiny():
    tiny_factory.create(tmp=True)


def test_create_distrib():
    distrib_factory.create_distrib(tmp=True)


def test_create_distrib():
    distrib_factory.create_distrib(tmp=True)
