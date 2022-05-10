"""Test SBML validation."""
from pathlib import Path

import pytest

from sbmlutils.io.sbml import validate_sbml
from sbmlutils.resources import (
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    VDP_SBML,
)


@pytest.mark.parametrize(
    "sbml_path, ucheck, n_all",
    [
        (DEMO_SBML, True, 0),
        (GALACTOSE_SINGLECELL_SBML, True, 0),
        (BASIC_SBML, True, 0),
        (VDP_SBML, False, 0),
    ],
)
def test_sbml_validation(sbml_path: Path, ucheck: bool, n_all: int) -> None:
    """Test SBML validation."""
    v_results = validate_sbml(sbml_path, units_consistency=ucheck)
    assert v_results
    assert n_all == v_results.all_count
