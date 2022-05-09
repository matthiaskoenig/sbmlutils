"""Test the galactose model."""
from sbmlutils.io.sbml import validate_sbml
from tests import GALACTOSE_SINGLECELL_SBML


def test_validate_sbml() -> None:
    """Test validation of galactose model."""
    vresults = validate_sbml(GALACTOSE_SINGLECELL_SBML, units_consistency=True)
    assert vresults.is_valid()
