"""Test the SBML to antimony conversion."""

from pathlib import Path

from sbmlutils.io.antimony import sbml_to_antimony
from sbmlutils.parser import antimony_to_sbml
from sbmlutils.resources import REPRESSILATOR_SBML


def test_sbml_to_antimony_from_file() -> None:
    """Convert an SBML file to antimony."""
    ant_str = sbml_to_antimony(REPRESSILATOR_SBML)
    assert "model" in ant_str
    assert "BIOMD0000000012" in ant_str
    # the antimony round trips to SBML
    sbml_str = antimony_to_sbml(ant_str)
    assert "<sbml" in sbml_str


def test_sbml_to_antimony_from_string(tmp_path: Path) -> None:
    """Convert an SBML string to antimony."""
    sbml_str = antimony_to_sbml(
        "model example\n J0: S1 -> S2; k1*S1\n S1 = 10; S2 = 0; k1 = 0.1\nend"
    )
    ant_str = sbml_to_antimony(sbml_str)
    assert "model" in ant_str
    assert "J0:" in ant_str
    assert "S1 -> S2" in ant_str
