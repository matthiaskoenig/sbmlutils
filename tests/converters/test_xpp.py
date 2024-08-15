"""Test XPP generation."""

from pathlib import Path

from sbmlutils.converters import xpp
from sbmlutils.io.sbml import validate_sbml
from sbmlutils.resources import TESTDATA_DIR
from sbmlutils.validation import ValidationOptions


model_ids = [
    # "112836_HH-ext",
    # "SkM_AP_KCa",
    "PLoSCompBiol_Fig1",
]


def _xpp_check(
    tmp_path: Path, ode_id: str, Nall: int = 0, Nerr: int = 0, Nwarn: int = 0
) -> None:
    sbml_file = tmp_path / f"{ode_id}.xml"
    xpp_file = TESTDATA_DIR / "xpp" / f"{ode_id}.ode"
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
    vresults = validate_sbml(
        sbml_file, validation_options=ValidationOptions(units_consistency=False)
    )
    assert vresults.all_count == Nall
    assert vresults.error_count == Nerr
    assert vresults.warning_count == Nwarn


def test_PLoSCompBiol_Fig1(tmp_path: Path) -> None:
    """Test model creation."""
    _xpp_check(tmp_path=tmp_path, ode_id="PLoSCompBiol_Fig1")


def test_SkM_AP_KCa(tmp_path: Path) -> None:
    """Test model creation."""
    _xpp_check(tmp_path=tmp_path, ode_id="SkM_AP_KCa")
