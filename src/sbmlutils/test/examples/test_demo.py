"""Test the demo model."""

from sbmlutils.io.sbml import validate_sbml
from sbmlutils.test import DEMO_SBML


def test_check_sbml() -> None:
    vresults = validate_sbml(DEMO_SBML, units_consistency=True)
    assert vresults.is_perfect()
