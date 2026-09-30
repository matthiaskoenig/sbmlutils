"""Testing cobra and fbc functionality."""

from pathlib import Path

import libsbml
import pytest

from sbmlutils.fbc.cobra import (
    check_mass_balance,
    cobra,
    cobra_reaction_info,
    read_cobra_model,
)
from sbmlutils.fbc.fbc import add_default_flux_bounds
from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.resources import DEMO_SBML, FBC_DIAUXIC_GROWTH_SBML


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_load_cobra_model() -> None:
    """Test loading of cobra model."""
    model = read_cobra_model(FBC_DIAUXIC_GROWTH_SBML)
    assert model


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_reaction_info() -> None:
    """Test reaction info."""
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
    """Test mass balance."""
    doc = read_sbml(DEMO_SBML)

    # add defaults
    add_default_flux_bounds(doc)

    filepath = tmp_path / "tests.xml"
    write_sbml(doc, filepath=filepath)
    model = read_cobra_model(filepath)

    # mass/charge balance
    for r in model.reactions:
        mb = r.check_mass_balance()
        # all metabolites are balanced
        assert len(mb) == 0


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_check_mass_balance() -> None:
    """Test that every reaction of the demo model is balanced."""
    assert check_mass_balance(sbml_path=DEMO_SBML) == {}


@pytest.mark.skipif(cobra is None, reason="requires cobrapy")
def test_check_mass_balance_finds_unbalanced_reactions(tmp_path: Path) -> None:
    """Test that the reactions of a species with another formula are unbalanced."""
    doc: libsbml.SBMLDocument = read_sbml(DEMO_SBML)
    model: libsbml.Model = doc.getModel()
    species: libsbml.Species = model.getSpecies("c__B")
    species_fbc: libsbml.FbcSpeciesPlugin = species.getPlugin("fbc")
    species_fbc.setChemicalFormula("C6H12O5")
    sbml_path = tmp_path / "unbalanced.xml"
    write_sbml(doc, filepath=sbml_path)

    unbalanced = check_mass_balance(sbml_path=sbml_path)

    # c__B lacks an oxygen: it is a product of v1 and v4, which lose one, and
    # the reactant of the transport bB, which gains one
    assert unbalanced == {"bB": {"O": 1.0}, "v1": {"O": -1.0}, "v4": {"O": -1.0}}
