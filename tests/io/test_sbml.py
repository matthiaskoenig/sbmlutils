"""Test SBML reading and writing."""

import re
import zipfile
from pathlib import Path

import libsbml
import pytest

from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.resources import BASIC_SBML, GZ_SBML


def test_read_sbml_from_path() -> None:
    """Read from path."""
    doc = read_sbml(BASIC_SBML)
    assert doc
    assert doc.getModel()


def test_read_sbml_from_strpath() -> None:
    """Read from strpath (os.path)."""
    doc = read_sbml(str(BASIC_SBML))
    assert doc
    assert doc.getModel()


def test_read_sbml_from_str() -> None:
    """Read SBML str."""
    doc1 = read_sbml(str(BASIC_SBML))
    sbml_str = write_sbml(doc1)
    assert sbml_str

    if sbml_str:
        doc = read_sbml(sbml_str)
        assert doc
        assert doc.getModel()


def test_read_sbml_from_gz() -> None:
    """Read SBML str."""
    doc1 = read_sbml(GZ_SBML)
    sbml_str = write_sbml(doc1)
    assert sbml_str

    if sbml_str:
        doc = read_sbml(sbml_str)
        assert doc
        assert doc.getModel()


def test_read_sbml_from_gzstr() -> None:
    """Read SBML str."""
    doc1 = read_sbml(str(GZ_SBML))
    sbml_str = write_sbml(doc1)

    assert sbml_str
    if sbml_str:
        doc = read_sbml(sbml_str)
        assert doc
        assert doc.getModel()


def test_read_sbml_validate() -> None:
    """Read and validate."""
    doc = read_sbml(BASIC_SBML, validate=True)
    assert doc
    assert doc.getModel()


def test_write_sbml(tmp_path: Path) -> None:
    """Test writing SBML."""
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    model.setId("test_id")

    sbml_path = tmp_path / "tests.xml"
    write_sbml(doc=doc, filepath=sbml_path)
    assert sbml_path.exists()

    doc2 = read_sbml(source=sbml_path)
    assert doc2
    assert doc2.getModel()


def test_write_sbml_creates_the_parent_directory(tmp_path: Path) -> None:
    """Test that a write into a directory which does not exist yet creates it.

    `libsbml.SBMLWriter.writeSBMLToFile` answers `False` for a path whose
    parent does not exist and writes nothing, which the writer used to
    discard: no file was written and nothing was reported.
    """
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    model.setId("test_id")

    sbml_path = tmp_path / "does" / "not" / "exist" / "model.xml"
    write_sbml(doc=doc, filepath=sbml_path)

    assert sbml_path.exists()
    assert read_sbml(source=sbml_path).getModel().getId() == "test_id"


def test_write_sbml_raises_when_the_file_cannot_be_written(tmp_path: Path) -> None:
    """Test that a write which cannot be repaired raises, naming the path.

    A directory which does not exist is the one failure a writer can repair;
    a parent which is a file is not. Such a write used to be discarded, and
    `create_model` went on to report `valid: TRUE` for a file it never wrote:
    the validation re-reads the path, and an unreadable file gives an empty
    document, which is valid.
    """
    blocking_file = tmp_path / "a_file"
    blocking_file.write_text("not a directory", encoding="utf-8")
    sbml_path = blocking_file / "model.xml"

    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    doc.createModel().setId("test_id")

    with pytest.raises(OSError, match=re.escape(str(sbml_path))):
        write_sbml(doc=doc, filepath=sbml_path)

    assert not sbml_path.exists()


_SBML_WITHOUT_MODEL = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
    'level="3" version="2"/>'
)

_SBML_COMP_LIBRARY = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
    'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
    'level="3" version="2" comp:required="true">'
    "<comp:listOfModelDefinitions>"
    '<comp:modelDefinition id="md"/>'
    "</comp:listOfModelDefinitions>"
    "</sbml>"
)

_SBML_TRUNCATED = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
    'level="3" version="2"><model id="m"><listOfParameters>'
)


@pytest.mark.parametrize("promote", [False, True])
def test_read_sbml_raises_for_a_file_which_does_not_exist(
    tmp_path: Path, promote: bool
) -> None:
    """An unreadable file raises with the libsbml error instead of only logging it.

    The error used to be logged and a document without a model returned, on
    which the promotion of local parameters crashed with an AttributeError.
    """
    with pytest.raises(ValueError, match=r"does_not_exist\.xml.*\n.*E2 "):
        read_sbml(tmp_path / "does_not_exist.xml", promote=promote)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("<sbml garbage", id="unclosed"),
        pytest.param(_SBML_TRUNCATED, id="truncated"),
    ],
)
def test_read_sbml_raises_for_malformed_xml(source: str) -> None:
    """A string which is not well-formed XML raises and names the libsbml errors."""
    with pytest.raises(ValueError, match=r"could not be read:\n.*E\d+"):
        read_sbml(source)


@pytest.mark.parametrize("promote", [False, True])
@pytest.mark.parametrize(
    "source",
    [
        pytest.param(_SBML_WITHOUT_MODEL, id="without-model"),
        pytest.param(_SBML_COMP_LIBRARY, id="comp-library"),
    ],
)
def test_read_sbml_returns_a_valid_document_without_a_model(
    source: str, promote: bool
) -> None:
    """A document without a model is valid SBML from L3V2 on and is read as it is."""
    doc = read_sbml(source, promote=promote)
    assert doc.getModel() is None
    assert doc.getNumErrors() == 0


def test_read_sbml_reads_a_document_with_errors_in_its_content() -> None:
    """Errors in the SBML content are for the validation, the document is read."""
    doc = read_sbml(
        _SBML_WITHOUT_MODEL.replace("/>", '><model id="m" foo="1"/></sbml>')
    )
    assert doc.getModel().getId() == "m"
    assert doc.getError(0).getErrorId() == libsbml.AllowedAttributesOnModel


