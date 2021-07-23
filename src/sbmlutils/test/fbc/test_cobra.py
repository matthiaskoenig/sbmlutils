"""
Unit tests for fbc.
"""
from pathlib import Path

import pytest

from sbmlutils.fbc.cobra import (
    check_mass_balance,
    cobra,
    cobra_reaction_info,
    read_cobra_model,
)
from sbmlutils.fbc.fbc import add_default_flux_bounds
from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.test import DEMO_SBML, FBC_DIAUXIC_GROWTH_SBML


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_load_cobra_model() -> None:
    model = read_cobra_model(FBC_DIAUXIC_GROWTH_SBML)
    assert model


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_reaction_info() -> None:
    cobra_model = read_cobra_model(FBC_DIAUXIC_GROWTH_SBML)
    df = cobra_reaction_info(cobra_model)
    assert df is not None

    assert df.at["v1", "objective_coefficient"] == 1
    assert df.at["v2", "objective_coefficient"] == 1
    assert df.at["v3", "objective_coefficient"] == 1
    assert df.at["v4", "objective_coefficient"] == 1
    assert df.at["EX_Ac", "objective_coefficient"] == 0
    assert df.at["EX_Glcxt", "objective_coefficient"] == 0
    assert df.at["EX_O2", "objective_coefficient"] == 0
    assert df.at["EX_X", "objective_coefficient"] == 0


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_mass_balance(tmp_path: Path) -> None:
    doc = read_sbml(DEMO_SBML)

    # add defaults
    add_default_flux_bounds(doc)

    filepath = tmp_path / "test.xml"
    write_sbml(doc, filepath=filepath)
    model = read_cobra_model(filepath)

    # mass/charge balance
    for r in model.reactions:
        mb = r.check_mass_balance()
        # all metabolites are balanced
        assert len(mb) == 0


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_check_mass_balance() -> None:
    check_mass_balance(sbml_path=DEMO_SBML)
