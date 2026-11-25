"""Test the printed result of an annotation validation."""

from pathlib import Path

import pytest

from sbmlutils.metadata.validator import _print_invalid_annotations


def test_valid_annotations_are_one_line(capsys: pytest.CaptureFixture[str]) -> None:
    """A model without invalid annotations is reported in one printed line."""
    _print_invalid_annotations(Path("model.xml"), [])
    out = capsys.readouterr().out
    assert out.strip() == "annotations valid model.xml"


def test_invalid_annotations_are_a_table(capsys: pytest.CaptureFixture[str]) -> None:
    """Invalid annotations are printed as a table, brackets as they are."""
    _print_invalid_annotations(
        "<sbml/>",
        [
            {
                "id": "glc",
                "object": "Species",
                "name": "glucose [ext]",
                "resource": "https://identifiers.org/chebi/x",
            }
        ],
    )
    out = capsys.readouterr().out
    assert "1 invalid annotation(s) in SBML string" in out
    assert "glucose [ext]" in out
    assert "https://identifiers.org/chebi/x" in out