def test_read_sbml_error_does_not_repeat_long_source() -> None:
    """A non-SBML string treated as a path is shortened in the message."""
    from sbmlutils.io.sbml import validate_sbml

    source = "x" * 5000
    with pytest.raises(FileNotFoundError) as excinfo:
        validate_sbml(source)
    assert len(str(excinfo.value)) < 300
    assert "..." in str(excinfo.value)


def _raise_name_too_long(self: Path, *args: object, **kwargs: object) -> bool:
    """Answer a file system check as python < 3.14 does for a very long name."""
    raise OSError(36, "File name too long", str(self))


def test_validate_sbml_raises_for_a_long_string_the_file_system_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A string the file system rejects as a path is no file, it does not crash.

    Before python 3.14 `Path.exists()` and `Path.is_file()` raise
    `OSError: [Errno 36] File name too long` for a string longer than a file
    name may be, instead of answering `False`; the check is emulated here so
    that the behaviour of every python version is tested on every version.
    """
    from sbmlutils.io.sbml import validate_sbml

    monkeypatch.setattr(Path, "exists", _raise_name_too_long)
    monkeypatch.setattr(Path, "is_file", _raise_name_too_long)
    with pytest.raises(FileNotFoundError, match="SBML file does not exist"):
        validate_sbml("x" * 5000)


#: directories with a character a path handling may get wrong: a space, which a
#: file URI percent-encodes, and a non-ASCII character, which libsbml cannot
#: open on Windows, where it passes the path to the narrow (ANSI) file API
PATH_DIRS = ["sp ace", "ü"]


def _model_doc(model_id: str = "m") -> libsbml.SBMLDocument:
    """Create a document with a model which has a non-ASCII name."""
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId(model_id)
    model.setName("über")
    return doc


@pytest.mark.parametrize("path_dir", PATH_DIRS)
def test_write_and_read_sbml_in_a_directory_with_a_special_character(
    tmp_path: Path, path_dir: str
) -> None:
    """A path with a space or a non-ASCII character is written, read and validated."""
    from sbmlutils.io.sbml import validate_sbml

    sbml_path = tmp_path / path_dir / "model.xml"
    write_sbml(_model_doc(), filepath=sbml_path, validate=True)

    doc = read_sbml(sbml_path)
    assert doc.getModel().getName() == "über"
    assert doc.getLocationURI() == f"file:{sbml_path.resolve()}"
    assert validate_sbml(sbml_path).is_valid()


def test_write_sbml_does_not_use_the_file_writer_of_libsbml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file is written by python, libsbml only serializes the document.

    `libsbml.SBMLWriter.writeSBMLToFile` refuses a path with a non-ASCII
    character on Windows; its refusal is emulated here so that the write is
    known not to depend on it on every platform.
    """
    monkeypatch.setattr(libsbml.SBMLWriter, "writeSBMLToFile", lambda *args: False)
    sbml_path = tmp_path / "model.xml"

    write_sbml(_model_doc(), filepath=sbml_path)

    assert libsbml.readSBMLFromString(sbml_path.read_text("utf-8")).getModel()


def test_read_sbml_does_not_use_the_file_reader_of_libsbml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file is read by python, libsbml only parses its content.

    `libsbml.readSBMLFromFile` cannot open a path with a non-ASCII character
    on Windows, it answers "File unreadable"; its failure is emulated here.
    """
    sbml_path = tmp_path / "model.xml"
    sbml_path.write_text(libsbml.writeSBMLToString(_model_doc("m1")), encoding="utf-8")
    monkeypatch.setattr(
        libsbml, "readSBMLFromFile", lambda *args: libsbml.readSBMLFromString("")
    )

    assert read_sbml(sbml_path).getModel().getId() == "m1"


@pytest.mark.parametrize("filename", ["m.xml.gz", "m.xml.bz2", "m.xml.zip", "m.zip"])
def test_compressed_files_are_compatible_with_libsbml(
    tmp_path: Path, filename: str
) -> None:
    """A compressed file is written and read as libsbml writes and reads it.

    libsbml compresses by the suffix of the path, `.gz`, `.bz2` or `.zip`, and
    names the entry of a zip archive after the path without `.zip`, with `.xml`
    added unless it ends in `.xml` or `.sbml`.
    """
    ours = tmp_path / "ours" / filename
    theirs = tmp_path / "theirs" / filename
    theirs.parent.mkdir()
    write_sbml(_model_doc("ours"), filepath=ours)
    assert libsbml.writeSBMLToFile(_model_doc("theirs"), str(theirs))

    assert libsbml.readSBMLFromFile(str(ours)).getModel().getId() == "ours"
    assert read_sbml(theirs).getModel().getId() == "theirs"
    if filename.endswith(".zip"):
        with zipfile.ZipFile(ours) as z_ours, zipfile.ZipFile(theirs) as z_theirs:
            assert z_ours.namelist() == z_theirs.namelist()


def test_read_sbml_raises_for_a_file_which_is_not_utf8(tmp_path: Path) -> None:
    """SBML is UTF-8, a file in another encoding cannot be read."""
    sbml_path = tmp_path / "latin1.xml"
    sbml_path.write_bytes(
        libsbml.writeSBMLToString(_model_doc())
        .encode("utf-8")
        .replace("ü".encode(), "ü".encode("latin-1"))
    )
    with pytest.raises(
        ValueError, match=r"latin1\.xml.*could not be read:\n.*E1017 .*UTF-8"
    ):
        read_sbml(sbml_path)
