"""Test SBML reading and writing."""

import re
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
