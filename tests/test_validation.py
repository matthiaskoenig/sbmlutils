"""Test SBML validation."""
from pathlib import Path

import pytest

from sbmlutils.io.sbml import ValidationOptions, ValidationResult, validate_sbml
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
    v_results = validate_sbml(
        source=sbml_path, validation_options=ValidationOptions(units_consistency=ucheck)
    )
    assert v_results
    assert n_all == v_results.all_count


@pytest.mark.parametrize(
    "options",
    [
        ValidationOptions(),
        ValidationOptions(internal_consistency=False),
        ValidationOptions(log_errors=False),
        ValidationOptions(general_consistency=False),
        ValidationOptions(identifier_consistency=False),
        ValidationOptions(mathml_consistency=False),
        ValidationOptions(units_consistency=False),
        ValidationOptions(sbo_consistency=False),
        ValidationOptions(overdetermined_model=False),
        ValidationOptions(modeling_practice=False),
    ],
)
def test_sbml_validation_options(options: ValidationOptions) -> None:
    """Test options for SBML validation."""
    v_results: ValidationResult = validate_sbml(
        source=DEMO_SBML, validation_options=options
    )
    assert v_results
