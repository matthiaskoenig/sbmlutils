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

    def raise_error(_self: Path) -> bool:
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
    with pytest.raises(UnicodeDecodeError):
        read_text(path)


def test_read_text_raises_for_a_truncated_gzip_file(tmp_path: Path) -> None:
    """A truncated `.gz` file raises an `OSError`, not an `EOFError`."""
    path = tmp_path / "m.xml.gz"
    write_text(path, "<sbml/>" * 100)
    path.write_bytes(path.read_bytes()[:-20])
    with pytest.raises(OSError, match="could not be decompressed"):
        read_text(path)


def test_read_text_raises_for_a_corrupt_zip_entry(tmp_path: Path) -> None:
    """A zip archive whose entry is corrupt raises an `OSError`."""
    path = tmp_path / "m.zip"
    write_text(path, "<sbml/>" * 100)
    content = bytearray(path.read_bytes())
    # the deflated data of the entry follows its 30 byte local header and name
    start = 30 + len("m.xml")
    content[start : start + 8] = b"\xff" * 8
    path.write_bytes(bytes(content))
    with pytest.raises(OSError, match="could not be decompressed"):
        read_text(path)


def test_read_text_reads_a_byte_order_mark(tmp_path: Path) -> None:
    """A UTF-8 byte order mark is not part of the text."""
    path = tmp_path / "m.xml"
    path.write_bytes(b"\xef\xbb\xbf<sbml/>")
    assert read_text(path) == "<sbml/>"


def test_write_text_compresses_by_lower_case_suffixes_only(tmp_path: Path) -> None:
    """As libsbml, an upper case `.GZ` is no gzip file."""
    path = tmp_path / "m.xml.GZ"
    write_text(path, "<sbml/>")
    assert path.read_bytes() == b"<sbml/>"
