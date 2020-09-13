"""
Unit tests for fbc.
"""

from sbmlutils.fbc.fbc import add_default_flux_bounds
from sbmlutils.fbc.cobra import load_cobra_model, cobra_reaction_info, check_mass_balance
from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.tests import FBC_SBML, DEMO_SBML


def test_load_cobra_model():
    model = load_cobra_model(FBC_SBML)
    assert model


def test_reaction_info():
    cobra_model = load_cobra_model(FBC_SBML)
    df = cobra_reaction_info(cobra_model)
    assert df is not None

    assert df.at['v1', 'objective_coefficient'] == 1
    assert df.at['v2', 'objective_coefficient'] == 1
    assert df.at['v3', 'objective_coefficient'] == 1
    assert df.at['v4', 'objective_coefficient'] == 1
    assert df.at['EX_Ac', 'objective_coefficient'] == 0
    assert df.at['EX_Glcxt', 'objective_coefficient'] == 0
    assert df.at['EX_O2', 'objective_coefficient'] == 0
    assert df.at['EX_X', 'objective_coefficient'] == 0


def test_mass_balance(tmp_path):
    doc = read_sbml(DEMO_SBML)

    # add defaults
    add_default_flux_bounds(doc)

    filepath = tmp_path / "test.xml"
    write_sbml(doc, filepath=filepath)
    model = load_cobra_model(filepath)

    # mass/charge balance
    for r in model.reactions:
        mb = r.check_mass_balance()
        # all metabolites are balanced
        assert len(mb) == 0
