from sbmlutils.io.sbml import validate_sbml
from sbmlutils.test import GALACTOSE_SINGLECELL_SBML


def test_validate_sbml() -> None:
    vresults = validate_sbml(GALACTOSE_SINGLECELL_SBML, units_consistency=True)
    assert vresults.is_valid()
