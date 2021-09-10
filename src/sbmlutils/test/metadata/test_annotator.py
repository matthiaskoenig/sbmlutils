"""
Test annotation functions and annotating of SBML models.
"""
import re
from pathlib import Path
from typing import Iterable

import libsbml

from sbmlutils.examples import annotation as annotation_example
from sbmlutils.factory import *
from sbmlutils.io.sbml import read_sbml
from sbmlutils.metadata import SBO, annotator
from sbmlutils.metadata.annotator import ExternalAnnotation, ModelAnnotator
from sbmlutils.metadata.miriam import *
from sbmlutils.test import (
    DEMO_ANNOTATIONS,
    DEMO_SBML_NO_ANNOTATIONS,
    GALACTOSE_ANNOTATIONS,
    GALACTOSE_SINGLECELL_SBML_NO_ANNOTATIONS,
)


def test_create_annotation() -> None:
    """Create assignment model."""
    annotation_example.create(tmp=True)


def test_external_annotation() -> None:
    """Check annotation data structure."""
    d = {
        "pattern": "id1",
        "sbml_type": "reaction",
        "annotation_type": "rdf",
        "qualifier": "BQB_IS",
        "resource": "sbo/SBO:0000290",
        "name": "physical compartment",
    }

    ma = ExternalAnnotation(d)
    assert "id1" == ma.pattern
    assert "reaction" == ma.sbml_type
    assert "rdf" == ma.annotation_type
    assert BQB.IS == ma.qualifier
    assert "sbo/SBO:0000290" == ma.resource
    assert "physical compartment" == ma.name


def test_model_annotator() -> None:
    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    annotations: Iterable[ExternalAnnotation] = []
    annotator = ModelAnnotator(model, annotations)
    assert model == annotator.model
    assert annotations == annotator.annotations
    annotator.annotate_model()


def test_model_annotation(tmp_path: Path) -> None:
    """Create minimal model and check that annotation is written correctly."""
    model_dict: ModelDict = {
        "sid": "example_annotation",
        "compartments": [
            Compartment(
                sid="C",
                value=1.0,
                sboTerm=SBO.PHYSICAL_COMPARTMENT,
                annotations=[
                    (BQB.IS, "chebi/CHEBI:28061"),  # alpha-D-galactose
                ],
            )
        ],
    }

    results = create_model(
        Model(**model_dict), output_dir=tmp_path, filename="annotation1.xml"
    )
    # check annotations
    doc: libsbml.SBMLDocument = read_sbml(source=results.sbml_path)
    model: libsbml.Model = doc.getModel()
    compartment: libsbml.Compartment = model.getCompartment(0)
    assert compartment

    cvterms: libsbml.CVTermList = compartment.getCVTerms()
    assert compartment.getNumCVTerms() == 1

    cv: libsbml.CVTerm = cvterms[0]
    assert cv.getNumResources() == 2


def test_demo_annotation(tmp_path: Path) -> None:
    """Annotate the demo network."""

    tmp_sbml_path = tmp_path / "sbml_annotated.xml"
    annotator.annotate_sbml(
        DEMO_SBML_NO_ANNOTATIONS, DEMO_ANNOTATIONS, filepath=tmp_sbml_path
    )

    # document
    doc: libsbml.SBMLDocument = read_sbml(source=tmp_sbml_path)
    # sbml_str = write_sbml(doc)
    # print(sbml_str)
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
    ce = model.getCompartment("e")
    assert ce.getSBOTerm() == 290
    assert ce.getSBOTermID() == "SBO:0000290"
    cvterms = ce.getCVTerms()
    # check: is one cv term with 3 resources in bag
    assert len(cvterms) == 1
    assert cvterms[0].getNumResources() == 3

    cm = model.getCompartment("m")
    assert cm.getSBOTerm() == 290
    assert cm.getSBOTermID() == "SBO:0000290"
    cvterms = cm.getCVTerms()
    assert len(cvterms) == 1
    assert cvterms[0].getNumResources() == 3

    cc = model.getCompartment("c")
    assert cc.getSBOTerm() == 290
    assert cc.getSBOTermID() == "SBO:0000290"
    cvterms = cm.getCVTerms()
    assert len(cvterms) == 1
    assert cvterms[0].getNumResources() == 3

    # parameters
    for p in model.parameters:
        cvterms = p.getCVTerms()
        if re.match(r"^Km_\w+$", p.id):
            assert p.getSBOTerm() == 27
            assert p.getSBOTermID() == "SBO:0000027"
            assert len(cvterms) == 1

        if re.match(r"^Keq_\w+$", p.id):
            assert p.getSBOTerm() == 281
            assert p.getSBOTermID() == "SBO:0000281"
            assert len(cvterms) == 1

        if re.match(r"^Vmax_\w+$", p.id):
            assert p.getSBOTerm() == 186
            assert p.getSBOTermID() == "SBO:0000186"
            assert len(cvterms) == 1

    # species
    for s in model.species:
        cvterms = s.getCVTerms()
        if re.match(r"^\w{1}__[ABC]$", s.id):
            assert s.getSBOTerm() == 247
            assert s.getSBOTermID() == "SBO:0000247"
            assert len(cvterms) == 1

    # reactions
    for r in model.reactions:
        cvterms = r.getCVTerms()
        if re.match(r"^b\w{1}$", r.id):
            assert r.getSBOTerm() == 185
            assert r.getSBOTermID() == "SBO:0000185"
            assert len(cvterms) == 1

        if re.match(r"^v\w{1}$", r.id):
            assert r.getSBOTerm() == 176
            assert r.getSBOTermID() == "SBO:0000176"
            assert len(cvterms) == 1

    # fbc:geneProduct
    modelFBCPlugin = model.getPlugin("fbc")
    for geneProduct in modelFBCPlugin.getListOfGeneProducts():
        if geneProduct.getId() == "PSHA_RS08100":
            cvterms = geneProduct.getCVTerms()
            assert len(cvterms) == 1


def test_galactose_annotation(tmp_path: Path) -> None:
    """Annotate the galactose network."""
    tmp_sbml_path = tmp_path / "sbml_annotated.xml"
    annotator.annotate_sbml(
        GALACTOSE_SINGLECELL_SBML_NO_ANNOTATIONS,
        annotations_path=GALACTOSE_ANNOTATIONS,
        filepath=tmp_sbml_path,
    )
