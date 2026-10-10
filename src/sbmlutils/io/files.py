"""File access for SBML which does not go through the file functions of libsbml.

libsbml opens a file with the narrow (ANSI) file API on Windows, so it can
neither read nor write a path with a non-ASCII character, e.g. a directory
named `ü`: `readSBMLFromFile` reports "File unreadable" and `writeSBMLToFile`
answers `False`. `sbmlutils.io.sbml` reads and writes such a path with these
functions, and libsbml only parses and serializes the SBML; every other path
is read and written by libsbml itself, whose reader handles what python does
not, e.g. a document in a declared encoding other than UTF-8.

libsbml compresses by the suffix of the path, in lower case only, and so do
these functions: a `.gz` file is gzip, a `.bz2` file bzip2 and a `.zip` file a
zip archive with a single entry, named as libsbml names it, see
`_zip_entry_name`. What libsbml still opens itself is the file of an external
model definition of the `comp` package, which it resolves when the definition
is used.
"""

import bz2
import gzip
import zipfile
import zlib
from pathlib import Path
from typing import Protocol


def is_file(source: Path | str) -> bool:
    """Check if a source is the path of an existing file.

    A string which is not meant as a path, e.g. SBML or antimony content, can
    be longer than a file name may be or contain a character a path cannot
    hold. Before python 3.14 `Path.is_file()` raises `OSError` (`File name too
    long`) or `ValueError` (`embedded null byte`) for such a string instead of
    answering `False`, so any such error means "not a file".

    Args:
        source: path or string to check

    Returns:
        whether the source names an existing file
    """
    try:
        return Path(source).is_file()
    except (OSError, ValueError):
        return False


def is_dir(source: Path | str) -> bool:
    """Check if a source is the path of an existing directory.

    Like `is_file`, any `OSError` or `ValueError` of the check means "not a
    directory".

    Args:
        source: path or string to check

    Returns:
        whether the source names an existing directory
    """
    try:
        return Path(source).is_dir()
    except (OSError, ValueError):
        return False


def libsbml_can_open(path: Path) -> bool:
    """Check if libsbml can open a path on every platform.

    libsbml passes the path to the narrow (ANSI) file API on Windows, which
    opens an ASCII path only for certain.

    Args:
        path: path of a file

    Returns:
        whether the path is ASCII
    """
    return str(path).isascii()


def _zip_entry_name(path: Path) -> str:
    """Get the name of the SBML entry in a zip archive, as libsbml names it.

    The name is the file name without `.zip`, with `.xml` added unless it
    ends in `.xml` or `.sbml`: `model.xml.zip` holds `model.xml`, `model.zip`
    holds `model.xml`.
    """
    name = path.name.removesuffix(".zip")
    return name if name.endswith((".xml", ".sbml")) else f"{name}.xml"


class InputSizeLimitError(ValueError):
    """The decompressed input exceeds the caller's byte limit."""


class _ByteReader(Protocol):
    """The read operation shared by plain and compressed binary streams."""

    def read(self, size: int = -1, /) -> bytes:
        """Read up to size bytes, or all remaining bytes for a negative size."""
        ...


def _read_limited(stream: _ByteReader, max_bytes: int | None) -> bytes:
    """Read at most one byte beyond a caller's decompressed input limit."""
    if max_bytes is not None and max_bytes < 0:
        raise ValueError("max_bytes must be nonnegative")
    content = stream.read() if max_bytes is None else stream.read(max_bytes + 1)
    if max_bytes is not None and len(content) > max_bytes:
        raise InputSizeLimitError(f"SBML input exceeds max_bytes={max_bytes}")
    return content


def read_text(path: Path, *, max_bytes: int | None = None) -> str:
    """Read the SBML of a file, decompressing it by its suffix.

    Args:
        path: path of the file, `.gz`, `.bz2` and `.zip` are decompressed
        max_bytes: optional limit on decompressed bytes, before UTF-8 decoding

    Returns:
        the content of the file, without a UTF-8 byte order mark

    Raises:
        OSError: if the file cannot be read or decompressed
        UnicodeDecodeError: if the content is not UTF-8, the encoding SBML
            requires
        ValueError: if the decompressed content exceeds `max_bytes`
    """
    content: bytes
    try:
        if path.suffix == ".gz":
            with gzip.open(path, "rb") as stream:
                content = _read_limited(stream, max_bytes)
        elif path.suffix == ".bz2":
            with bz2.open(path, "rb") as stream:
                content = _read_limited(stream, max_bytes)
        elif path.suffix == ".zip":
            content = _read_zip_entry(path, max_bytes=max_bytes)
        else:
            with path.open("rb") as stream:
                content = _read_limited(stream, max_bytes)
    except (EOFError, zlib.error, zipfile.BadZipFile) as err:
        # a truncated or corrupt stream, which is no `OSError` of its own
        raise OSError(f"'{path}' could not be decompressed: {err}") from err

    return content.decode("utf-8-sig")


def _read_zip_entry(path: Path, *, max_bytes: int | None = None) -> bytes:
    """Read the first entry of a zip archive, the one libsbml reads.

    Raises:
        OSError: if the file is no zip archive or has no entry
    """
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as err:
        raise OSError(f"not a zip archive: '{path}': {err}") from err
    with archive:
        names = archive.namelist()
        if not names:
            raise OSError(f"zip archive has no entry: '{path}'")
        with archive.open(names[0]) as stream:
            return _read_limited(stream, max_bytes)


def write_text(path: Path, text: str) -> None:
    """Write SBML to a file, compressing it by its suffix.

    The text is written as UTF-8 without translating line endings, so the file
    is the same on every platform and as libsbml writes it.

    Args:
        path: path of the file, `.gz`, `.bz2` and `.zip` are compressed
        text: SBML to write

    Raises:
        OSError: if the file cannot be written
    """
    content: bytes = text.encode("utf-8")
    if path.suffix == ".gz":
        path.write_bytes(gzip.compress(content))
    elif path.suffix == ".bz2":
        path.write_bytes(bz2.compress(content))
    elif path.suffix == ".zip":
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(_zip_entry_name(path), content)
    else:
        path.write_bytes(content)
