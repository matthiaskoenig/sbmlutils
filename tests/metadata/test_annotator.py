"""Test annotation functions and annotating of SBML models."""

import logging
import re
from collections.abc import Iterable
from pathlib import Path

import libsbml
import pytest

from examples import annotation as annotation_example
from sbmlutils.factory import *
from sbmlutils.io.sbml import read_sbml
from sbmlutils.metadata import BQB, SBO, annotator
from sbmlutils.metadata.annotator import ExternalAnnotation, ModelAnnotator
from sbmlutils.resources import (
    DEMO_ANNOTATIONS,
    DEMO_SBML_NO_ANNOTATIONS,
    GALACTOSE_ANNOTATIONS,
    GALACTOSE_SINGLECELL_SBML_NO_ANNOTATIONS,
)


def test_create_annotation(tmp_path: Path) -> None:
    """Create assignment model."""
    model_path: Path = tmp_path / "model.xml"
    create_model(annotation_example.model, filepath=model_path)
    assert model_path.exists()


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
    assert ma.pattern == "id1"
    assert ma.sbml_type == "reaction"
    assert ma.annotation_type == "rdf"
    assert ma.qualifier == BQB.IS
    assert ma.resource == "sbo/SBO:0000290"
    assert ma.name == "physical compartment"


def test_model_annotator() -> None:
    """Test model annotator."""
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
        model=Model(**model_dict), filepath=tmp_path / "annotation1.xml"
    )
    # check annotations
    doc: libsbml.SBMLDocument = read_sbml(source=results.sbml_path)
    model: libsbml.Model = doc.getModel()
    compartment: libsbml.Compartment = model.getCompartment(0)
    assert compartment

    # the sboTerm attribute is written as an attribute, not duplicated as a
    # CVTerm, see https://github.com/matthiaskoenig/sbmlutils/issues/469
    assert compartment.getSBOTermID() == "SBO:0000290"

    cvterms: libsbml.CVTermList = compartment.getCVTerms()
    assert compartment.getNumCVTerms() == 1

    cv: libsbml.CVTerm = cvterms[0]
    assert cv.getNumResources() == 1


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


def _written_resources(sbml_path: Path, sid: str) -> list[str]:
    """Collect the annotation resources written for an element.

    Args:
        sbml_path: path of the SBML file
        sid: id of the species the annotation is on

    Returns:
        every resource of every CVTerm of the species
    """
    doc: libsbml.SBMLDocument = read_sbml(source=sbml_path)
    sbase: libsbml.Species = doc.getModel().getSpecies(sid)
    return [
        sbase.getCVTerm(k).getResourceURI(i)
        for k in range(sbase.getNumCVTerms())
        for i in range(sbase.getCVTerm(k).getNumResources())
    ]


def _annotated_species(resource: str, sbml_path: Path) -> None:
    """Write a model with a single species annotated with the given resource.

    Args:
        resource: the annotation resource, as a model definition gives it
        sbml_path: path the SBML is written to
    """
    create_model(
        model=Model(
            sid="annotation",
            compartments=[Compartment("c", 1.0)],
            species=[
                Species(
                    "s1",
                    compartment="c",
                    initialAmount=1.0,
                    annotations=[(BQB.IS, resource)],
                )
            ],
        ),
        filepath=sbml_path,
        validation_options=ValidationOptions(units_consistency=False),
    )


#: resources pymetadata cannot canonicalize without losing their collection,
#: measured with pymetadata 0.6.2: the first three normalize to the bare term
#: `1406`, `UO:0000040` and `CMO:0000012`, which name no collection at all,
#: and the fourth to `https://identifiers.org/000000035`, a URL the `slm`
#: collection has been dropped from
LOSSY_RESOURCES: list[str] = [
    "http://identifiers.org/sabiork/1406",
    "http://identifiers.org/unit/UO:0000040",
    "https://identifiers.org/CMO:0000012",
    "http://identifiers.org/slm/000000035",
]


@pytest.mark.parametrize("resource", LOSSY_RESOURCES)
def test_annotation_resource_which_cannot_be_normalized_is_written_as_given(
    resource: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a resource is written as given rather than losing its collection.

    An annotation is written as `RDFAnnotation.resource_normalized`, which is
    the identifiers.org compact URL for a collection of the registry and the
    bare term for one which is not in it. The bare term is not a resolvable
    resource and no longer names the collection, so the annotation says
    something else than the model definition did.
    """
    sbml_path = tmp_path / "annotation.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        _annotated_species(resource, sbml_path)

    assert _written_resources(sbml_path, "s1") == [resource]
    warnings = [
        record.getMessage()
        for record in caplog.records
        if record.levelname == "WARNING" and resource in record.getMessage()
    ]
    assert len(warnings) == 1, caplog.text


#: resources which pymetadata canonicalizes to the compact identifiers.org
#: URL of their collection and term, one per form: a classic URL, a MIRIAM
#: URN, the `http` spelling of the compact URL and a bare compact identifier
NORMALIZED_RESOURCES: list[tuple[str, str]] = [
    ("chebi/CHEBI:12965", "https://identifiers.org/CHEBI:12965"),
    ("urn:miriam:chebi:CHEBI%3A33699", "https://identifiers.org/CHEBI:33699"),
    ("http://identifiers.org/BTO:0000131", "https://identifiers.org/BTO:0000131"),
    ("UO:0000021", "https://identifiers.org/UO:0000021"),
]


@pytest.mark.parametrize("resource, expected", NORMALIZED_RESOURCES)
def test_annotation_resource_of_a_known_collection_is_normalized(
    resource: str, expected: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a resource which keeps its collection is still normalized.

    Every one of these normalizes to the compact identifiers.org URL of the
    collection and term it was given with, so nothing is lost and no warning
    is due.
    """
    sbml_path = tmp_path / "annotation.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        _annotated_species(resource, sbml_path)

    assert _written_resources(sbml_path, "s1") == [expected]
    assert not [
        record.getMessage()
        for record in caplog.records
        if record.levelname == "WARNING"
        and record.name == "sbmlutils.metadata.annotator"
    ], caplog.text


def test_annotation_resource_of_an_arbitrary_url_is_unchanged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a URL outside identifiers.org is written as given, silently.

    pymetadata keeps such a URL as it is, so there is nothing to warn about.
    """
    resource = "http://example.com/my/resource"
    sbml_path = tmp_path / "annotation.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        _annotated_species(resource, sbml_path)

    assert _written_resources(sbml_path, "s1") == [resource]
    assert not [
        record
        for record in caplog.records
        if record.levelname == "WARNING"
        and record.name == "sbmlutils.metadata.annotator"
    ], caplog.text
