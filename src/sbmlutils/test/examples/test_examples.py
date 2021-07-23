"""Example model creation."""
from typing import Any

import pytest

from sbmlutils.examples import (
    amount_species,
    annotation,
    assignment,
    boundary_condition1,
    boundary_condition2,
    core2,
    distrib_comp,
    distrib_distributions,
    distrib_uncertainty,
    fbc1,
    fbc2,
    fbc_mass_charge,
    initial_assignment,
    model_definitions,
    reaction,
    simple_reaction,
    substance_units,
)
from sbmlutils.examples.dallaman import factory as dallaman_factory
from sbmlutils.examples.demo import factory as demo_factory
from sbmlutils.examples.minimal_example import (
    comp_model,
    full_model,
    linear_chain,
    minimal_model,
    model_composition,
    random_network,
)
from sbmlutils.examples.tiny_model import factory as tiny_factory


testdata = [
    annotation,
    amount_species,
    boundary_condition1,
    boundary_condition2,
    minimal_model,
    comp_model,
    random_network,
    full_model,
    model_composition,
    linear_chain,
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
    substance_units,
    tiny_factory,
    model_definitions,
]


@pytest.mark.parametrize("module", testdata)
def test_create_model(module: Any) -> None:
    module.create(tmp=True)
