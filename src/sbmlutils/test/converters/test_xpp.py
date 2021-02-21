"""Test XPP generation."""
import pytest

from sbmlutils.converters import xpp, xpp_examples
from sbmlutils.io.sbml import validate_sbml
from sbmlutils.test import DATA_DIR


model_ids = [
    # "112836_HH-ext",
    # "SkM_AP_KCa",
    "PLoSCompBiol_Fig1",
]


@pytest.mark.parametrize("model_id", model_ids)
def test_xpp_examples(model_id):
    xpp_examples.example(model_id)


def xpp_check(tmp_path, ode_id, Nall=0, Nerr=0, Nwarn=0):
    sbml_file = tmp_path / f"{ode_id}.xml"
    xpp_file = DATA_DIR / "xpp" / f"{ode_id}.ode"
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
    vresults = validate_sbml(sbml_file, units_consistency=False)
    assert vresults.all_count == Nall
    assert vresults.error_count == Nerr
    assert vresults.warning_count == Nwarn


def test_PLoSCompBiol_Fig1(tmp_path):
    xpp_check(tmp_path=tmp_path, ode_id="PLoSCompBiol_Fig1")


def test_SkM_AP_KCa(tmp_path):
    xpp_check(tmp_path=tmp_path, ode_id="SkM_AP_KCa")
