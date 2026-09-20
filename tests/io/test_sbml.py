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
