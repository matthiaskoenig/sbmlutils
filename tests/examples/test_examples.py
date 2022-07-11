"""Example model creation."""
from pathlib import Path
from typing import Any

import pytest

from sbmlutils.factory import create_model
from sbmlutils.examples import examples_models, examples_create
from sbmlutils.io import validate_sbml
from sbmlutils.validation import ValidationResult, ValidationOptions


@pytest.mark.parametrize("module", examples_create)
def test_create_model(tmp_path: Path, module: Any) -> None:
    """Test create model."""
    module.create(tmp=True)


@pytest.mark.parametrize("module", examples_models)
def test_create_model(tmp_path: Path, module: Any) -> None:
    """Test create model."""
    model_path: Path = tmp_path / f"model.xml"
    results = create_model(
        model=module.model,
        filepath=model_path,
    )
    assert model_path.exists()

    # check that valid model
    vresults: ValidationResult = validate_sbml(
        source=results.sbml_path,
        validation_options=ValidationOptions(units_consistency=False)
    )
    assert vresults.error_count == 0
