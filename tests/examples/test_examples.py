"""Example model creation."""

from pathlib import Path
from typing import Any

import pytest

from sbmlutils.examples import examples_create, examples_models
from sbmlutils.factory import create_model
from sbmlutils.io import validate_sbml
from sbmlutils.validation import ValidationOptions, ValidationResult


@pytest.mark.parametrize("module", examples_create)
def test_create_example_create(tmp_path: Path, module: Any) -> None:
    """Test create model."""
    module.create(output_dir=tmp_path)


@pytest.mark.parametrize("module", examples_models)
def test_create_example_models(tmp_path: Path, module: Any) -> None:
    """Test create model."""
    model_path: Path = tmp_path / "model.xml"
    results = create_model(
        model=module.model,
        filepath=model_path,
    )
    assert model_path.exists()

    # check that valid model
    vresults: ValidationResult = validate_sbml(
        source=results.sbml_path,
        validation_options=ValidationOptions(units_consistency=False),
    )
    assert vresults.error_count == 0
