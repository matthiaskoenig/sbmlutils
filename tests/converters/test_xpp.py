"""Test XPP generation."""

from pathlib import Path

import libsbml
import pytest

from sbmlutils.converters import xpp
from sbmlutils.io.sbml import validate_sbml
from sbmlutils.resources import TESTDATA_DIR
from sbmlutils.validation import ValidationOptions

#: the packaged ode files, every one of them converts to valid SBML
model_ids = [
    "112836_HH-ext",
    "SkM_AP_KCa",
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


@pytest.mark.parametrize("ode_id", model_ids)
def test_xpp2sbml(tmp_path: Path, ode_id: str) -> None:
    """Every packaged ode file converts to a valid SBML model."""
    _xpp_check(tmp_path=tmp_path, ode_id=ode_id)


def test_xpp2sbml_notes_and_functions(tmp_path: Path) -> None:
    """The ode file is escaped once into the notes, min and max are named right."""
    xpp_file = tmp_path / "escape.ode"
    xpp_file.write_text(
        "# x decays while a < b & b > 0\npar a=1, b=2\nx'=-a*x\ninit x=1\ndone\n",
        encoding="utf-8",
    )
    sbml_file = tmp_path / "escape.xml"
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)

    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_file))
    model: libsbml.Model = doc.getModel()
    notes = model.getNotesString()
    assert "a &lt; b &amp; b &gt; 0" in notes
    assert "&amp;lt;" not in notes

    assert model.getFunctionDefinition("max").getName() == "maximum"
    assert model.getFunctionDefinition("min").getName() == "minimum"


def test_escape_string() -> None:
    """Every markup character is escaped exactly once."""
    assert xpp.escape_string("a < b & c > d") == "a &lt; b &amp; c &gt; d"
