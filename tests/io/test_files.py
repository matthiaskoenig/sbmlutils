"""Test the file access for SBML which does not go through libsbml."""

from pathlib import Path

import pytest

from sbmlutils.io.files import is_file, read_text, write_text


def test_is_file(tmp_path: Path) -> None:
    """An existing file is a file, a directory and a missing path are not."""
    path = tmp_path / "model.xml"
    path.write_text("<sbml/>", encoding="utf-8")

    assert is_file(path)
    assert is_file(str(path))
    assert not is_file(tmp_path)
    assert not is_file(tmp_path / "missing.xml")


@pytest.mark.parametrize(
    "error",
    [OSError(36, "File name too long"), ValueError("embedded null byte")],
    ids=["OSError", "ValueError"],
)
def test_is_file_is_false_when_the_file_system_check_raises(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    """A string the file system rejects is no file, as python >= 3.14 answers.

    Before python 3.14 `Path.is_file()` raises for a name which is too long or
    holds a null byte instead of answering `False`.
    """

    def raise_error(self: Path) -> bool:
        raise error

    monkeypatch.setattr(Path, "is_file", raise_error)
    assert not is_file("x" * 5000)


@pytest.mark.parametrize(
    "filename", ["m.xml", "m.xml.gz", "m.xml.bz2", "m.xml.zip", "m.sbml.zip", "m.zip"]
)
def test_write_and_read_text(tmp_path: Path, filename: str) -> None:
    """Text is written and read back unchanged, compressed by the suffix."""
    path = tmp_path / filename
    text = '<?xml version="1.0" encoding="UTF-8"?>\n<sbml name="über">\r\n</sbml>\n'

    write_text(path, text)

    assert read_text(path) == text


def test_read_text_raises_for_a_zip_file_which_is_no_archive(tmp_path: Path) -> None:
    """A `.zip` file which is not a zip archive cannot be read."""
    path = tmp_path / "m.zip"
    path.write_bytes(b"<sbml/>")
    with pytest.raises(OSError, match="not a zip archive"):
        read_text(path)


def test_read_text_raises_for_content_which_is_not_utf8(tmp_path: Path) -> None:
    """SBML is UTF-8, other content cannot be read."""
    path = tmp_path / "m.xml"
    path.write_bytes("<sbml name='über'/>".encode("latin-1"))
    with pytest.raises(ValueError, match="not UTF-8"):
        read_text(path)
