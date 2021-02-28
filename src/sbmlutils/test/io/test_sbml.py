from pathlib import Path

import libsbml

from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.test import BASIC_SBML, GZ_SBML


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

    doc = read_sbml(sbml_str)
    assert doc
    assert doc.getModel()


def test_read_sbml_from_gz() -> None:
    """Read SBML str."""
    doc1 = read_sbml(GZ_SBML)
    sbml_str = write_sbml(doc1)

    doc = read_sbml(sbml_str)
    assert doc
    assert doc.getModel()


def test_read_sbml_from_gzstr() -> None:
    """Read SBML str."""
    doc1 = read_sbml(str(GZ_SBML))
    sbml_str = write_sbml(doc1)

    doc = read_sbml(sbml_str)
    assert doc
    assert doc.getModel()


def test_read_sbml_validate() -> None:
    """Read and validate."""
    doc = read_sbml(BASIC_SBML, validate=True)
    assert doc
    assert doc.getModel()


def test_write_sbml(tmp_path: Path) -> None:
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    model.setId("test_id")

    sbml_path = tmp_path / "test.xml"
    write_sbml(doc=doc, filepath=sbml_path)
    assert sbml_path.exists()

    doc2 = read_sbml(source=sbml_path)
    assert doc2
    assert doc2.getModel()
