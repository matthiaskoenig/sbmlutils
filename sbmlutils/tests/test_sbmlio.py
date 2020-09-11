import libsbml

from sbmlutils.sbmlio import read_sbml, write_sbml
from sbmlutils.tests import BASIC_SBML
import pytest


def test_read_sbml_from_path():
    """Read from path."""
    doc = read_sbml(BASIC_SBML)
    assert doc
    assert doc.getModel()


def test_read_sbml_from_strpath():
    """Read from strpath (os.path)."""
    doc = read_sbml(str(BASIC_SBML))
    assert doc
    assert doc.getModel()


def test_read_sbml_from_str():
    """Read SBML str."""
    doc1 = read_sbml(str(BASIC_SBML))
    sbml_str = libsbml.writeSBMLToString(doc1)

    doc = read_sbml(sbml_str)
    assert doc
    assert doc.getModel()


def test_read_sbml_validate():
    """Read and validate."""
    doc = read_sbml(BASIC_SBML, validate=True)
    assert doc
    assert doc.getModel()


def test_write_sbml(tmp_path):
    doc = libsbml.SBMLDocument()  # type: libsbml.SBMLDocument
    model = doc.createModel()  # type: libsbml.Model
    model.setId("test_id")

    sbml_path = tmp_path / "test.xml"
    write_sbml(doc=doc, filepath=sbml_path)
    assert sbml_path.exists()

    doc2 = read_sbml(source=sbml_path)
    assert doc2
    assert doc2.getModel()
