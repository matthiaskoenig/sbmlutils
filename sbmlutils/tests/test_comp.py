"""
Unit tests for the comp module.
"""

from __future__ import print_function, division
import unittest
from sbmlutils import sbmlio
from sbmlutils.tests import resources
from sbmlutils.comp import flattenExternalModelDefinitions


class CompTestCase(unittest.TestCase):
    """ Implement tests for comp model building. """

    def test_flattenExternalModelDefinition(self):
        sbml_path = resources.DFBA_EMD_SBML
        print(sbml_path)
        doc = sbmlio.read_sbml(sbml_path)

        # test that resource could be read
        self.assertIsNotNone(doc)
        # test that model in document
        self.assertIsNotNone(doc.getModel())
        print(doc)
        print(doc.getModel().getId())

        # check that model exists
        doc_no_emd = flattenExternalModelDefinitions(doc, validate=True)
        self.assertIsNotNone(doc_no_emd)

        # check that there are no external model definitions
        comp_doc_no_emd = doc_no_emd.getPlugin("comp")
        self.assertEqual(0, comp_doc_no_emd.getNumExternalModelDefinitions())

        # check that all model definitions are still there
        self.assertEqual(3, comp_doc_no_emd.getNumModelDefinitions())


if __name__ == '__main__':
    unittest.main()
