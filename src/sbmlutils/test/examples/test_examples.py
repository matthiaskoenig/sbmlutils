"""Example model creation."""
from typing import Any

import pytest

from sbmlutils.creator import CoreModel, Preprocess
from sbmlutils.examples import (
    amount_species,
    annotation,
    assignment,
    boundary_condition1,
    boundary_condition2,
    core1,
    core2,
    distrib_comp,
    distrib_distributions,
    distrib_uncertainty,
    fbc1,
    fbc2,
    fbc_mass_charge,
    initial_assignment,
    reaction,
    simple_reaction,
)
from sbmlutils.examples.dallaman import factory as dallaman_factory
from sbmlutils.examples.demo import factory as demo_factory
from sbmlutils.examples.tiny_model import factory as tiny_factory


testdata = [
    annotation,
    amount_species,
    boundary_condition1,
    boundary_condition2,
    core1,
    core2,
    dallaman_factory,
    assignment,
    initial_assignment,
    distrib_comp,
    distrib_distributions,
    distrib_uncertainty,
    demo_factory,
    fbc1,
    fbc2,
    fbc_mass_charge,
    reaction,
    simple_reaction,
    tiny_factory,
]


@pytest.mark.parametrize("module", testdata)
def test_create_model(module: Any) -> None:
    module.create(tmp=True)
