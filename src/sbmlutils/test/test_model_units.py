"""Test ModelUnits and setting model units."""
from pathlib import Path

import pytest
from libsbml import UNIT_KIND_LITER, UNIT_KIND_LITRE, UNIT_KIND_METER, UNIT_KIND_METRE

from sbmlutils.creator import create_model
from sbmlutils.factory import ModelUnits, UnitType
from sbmlutils.io import validate_sbml


@pytest.mark.parametrize("unit", [UNIT_KIND_LITER, UNIT_KIND_LITRE])
def test_model_units_litre(unit: UnitType, tmp_path: Path) -> None:
    """Test that volume can be set with litre and liter."""
    md = {
        "mid": "example_model",
        "model_units": ModelUnits(
            volume=unit,
        ),
    }
    results = create_model(
        modules=md,
        output_dir=tmp_path,
        tmp=False,
        sbml_level=3,
        sbml_version=1,
        validate=False,
    )
    val_results = validate_sbml(source=results.sbml_path)
    assert val_results.all_count == 0


@pytest.mark.parametrize("unit", [UNIT_KIND_METER, UNIT_KIND_METRE])
def test_model_units_metre(unit: UnitType, tmp_path: Path) -> None:
    """Test that length can be set with metre and meter."""
    md = {
        "mid": "example_model",
        "model_units": ModelUnits(
            length=unit,
        ),
    }
    results = create_model(
        modules=md,
        output_dir=tmp_path,
        tmp=False,
        sbml_level=3,
        sbml_version=1,
        validate=False,
    )
    val_results = validate_sbml(source=results.sbml_path)
    assert val_results.all_count == 0
