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
from sbmlutils.metadata.annotator import (
    Annotation,
    ExternalAnnotation,
    ModelAnnotator,
)
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


def _annotated_model(resources: list[str], sbml_path: Path) -> None:
    """Write a model with one species per given annotation resource.

    Args:
        resources: the annotation resources, as a model definition gives them
        sbml_path: path the SBML is written to
    """
    create_model(
        model=Model(
            sid="annotation",
            compartments=[Compartment("c", 1.0)],
            species=[
                Species(
                    f"s{k}",
                    compartment="c",
                    initialAmount=1.0,
                    annotations=[(BQB.IS, resource)],
                )
                for k, resource in enumerate(resources, start=1)
            ],
        ),
        filepath=sbml_path,
        validation_options=ValidationOptions(units_consistency=False),
    )


def _annotated_species(resource: str, sbml_path: Path) -> None:
    """Write a model with a single species annotated with the given resource.

    Args:
        resource: the annotation resource, as a model definition gives it
        sbml_path: path the SBML is written to
    """
    _annotated_model([resource], sbml_path)


def _annotator_records(
    caplog: pytest.LogCaptureFixture, level: str
) -> list[logging.LogRecord]:
    """Get the records the annotator logged at the given level.

    Args:
        caplog: the pytest log capture fixture
        level: the level name, e.g. `WARNING`

    Returns:
        every record of the annotator logger at that level
    """
    return [
        record
        for record in caplog.records
        if record.name == "sbmlutils.metadata.annotator" and record.levelname == level
    ]


#: a collection of this test suite, and a second one, which the
#: identifiers.org registry does not know. Both name no database at all: the
#: registry holds the namespaces of real, resolvable data providers, so
#: neither of these is ever registered. A real collection which is unknown
#: today, `sabiork` or `unit`, would turn every test below red on the day it
#: is registered, without a line of code changing here - the registry is
#: downloaded and refreshed by pymetadata, so it is not the installed version
#: which decides what these tests see.
UNKNOWN_COLLECTION: str = "sbmlutils.test.collection1"
OTHER_UNKNOWN_COLLECTION: str = "sbmlutils.test.collection2"

#: resources pymetadata cannot canonicalize without changing what they say,
#: measured with pymetadata 0.6.4. All of them are malformed: the first three
#: name a collection and no term, so there is no canonical resource at all,
#: and the last names a term and an empty collection, whose canonical
#: resource `https://identifiers.org//bar` no longer parses as a resource of
#: identifiers.org
LOSSY_RESOURCES: list[str] = [
    f"urn:miriam:{UNKNOWN_COLLECTION}",
    f"urn:miriam:{UNKNOWN_COLLECTION}:",
    f"{UNKNOWN_COLLECTION}/",
    "urn:miriam::bar",
]


