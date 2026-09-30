"""Test the SBML to antimony conversion."""

import logging
from pathlib import Path

import pytest

from sbmlutils.io.antimony import sbml_to_antimony
from sbmlutils.parser import antimony_to_sbml
from sbmlutils.resources import REPRESSILATOR_SBML


def test_sbml_to_antimony_from_file() -> None:
    """Convert an SBML file to antimony."""
    ant_str = sbml_to_antimony(REPRESSILATOR_SBML)
    assert "model" in ant_str
    assert "BIOMD0000000012" in ant_str
    # the antimony round trips to SBML
    sbml_str = antimony_to_sbml(ant_str)
    assert "<sbml" in sbml_str


def test_sbml_to_antimony_from_string(tmp_path: Path) -> None:
    """Convert an SBML string to antimony."""
    sbml_str = antimony_to_sbml(
        "model example\n J0: S1 -> S2; k1*S1\n S1 = 10; S2 = 0; k1 = 0.1\nend"
    )
    ant_str = sbml_to_antimony(sbml_str)
    assert "model" in ant_str
    assert "J0:" in ant_str
    assert "S1 -> S2" in ant_str


def test_antimony_to_sbml_valid_logs_no_error(caplog: pytest.LogCaptureFixture) -> None:
    """Valid antimony is converted without an error being logged."""
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        sbml_str = antimony_to_sbml("model m\n S1 = 1\nend")
    assert "<sbml" in sbml_str
    assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []


def test_antimony_to_sbml_invalid_raises() -> None:
    """Invalid antimony raises a ValueError with the antimony error."""
    with pytest.raises(ValueError, match="syntax error"):
        antimony_to_sbml("model m\n S1 -> -> ;;; =\nend")


def test_antimony_to_sbml_str_path_with_model_in_name(tmp_path: Path) -> None:
    """A string path of an existing file is read as file, even with 'model' in it."""
    path = tmp_path / "my_model.ant"
    path.write_text("model m\n S1 = 1\nend", encoding="utf-8")
    assert "<sbml" in antimony_to_sbml(str(path))
    assert "<sbml" in antimony_to_sbml(path)


def test_antimony_to_sbml_string_without_model_keyword() -> None:
    """Antimony content without the 'model' keyword is content, not a path."""
    sbml_str = antimony_to_sbml("J0: S1 -> S2; k1*S1; S1 = 10; S2 = 0; k1 = 0.1")
    assert "J0" in sbml_str


def test_antimony_to_sbml_missing_path_raises(tmp_path: Path) -> None:
    """A Path which does not exist raises a FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        antimony_to_sbml(tmp_path / "missing.ant")
