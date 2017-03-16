"""
Unit tests for the comp module.
"""

from __future__ import print_function, absolute_import

from sbmlutils.comp import flattenExternalModelDefinitions
from sbmlutils import sbmlio
from sbmlutils import validation
from sbmlutils.tests import data


def test_flattenExternalModelDefinition():
    sbml_path = data.DFBA_EMD_SBML
    print(sbml_path)
    doc = sbmlio.read_sbml(sbml_path)

    # test that resource could be read
    assert doc is not None
    # test that model in document
    assert doc.getModel() is not None
    print(doc)
    print(doc.getModel().getId())

    # check that model exists
    doc_no_emd = flattenExternalModelDefinitions(doc, validate=True)
    assert doc_no_emd is not None

    # check that there are no external model definitions
    comp_doc_no_emd = doc_no_emd.getPlugin("comp")
    assert 0 == comp_doc_no_emd.getNumExternalModelDefinitions()

    # check that all model definitions are still there
    assert 3 == comp_doc_no_emd.getNumModelDefinitions()

    # check model consistency
    Nall, Nerr, Nwarn = validation.check_doc(doc_no_emd)
    assert Nall == 0

