"""
Test XPP generation
"""
from sbmlutils.converters import xpp
from sbmlutils.tests import DATA_DIR
from sbmlutils.io.sbml import validate_sbml


def xpp_check(tmp_path, ode_id, Nall=0, Nerr=0, Nwarn=0):
    sbml_file = tmp_path / f"{ode_id}.xml"
    xpp_file = DATA_DIR / 'xpp' / f"{ode_id}.ode"
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
    Nall_res, Nerr_res, Nwarn_res = validate_sbml(sbml_file, units_consistency=False)
    assert Nall_res == Nall
    assert Nerr_res == Nerr
    assert Nwarn_res == Nwarn


def test_PLoSCompBiol_Fig1(tmp_path):
    xpp_check(tmp_path=tmp_path, ode_id="PLoSCompBiol_Fig1")


def test_SkM_AP_KCa(tmp_path):
    xpp_check(tmp_path=tmp_path, ode_id="SkM_AP_KCa")
