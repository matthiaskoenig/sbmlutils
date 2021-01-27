"""
Test model creation.
"""
import pytest

from sbmlutils.examples.models.annotation import annotation_example
from sbmlutils.examples.models.core import (
    amount_species_example,
    assignment_example,
    core_example1,
    core_example2,
    initial_assignment_example,
    reaction_example,
)
from sbmlutils.examples.models.dallaman import factory as dallaman_factory
from sbmlutils.examples.models.demo import factory as demo_factory
from sbmlutils.examples.models.distrib import (
    distrib_comp_example,
    distributions_example,
    uncertainty_example,
)
from sbmlutils.examples.models.fbc import (
    fbc_example1,
    fbc_example2,
    mass_charge_example,
)
from sbmlutils.examples.models.tiny_model import factory as tiny_factory
from sbmlutils.modelcreator.creator import CoreModel, Preprocess


testdata = [
    annotation_example,
    amount_species_example,
    core_example1,
    core_example2,
    dallaman_factory,
    assignment_example,
    initial_assignment_example,
    distrib_comp_example,
    distributions_example,
    uncertainty_example,
    demo_factory,
    fbc_example1,
    fbc_example2,
    mass_charge_example,
    reaction_example,
    tiny_factory,
]


@pytest.mark.parametrize("module", testdata)
def test_create_model(module):
    module.create(tmp=True)


def test_demo():
    model_dict = Preprocess.dict_from_modules(["sbmlutils.examples.models.demo.model"])
    cell_model = CoreModel.from_dict(model_dict)
    cell_model.create_sbml()
