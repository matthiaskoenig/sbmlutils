from __future__ import print_function, division
import unittest
import libsbml
from sbmlutils.examples import testfiles

from sbmlutils.comp import flattenExternalModelDefinitions


class CompTestCase(unittest.TestCase):
    """ Implement tests for comp model building. """

    def test_flattenExternalModelDefinition(self):
        sbml_path = testfiles.DFBA_EMD_SBML
        doc = libsbml.readSBMLFromFile(sbml_path)
        doc_no_emd = flattenExternalModelDefinitions(doc)

        # check that model exists
        self.assertIsNotNone(doc_no_emd)

        # check that there are no external model definitions
        comp_doc_no_emd = doc_no_emd.getPlugin("comp")
        self.assertEqual(0, doc.getNumExternalModelDefinitions())

        # check that all model definitions are still there
        self.assertEqual(3, doc.getNumModelDefinitions())


if __name__ == '__main__':
    unittest.main()
