"""File access for SBML which does not go through the file functions of libsbml.

libsbml opens a file with the narrow (ANSI) file API on Windows, so it can
neither read nor write a path with a character outside the code page, e.g. a
directory named `ü`: `readSBMLFromFile` reports "File unreadable" and
`writeSBMLToFile` answers `False`. The content of a file is therefore read and
written by python, and libsbml only parses and serializes it.

libsbml compresses by the suffix of the path, and so do these functions: a
`.gz` file is gzip, a `.bz2` file bzip2 and a `.zip` file a zip archive with a
single entry, named as libsbml names it, see `_zip_entry_name`. What libsbml
still opens itself is the file of an external model definition of the `comp`
package, which it resolves when the definition is used.
"""

import bz2
import gzip
import zipfile
from pathlib import Path


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


def _zip_entry_name(path: Path) -> str:
    """Get the name of the SBML entry in a zip archive, as libsbml names it.

    The name is the file name without `.zip`, with `.xml` added unless it
    ends in `.xml` or `.sbml`: `model.xml.zip` holds `model.xml`, `model.zip`
    holds `model.xml`.
    """
    name = path.name.removesuffix(".zip")
    return name if name.endswith((".xml", ".sbml")) else f"{name}.xml"


def read_text(path: Path) -> str:
    """Read the SBML of a file, decompressing it by its suffix.

    Args:
        path: path of the file, `.gz`, `.bz2` and `.zip` are decompressed

    Returns:
        the content of the file

    Raises:
        OSError: if the file cannot be read or decompressed
        ValueError: if the content is not UTF-8, the encoding SBML requires
    """
    content: bytes
    if path.suffix == ".gz":
        content = gzip.decompress(path.read_bytes())
    elif path.suffix == ".bz2":
        content = bz2.decompress(path.read_bytes())
    elif path.suffix == ".zip":
        try:
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                if not names:
                    raise OSError(f"zip archive has no entry: '{path}'")
                content = archive.read(names[0])
        except zipfile.BadZipFile as err:
            raise OSError(f"not a zip archive: '{path}': {err}") from err
    else:
        content = path.read_bytes()

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as err:
        raise ValueError(f"content is not UTF-8, which SBML requires: {err}") from err


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
