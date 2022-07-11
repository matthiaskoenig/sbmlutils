"""Example model creation."""
from pathlib import Path
from typing import Any

import pytest

from sbmlutils.examples import (
    algebraic_rule,
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
    parameter,
    random_network,
    reaction,
    species,
    simple_reaction_with_units,
    unit_definitions,
    units_namespace,
)
from sbmlutils.examples.dallaman import factory as dallaman_factory
from sbmlutils.examples.demo import factory as demo_factory
from sbmlutils.examples.tiny_model import factory as tiny_factory


testdata = [
    algebraic_rule,
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
    parameter,
    reaction,
    simple_reaction_with_units,
    unit_definitions,
    units_namespace,
    dallaman_factory,
    demo_factory,
    tiny_factory,
]


@pytest.mark.parametrize("module", testdata)
def test_create_model(tmp_path: Path, module: Any) -> None:
    """Test create model."""
    module.create(tmp=True)
