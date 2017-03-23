"""
Test annotation functions and annotating of SBML models.
"""
from __future__ import print_function, division
import re
import tempfile
import libsbml

from sbmlutils.factory import Creator
from sbmlutils import annotation
from sbmlutils.annotation import ModelAnnotator, ModelAnnotation
from sbmlutils.tests import data


def test_model_annotation():
    """ Check annotation data structure. """
    d = {'pattern': 'test_pattern',
         'sbml_type': 'reaction',
         'annotation_type': 'RDF',
         'value': 'test_value',
         'qualifier': 'test_qualifier',
         'collection': 'test_collection',
         'name': 'test_name'}

    ma = ModelAnnotation(d)
    assert 'test_pattern' == ma.pattern
    assert 'reaction' == ma.sbml_type
    assert 'RDF' == ma.annotation_type
    assert 'test_value' == ma.value
    assert 'test_qualifier' == ma.qualifier
    assert 'test_collection' == ma.collection
    assert 'test_name' == ma.name


def test_model_annotator():
    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    annotations = []
    annotator = ModelAnnotator(model, annotations)
    assert model == annotator.model
    assert annotations == annotator.annotations
    annotator.annotate_model()


def test_set_model_history():
    creators = [Creator(familyName='Koenig', givenName="Matthias",
                        email="konigmatt@googlemail.com", organization="Test organisation")]
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    doc = libsbml.SBMLDocument(sbmlns)
    model = doc.createModel()
    annotation.set_model_history(model, creators)
    h = model.getModelHistory()
    assert h is not None
    assert h.getNumCreators() == 1
    c = h.getCreator(0)
    assert 'Koenig' == c.getFamilyName()
    assert 'Matthias' == c.getGivenName()
    assert 'konigmatt@googlemail.com' == c.getEmail()
    assert 'Test organisation' == c.getOrganization()


def test_demo_annotation():
    """ Annotate the demo network. """

    f_tmp = tempfile.NamedTemporaryFile()
    annotation.annotate_sbml_file(data.DEMO_SBML_NO_ANNOTATIONS, data.DEMO_ANNOTATIONS, f_sbml_annotated=f_tmp.name)
    f_tmp.flush()

    # document
    doc = libsbml.readSBMLFromFile(f_tmp.name)
    assert doc.getSBOTerm() == 293
    assert doc.getSBOTermID() == "SBO:0000293"
    cvterms = doc.getCVTerms()
    # check: is one cv term with 3 resources in bag
    assert len(cvterms) == 1
    assert cvterms[0].getNumResources() == 1

    # model
    model = doc.getModel()
    cvterms = model.getCVTerms()
    assert len(cvterms) == 0

    # compartments
    ce = model.getCompartment('e')
    assert ce.getSBOTerm() == 290
    assert ce.getSBOTermID() == "SBO:0000290"
    cvterms = ce.getCVTerms()
    # check: is one cv term with 3 resources in bag
    assert len(cvterms) == 1
    assert cvterms[0].getNumResources() == 3

    cm = model.getCompartment('m')
    assert cm.getSBOTerm() == 290
    assert cm.getSBOTermID() == "SBO:0000290"
    cvterms = cm.getCVTerms()
    assert len(cvterms) == 1
    assert cvterms[0].getNumResources() == 3

    cc = model.getCompartment('c')
    assert cc.getSBOTerm() == 290
    assert cc.getSBOTermID() == "SBO:0000290"
    cvterms = cm.getCVTerms()
    assert len(cvterms) == 1
    assert cvterms[0].getNumResources() == 3

    # parameters
    for p in model.parameters:
        cvterms = p.getCVTerms()
        if re.match("^Km_\w+$", p.id):
            assert p.getSBOTerm() == 27
            assert p.getSBOTermID() == "SBO:0000027"
            assert len(cvterms) == 1

        if re.match("^Keq_\w+$", p.id):
            assert p.getSBOTerm() == 281
            assert p.getSBOTermID() == "SBO:0000281"
            assert len(cvterms) == 1

        if re.match("^Vmax_\w+$", p.id):
            assert p.getSBOTerm() == 186
            assert p.getSBOTermID() == "SBO:0000186"
            assert len(cvterms) == 1

    # species
    for s in model.species:
        cvterms = s.getCVTerms()
        if re.match("^\w{1}__[ABC]$", s.id):
            assert s.getSBOTerm() == 247
            assert s.getSBOTermID() == "SBO:0000247"
            assert len(cvterms) == 1

    # reactions
    for r in model.reactions:
        cvterms = r.getCVTerms()
        if re.match("^b\w{1}$", r.id):
            assert r.getSBOTerm() == 185
            assert r.getSBOTermID() == "SBO:0000185"
            assert len(cvterms) == 1

        if re.match("^v\w{1}$", r.id):
            assert r.getSBOTerm() == 176
            assert r.getSBOTermID() == "SBO:0000176"
            assert len(cvterms) == 1


def test_galactose_annotation():
    """ Annotate the galactose network. """
    f_tmp = tempfile.NamedTemporaryFile()
    annotation.annotate_sbml_file(data.GALACTOSE_SINGLECELL_SBML_NO_ANNOTATIONS, data.GALACTOSE_ANNOTATIONS,
                       f_sbml_annotated=f_tmp.name)
    f_tmp.flush()
