"""Test the creator module."""

from pathlib import Path
from typing import Any

import libsbml
import pytest

from sbmlutils.factory import *
from sbmlutils.io import read_sbml
from sbmlutils.validation import SBMLValidationError, ValidationOptions


def test_create_model_returns_final_validation(tmp_path: Path) -> None:
    """An invalid written model exposes its errors without a second validation."""
    model = Model(
        "invalid", species=[Species("S", compartment="missing", initialAmount=1)]
    )
    result = create_model(model, tmp_path / "invalid.xml")
    assert result.sbml_path.exists()
    assert result.validation is not None
    assert not result.validation.is_valid()
    skipped = create_model(model, tmp_path / "unchecked.xml", validate=False)
    assert skipped.validation is None


def test_create_model_can_raise_for_invalid_output(tmp_path: Path) -> None:
    """Strict creation validates even if the ordinary validation flag is off."""
    path = tmp_path / "invalid.xml"
    model = Model(
        "invalid", species=[Species("S", compartment="missing", initialAmount=1)]
    )
    with pytest.raises(SBMLValidationError, match="failed validation") as caught:
        create_model(model, path, validate=False, raise_on_error=True)
    assert not caught.value.result.is_valid()
    assert path.exists()


def test_create_model_validates_after_annotation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The reported validation describes the final annotated document."""
    from sbmlutils.metadata import annotator

    annotations = tmp_path / "annotations.csv"
    annotations.write_text(
        "pattern,sbml_type,annotation_type,qualifier,resource\n", encoding="utf-8"
    )

    def annotate(
        doc: libsbml.SBMLDocument, _annotations: list[annotator.ExternalAnnotation]
    ) -> libsbml.SBMLDocument:
        # Simulate a post-processing step that introduces an invalid reference.
        species = doc.getModel().createSpecies()
        species.setId("S")
        species.setCompartment("missing")
        species.setConstant(False)
        species.setBoundaryCondition(False)
        species.setHasOnlySubstanceUnits(False)
        return doc

    monkeypatch.setattr(annotator, "annotate_sbml_doc", annotate)
    result = create_model(
        Model("annotated"), tmp_path / "annotated.xml", annotations=annotations
    )
    assert result.validation is not None
    assert not result.validation.is_valid()


level_version_testdata = [
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (3, 1),
    (3, 2),
]


@pytest.mark.parametrize(("level", "version"), level_version_testdata)
def test_sbml_level_version(level: int, version: int, tmp_path: Path) -> None:
    """Test that the various levels and versions of SBML can be generated."""
    md: dict[str, Any] = {
        "sid": "level_version",
        "compartments": [Compartment(sid="C", value=1.0)],
        "species": [
            Species(
                sid="S1",
                initialConcentration=10.0,
                compartment="C",
                hasOnlySubstanceUnits=False,
                boundaryCondition=True,
            )
        ],
        "parameters": [Parameter(sid="k1", value=1.0)],
        "reactions": [
            Reaction(
                sid="R1",
                equation="S1 ->",
                formula=("k1 * S1 * sin(time)", Units.dimensionless),
            )
        ],
    }

    results = create_model(
        model=Model(**md),
        filepath=tmp_path / "model.xml",
        sbml_level=level,
        sbml_version=version,
        validation_options=ValidationOptions(units_consistency=False),
    )
    doc = read_sbml(source=results.sbml_path, validate=False)
    assert level == doc.getLevel()
    assert version == doc.getVersion()