@pytest.mark.parametrize("resource", LOSSY_RESOURCES)
def test_annotation_resource_which_cannot_be_normalized_is_written_as_given(
    resource: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a resource is written as given rather than as something else.

    An annotation is written as `RDFAnnotation.resource_normalized`, which
    does not exist for a resource without a term and is not a resource of
    identifiers.org any more for one without a collection. Writing either
    would make the annotation say something else than the model definition
    did.
    """
    sbml_path = tmp_path / "annotation.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        _annotated_species(resource, sbml_path)

    assert _written_resources(sbml_path, "s1") == [resource]
    warnings = _annotator_records(caplog, "WARNING")
    assert len(warnings) == 1, caplog.text
    assert resource in warnings[0].getMessage()


#: resources which pymetadata canonicalizes to an identifiers.org URL of
#: their collection and term. The first four are the forms of a collection
#: of the registry, which are written as the compact URL: a classic URL, a
#: MIRIAM URN, the `http` spelling of the compact URL and a bare compact
#: identifier. The others cannot be written as a compact URL, because the
#: registry does not know the collection or because the term does not carry
#: the prefix of its collection, and keep the classic form
#: `https://identifiers.org/<collection>/<term>`; up to pymetadata 0.6.3
#: those lost their collection and were written as given instead
NORMALIZED_RESOURCES: list[tuple[str, str]] = [
    ("chebi/CHEBI:12965", "https://identifiers.org/CHEBI:12965"),
    ("urn:miriam:chebi:CHEBI%3A33699", "https://identifiers.org/CHEBI:33699"),
    ("http://identifiers.org/BTO:0000131", "https://identifiers.org/BTO:0000131"),
    ("UO:0000021", "https://identifiers.org/UO:0000021"),
    (
        f"http://identifiers.org/{UNKNOWN_COLLECTION}/1406",
        f"https://identifiers.org/{UNKNOWN_COLLECTION}/1406",
    ),
    (
        f"http://identifiers.org/{UNKNOWN_COLLECTION}/XX:0000040",
        f"https://identifiers.org/{UNKNOWN_COLLECTION}/XX:0000040",
    ),
    (
        "https://identifiers.org/SBMLUTILS.TEST.COLLECTION1:0000012",
        "https://identifiers.org/SBMLUTILS.TEST.COLLECTION1:0000012",
    ),
    (
        "http://identifiers.org/chebi/000000035",
        "https://identifiers.org/chebi/000000035",
    ),
    (
        f"urn:miriam:{UNKNOWN_COLLECTION}:bar",
        f"https://identifiers.org/{UNKNOWN_COLLECTION}/bar",
    ),
]


@pytest.mark.parametrize("resource, expected", NORMALIZED_RESOURCES)
def test_annotation_resource_of_a_known_collection_is_normalized(
    resource: str, expected: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a resource which keeps its collection and term is normalized.

    Every one of these normalizes to an identifiers.org URL of the collection
    and term it was given with, so nothing is lost and no warning is due.
    """
    sbml_path = tmp_path / "annotation.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        _annotated_species(resource, sbml_path)

    assert _written_resources(sbml_path, "s1") == [expected]
    assert not _annotator_records(caplog, "WARNING"), caplog.text


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
    assert not _annotator_records(caplog, "WARNING"), caplog.text


#: three resources without a term of one collection and two of another,
#: enough to tell a per-collection report from a per-resource one
TWO_LOSSY_COLLECTIONS: list[str] = [
    f"urn:miriam:{UNKNOWN_COLLECTION}",
    f"urn:miriam:{UNKNOWN_COLLECTION}:",
    f"{UNKNOWN_COLLECTION}/",
    f"urn:miriam:{OTHER_UNKNOWN_COLLECTION}",
    f"{OTHER_UNKNOWN_COLLECTION}/",
]


def test_annotation_losses_are_reported_once_per_collection(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a document reports one warning per collection, not per resource.

    Writing one warning per resource buried every other message, 19853 of
    them for the Recon3D fixture while pymetadata up to 0.6.3 lost the
    collections the registry does not know, and taught users to silence the
    logger. The detail of each resource stays available at debug.
    """
    sbml_path = tmp_path / "annotation.xml"
    with caplog.at_level(logging.DEBUG, logger="sbmlutils.metadata.annotator"):
        _annotated_model(TWO_LOSSY_COLLECTIONS, sbml_path)

    warnings = [record.getMessage() for record in _annotator_records(caplog, "WARNING")]
    assert len(warnings) == 2, caplog.text
    # the report is sorted by collection, so the first one comes first
    assert f"'{UNKNOWN_COLLECTION}'" in warnings[0]
    assert f"'{OTHER_UNKNOWN_COLLECTION}'" in warnings[1]
    # each names how many resources of its collection were written as given
    assert warnings[0].startswith("3 ") and warnings[1].startswith("2 ")
    # each names an example resource of its own collection
    assert f"'urn:miriam:{UNKNOWN_COLLECTION}'" in warnings[0]
    assert f"'urn:miriam:{OTHER_UNKNOWN_COLLECTION}'" in warnings[1]

    # the detail of every single resource is still available, at debug
    details = [record.getMessage() for record in _annotator_records(caplog, "DEBUG")]
    for k, resource in enumerate(TWO_LOSSY_COLLECTIONS, start=1):
        assert any(resource in detail for detail in details), (resource, details)
        assert _written_resources(sbml_path, f"s{k}") == [resource]


def test_annotation_losses_do_not_leak_between_documents(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that each written document reports its own resources.

    The collector is installed per document. A collector kept beyond the
    document it was installed for would add the resources of the first
    document to the report of the second.
    """
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        _annotated_model(TWO_LOSSY_COLLECTIONS[:3], tmp_path / "first.xml")
        first = [
            record.getMessage() for record in _annotator_records(caplog, "WARNING")
        ]
        caplog.clear()
        _annotated_model(TWO_LOSSY_COLLECTIONS[3:], tmp_path / "second.xml")
        second = [
            record.getMessage() for record in _annotator_records(caplog, "WARNING")
        ]

    assert len(first) == 1 and first[0].startswith("3 ")
    assert f"'{UNKNOWN_COLLECTION}'" in first[0]
    assert len(second) == 1 and second[0].startswith("2 ")
    assert f"'{OTHER_UNKNOWN_COLLECTION}'" in second[0]


def test_annotation_loss_without_a_collection_is_grouped_as_such(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a resource with an empty collection is still reported.

    There is no collection to group such a resource under, and dropping it
    from the report for that reason would hide it entirely, so all of them
    are reported together under a placeholder.
    """
    sbml_path = tmp_path / "annotation.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        _annotated_model(["urn:miriam::bar", "urn:miriam::baz"], sbml_path)

    warnings = [record.getMessage() for record in _annotator_records(caplog, "WARNING")]
    assert len(warnings) == 1, caplog.text
    assert warnings[0].startswith("2 ") and "'<no collection>'" in warnings[0], warnings


def test_annotation_loss_outside_a_document_is_reported_per_resource(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a single annotation written on its own reports itself.

    `ModelAnnotator.annotate_sbase` annotates one element at a time and is
    called directly. There is no document scope then, and nothing would ever
    report a resource which was only collected.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel("m")
    compartment: libsbml.Compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setConstant(True)

    resource = f"urn:miriam:{UNKNOWN_COLLECTION}"
    with caplog.at_level(logging.WARNING, logger="sbmlutils.metadata.annotator"):
        ModelAnnotator.annotate_sbase(compartment, Annotation(BQB.IS, resource))

    warnings = [record.getMessage() for record in _annotator_records(caplog, "WARNING")]
    assert len(warnings) == 1, caplog.text
    assert resource in warnings[0]
    del doc
