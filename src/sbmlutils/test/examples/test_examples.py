"""Example model creation."""
from typing import Any

import pytest

from sbmlutils.examples import (
    amount_species,
    annotation,
    assignment,
    boundary_condition,
    compartment_species_reaction,
    complete_model,
    distrib_comp,
    distrib_distributions,
    distrib_uncertainties,
    fbc_example,
    fbc_mass_charge,
    linear_chain,
    minimal_model,
    minimal_model_comp,
    model_composition,
    model_definitions,
    multiple_substance_units,
    nan,
    notes,
    random_network,
    reaction,
    simple_reaction_with_units,
    unit_definitions,
    units_namespace,
)
from sbmlutils.examples.dallaman import factory as dallaman_factory
from sbmlutils.examples.demo import factory as demo_factory
from sbmlutils.examples.tiny_model import factory as tiny_factory


testdata = [
    amount_species,
    annotation,
    assignment,
    boundary_condition,
    compartment_species_reaction,
    complete_model,
    distrib_comp,
    distrib_distributions,
    distrib_uncertainties,
    fbc_example,
    fbc_mass_charge,
    linear_chain,
    minimal_model,
    minimal_model_comp,
    model_composition,
    model_definitions,
    multiple_substance_units,
    nan,
    notes,
    random_network,
    reaction,
    simple_reaction_with_units,
    unit_definitions,
    units_namespace,
    dallaman_factory,
    demo_factory,
    tiny_factory,
]


@pytest.mark.parametrize("module", testdata)
def test_create_model(module: Any) -> None:
    module.create(tmp=True)
