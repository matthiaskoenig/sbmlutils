"""Test the utility functions."""

import libsbml

from sbmlutils.io import read_sbml
from sbmlutils.resources import FBC_ECOLI_CORE_SBML
from sbmlutils.utils import all_elements


def test_all_elements_yields_the_elements_of_get_list_of_all_elements() -> None:
    """Test that `all_elements` yields what the iteration of the libsbml list yields, in its order."""
    doc: libsbml.SBMLDocument = read_sbml(FBC_ECOLI_CORE_SBML)
    expected = [
        (type(e), e.getElementName(), e.getMetaId()) for e in doc.getListOfAllElements()
    ]

    elements = list(all_elements(doc))

    assert [(type(e), e.getElementName(), e.getMetaId()) for e in elements] == expected
    assert len(elements) > 1000


def test_all_elements_leaves_the_document_unchanged() -> None:
    """Test that consuming the list removes no element from the document and every element stays usable."""
    doc: libsbml.SBMLDocument = read_sbml(FBC_ECOLI_CORE_SBML)
    before: str = libsbml.writeSBMLToString(doc)

    elements = list(all_elements(doc.getModel()))

    assert libsbml.writeSBMLToString(doc) == before
    assert all(element.getSBMLDocument() is not None for element in elements)
