"""Test the galactose model."""

from sbmlutils.io.sbml import validate_sbml
from sbmlutils.resources import GALACTOSE_SINGLECELL_SBML


def test_validate_sbml() -> None:
    """Test validation of galactose model."""
    vresults = validate_sbml(GALACTOSE_SINGLECELL_SBML)
    assert vresults.is_valid()
