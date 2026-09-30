"""Example model creation."""

from pathlib import Path
from typing import Any

import pytest

from examples.registry import examples_create, examples_models
from sbmlutils.factory import create_model
from sbmlutils.io import validate_sbml
from sbmlutils.validation import ValidationOptions, ValidationResult


@pytest.mark.parametrize("module", examples_create)
def test_create_example_create(tmp_path: Path, module: Any) -> None:
    """Test that an example writes models and that every one of them is valid."""
    module.create(output_dir=tmp_path)

    sbml_paths = sorted(tmp_path.glob("**/*.xml"))
    assert sbml_paths, f"'{module.__name__}' wrote no model"
    for sbml_path in sbml_paths:
        vresults: ValidationResult = validate_sbml(
            source=sbml_path,
            validation_options=ValidationOptions(units_consistency=False),
        )
        assert vresults.error_count == 0, f"'{sbml_path.name}' is invalid"


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


def test_create_omex_example(tmp_path: Path) -> None:
    """Test that the COMBINE archive example writes valid models and the archive.

    The hierarchical model of the example couples copies of the minimal model,
    so its external model definitions must reference the file of the minimal
    model and not the file of the hierarchical model itself, which libsbml
    cannot instantiate and `flatten_sbml` refuses.
    """
    from examples.combine_archive.omex_models import create_omex

    create_omex(tmp_dir=tmp_path)

    sbml_paths = sorted(tmp_path.glob("*.xml"))
    assert [p.name for p in sbml_paths] == [
        "omex_comp.xml",
        "omex_comp_flat.xml",
        "omex_minimal.xml",
    ]
    for sbml_path in sbml_paths:
        vresults: ValidationResult = validate_sbml(
            source=sbml_path,
            validation_options=ValidationOptions(units_consistency=False),
        )
        assert vresults.error_count == 0, f"'{sbml_path.name}' is invalid"
    assert (tmp_path / "omex_comp.omex").exists()
