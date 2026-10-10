"""Test the SBML to antimony conversion."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import antimony
import libsbml
import pytest

from sbmlutils.io.antimony import sbml_to_antimony
from sbmlutils.parser import antimony_to_sbml
from sbmlutils.resources import REPRESSILATOR_SBML


def test_antimony_conversions_release_loaded_models() -> None:
    """Successful and failed conversions leave no retained native models."""
    for k in range(5):
        xml = antimony_to_sbml(f"model model_{k}()\n S=1;\nend")
        assert antimony.getNumFiles() == 0
        assert "model" in sbml_to_antimony(xml)
        assert antimony.getNumFiles() == 0
    with pytest.raises(ValueError, match="Antimony error"):
        antimony_to_sbml("model m\n S -> -> ;;\nend")
    assert antimony.getNumFiles() == 0


def test_antimony_conversions_are_isolated_between_threads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Concurrent conversions return the requested model in both directions."""
    original = antimony.loadAntimonyString

    def interleaved_load(source: str) -> int:
        status = original(source)
        # Yield between loading and serialization, where an unprotected load
        # in another thread would replace this conversion's active model.
        time.sleep(0.005)
        return status

    monkeypatch.setattr(antimony, "loadAntimonyString", interleaved_load)

    def convert(k: int) -> str:
        name = f"model_{k}"
        xml = antimony_to_sbml(f"model {name}()\n S=1;\nend")
        assert f"model *{name}()" in sbml_to_antimony(xml)
        doc = libsbml.readSBMLFromString(xml)
        return doc.getModel().getId()

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(convert, range(20))) == [f"model_{k}" for k in range(20)]
    assert antimony.getNumFiles() == 0


def test_sbml_to_antimony_from_file() -> None:
    """Convert an SBML file to antimony."""
    ant_str = sbml_to_antimony(REPRESSILATOR_SBML)
    assert "model" in ant_str
    assert "BIOMD0000000012" in ant_str
    # the antimony round trips to SBML
    sbml_str = antimony_to_sbml(ant_str)
    assert "<sbml" in sbml_str


def test_sbml_to_antimony_from_string() -> None:
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


def test_antimony_to_sbml_missing_file_name() -> None:
    """A string which looks like a file name and names no file is a missing file."""
    with pytest.raises(FileNotFoundError, match=r"model\.ant"):
        antimony_to_sbml("model.ant")


def test_antimony_to_sbml_long_content_the_file_system_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Content the file system rejects as a path is content, it does not crash.

    Before python 3.14 `Path.is_file()` raises `OSError: [Errno 36] File name
    too long` for a long string instead of answering `False`, emulated here.
    """

    def raise_name_too_long(self: Path) -> bool:
        raise OSError(36, "File name too long", str(self))

    monkeypatch.setattr(Path, "is_file", raise_name_too_long)
    content = "J0: S1 -> S2; k1*S1; S1 = 10; S2 = 0; k1 = 0.1\n" + "// x\n" * 1000
    assert "J0" in antimony_to_sbml(content)
