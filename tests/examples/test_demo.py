"""Test the demo model."""

from sbmlutils.io.sbml import validate_sbml
from sbmlutils.resources import DEMO_SBML


def test_check_sbml() -> None:
    """Test the demo SBML."""
    vresults = validate_sbml(DEMO_SBML)
    assert vresults.is_perfect()
