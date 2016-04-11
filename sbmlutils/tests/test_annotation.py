"""
Test annotation functions and annotating of SBML models.
"""

from __future__ import print_function, division

import os
import tempfile
import unittest
import libsbml

from multiscale.examples import testdata
from multiscale.sbmlutils.annotation import *


class TestAnnotation(unittest.TestCase):

    def test_model_annotation(self):
        """
        Check the annotation data structure.
        """
        d = {'pattern': 'test_pattern',
             'sbml_type': 'reaction',
             'annotation_type': 'RDF',
             'value': 'test_value',
             'qualifier': 'test_qualifier',
             'collection': 'test_collection',
             'name': 'test_name'}
        ma = ModelAnnotation(d)
        self.assertEqual('test_pattern', ma.pattern)
        self.assertEqual('reaction', ma.sbml_type)
        self.assertEqual('RDF', ma.annotation_type)
        self.assertEqual('test_value', ma.value)
        self.assertEqual('test_qualifier', ma.qualifier)
        self.assertEqual('test_collection', ma.collection)
        self.assertEqual('test_name', ma.name)

    def test_model_annotator(self):
        doc = libsbml.SBMLDocument(3, 1)
        model = doc.createModel()
        annotations = []
        annotator = ModelAnnotator(model, annotations)
        self.assertEqual(model, annotator.model)
        self.assertEqual(annotations, annotator.annotations)
        annotator.annotate_model()

    def test_set_model_history(self):
        creators = {'Test' :
                        {'FamilyName': 'Koenig',
                         'GivenName': 'Matthias',
                         'Email': 'konigmatt@googlemail.com',
                         'Organization': 'Test organisation'}}
        sbmlns = libsbml.SBMLNamespaces(3, 1)
        doc = libsbml.SBMLDocument(sbmlns)
        model = doc.createModel()
        set_model_history(model, creators)
        h = model.getModelHistory()
        self.assertIsNotNone(h)
        self.assertEqual(1, h.getNumCreators())
        c = h.getCreator(0)
        self.assertEqual('Koenig', c.getFamilyName())
        self.assertEqual('Matthias', c.getGivenName())
        self.assertEqual('konigmatt@googlemail.com', c.getEmail())
        self.assertEqual('Test organisation', c.getOrganization())

    def test_demo_annotation(self):
        """ Annotate the demo network. """
        f_tmp = tempfile.NamedTemporaryFile()
        annotate_sbml_file(testdata.demo_sbml_no_annotations, testdata.demo_annotations, f_sbml_annotated=f_tmp.name)
        f_tmp.flush()

        import re

        # document
        doc = libsbml.readSBMLFromFile(f_tmp.name)
        self.assertEqual(doc.getSBOTerm(), 293)
        self.assertEqual(doc.getSBOTermID(), "SBO:0000293")
        cvterms = doc.getCVTerms()
        # check: is one cv term with 3 resources in bag
        self.assertEqual(len(cvterms), 1)
        self.assertEqual(cvterms[0].getNumResources(), 1)

        # model
        model = doc.getModel()
        cvterms = model.getCVTerms()
        print(cvterms)
        self.assertEqual(len(cvterms), 1)

        # compartments
        ce = model.getCompartment('e')
        self.assertEqual(ce.getSBOTerm(), 290)
        self.assertEqual(ce.getSBOTermID(), "SBO:0000290")
        cvterms = ce.getCVTerms()
        # check: is one cv term with 3 resources in bag
        self.assertEqual(len(cvterms), 1)
        self.assertEqual(cvterms[0].getNumResources(), 3)

        cm = model.getCompartment('m')
        self.assertEqual(cm.getSBOTerm(), 290)
        self.assertEqual(cm.getSBOTermID(), "SBO:0000290")
        cvterms = cm.getCVTerms()
        self.assertEqual(len(cvterms), 1)
        self.assertEqual(cvterms[0].getNumResources(), 3)

        cc = model.getCompartment('c')
        self.assertEqual(cc.getSBOTerm(), 290)
        self.assertEqual(cc.getSBOTermID(), "SBO:0000290")
        cvterms = cm.getCVTerms()
        self.assertEqual(len(cvterms), 1)
        self.assertEqual(cvterms[0].getNumResources(), 3)

        # parameters
        for p in model.parameters:
            cvterms = p.getCVTerms()
            if re.match("^Km_\w+$", p.id):
                self.assertEqual(p.getSBOTerm(), 27)
                self.assertEqual(p.getSBOTermID(), "SBO:0000027")
                self.assertEqual(len(cvterms), 1)

            if re.match("^Keq_\w+$", p.id):
                self.assertEqual(p.getSBOTerm(), 281)
                self.assertEqual(p.getSBOTermID(), "SBO:0000281")
                self.assertEqual(len(cvterms), 1)

            if re.match("^Vmax_\w+$", p.id):
                self.assertEqual(p.getSBOTerm(), 186)
                self.assertEqual(p.getSBOTermID(), "SBO:0000186")
                self.assertEqual(len(cvterms), 1)

        # species
        for s in model.species:
            cvterms = s.getCVTerms()
            if re.match("^\w{1}__[ABC]$", s.id):
                self.assertEqual(s.getSBOTerm(), 247)
                self.assertEqual(s.getSBOTermID(), "SBO:0000247")
                self.assertEqual(len(cvterms), 1)

        # reactions
        for r in model.reactions:
            cvterms = r.getCVTerms()
            if re.match("^b\w{1}$", r.id):
                self.assertEqual(r.getSBOTerm(), 185)
                self.assertEqual(r.getSBOTermID(), "SBO:0000185")
                self.assertEqual(len(cvterms), 1)

            if re.match("^v\w{1}$", r.id):
                self.assertEqual(r.getSBOTerm(), 176)
                self.assertEqual(r.getSBOTermID(), "SBO:0000176")
                self.assertEqual(len(cvterms), 1)

    def test_galactose_annotation(self):
        """ Annotate the galactose network. """
        f_tmp = tempfile.NamedTemporaryFile()
        annotate_sbml_file(testdata.galactose_singlecell_sbml_no_annotations, testdata.galactose_annotations,
                           f_sbml_annotated=f_tmp.name)
        f_tmp.flush()

if __name__ == "__main__":
    unittest.main()
