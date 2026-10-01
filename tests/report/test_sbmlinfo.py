"""Test the SBML report information."""

import libsbml
import pytest

from sbmlutils.report.sbmlinfo import SBMLDocumentInfo
from sbmlutils.resources import EXAMPLES_DIR, REPRESSILATOR_SBML

REACTION_SBML = EXAMPLES_DIR / "reaction.xml"


def test_info_for_repressilator() -> None:
    """The report information is created for a model."""
    info = SBMLDocumentInfo.from_sbml(REPRESSILATOR_SBML)
    assert info.info["doc"]
    assert info.info["model"]["reactions"]


def test_info_for_variable_stoichiometry() -> None:
    """Reactions with variable (NaN) stoichiometry get an equation."""
    info = SBMLDocumentInfo.from_sbml(REACTION_SBML)
    equations = {r["id"]: r["equation"] for r in info.info["model"]["reactions"]}
    assert equations["v1"] == "x &#10142; y"
    assert equations["v2"] == "x &#10142; 2.0 y"
    # stoichiometry set by rules via the species reference id
    assert equations["v3"] == "f1 x &#10142; f2 y"
    assert equations["v4"] == "v4_x x &#10142; v4_y y"


@pytest.mark.parametrize(
    "stoichiometry, expected",
    [
        (1.0, "x"),
        (-1.0, "-x"),
        (2.0, "2.0 x"),
        (-2.5, "-2.5 x"),
        (0.0, "0.0 x"),
        (float("nan"), "sr x"),
    ],
)
def test_half_equation(stoichiometry: float, expected: str) -> None:
    """Half equations for the different stoichiometries."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setId("sr")
    sr.setSpecies("x")
    sr.setStoichiometry(stoichiometry)
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == expected


def test_half_equation_nan_without_id() -> None:
    """A variable stoichiometry without species reference id is marked."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    reaction = model.createReaction()
    sr = reaction.createReactant()
    sr.setSpecies("x")
    sr.setStoichiometry(float("nan"))
    assert SBMLDocumentInfo._half_equation(reaction.getListOfReactants()) == "? x"


def _anonymous_events_doc() -> libsbml.SBMLDocument:
    """Document with two identical events without id or metaId."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId("m")
    p: libsbml.Parameter = model.createParameter()
    p.setId("p")
    p.setValue(0.0)
    p.setConstant(False)
    for _ in range(2):
        event: libsbml.Event = model.createEvent()
        event.setUseValuesFromTriggerTime(True)
        trigger: libsbml.Trigger = event.createTrigger()
        trigger.setInitialValue(False)
        trigger.setPersistent(True)
        trigger.setMath(libsbml.parseL3Formula("time > 10"))
        assignment: libsbml.EventAssignment = event.createEventAssignment()
        assignment.setVariable("p")
        assignment.setMath(libsbml.parseL3Formula("1"))
    return doc


def test_primary_keys_unique_for_identical_elements() -> None:
    """Identical elements without id or metaId get distinct primary keys."""
    info = SBMLDocumentInfo(doc=_anonymous_events_doc())
    events = info.info["model"]["events"]
    assert len(events) == 2
    assert events[0]["pk"] != events[1]["pk"]
    assert [e["pk"] for e in events] == ["Event:listOfEvents/0", "Event:listOfEvents/1"]


def test_primary_keys_stable() -> None:
    """The primary keys of the same document are the same in every run."""
    first = SBMLDocumentInfo(doc=_anonymous_events_doc()).info["model"]["events"]
    second = SBMLDocumentInfo(doc=_anonymous_events_doc()).info["model"]["events"]
    assert [e["pk"] for e in first] == [e["pk"] for e in second]


def test_primary_key_of_nested_element() -> None:
    """An element without id is keyed below the element which owns it."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    reaction: libsbml.Reaction = model.createReaction()
    reaction.setId("R1")
    law: libsbml.KineticLaw = reaction.createKineticLaw()
    reactant: libsbml.SpeciesReference = reaction.createReactant()
    product: libsbml.SpeciesReference = reaction.createProduct()
    assert SBMLDocumentInfo._get_pk(law) == "KineticLaw:R1/kineticLaw"
    assert SBMLDocumentInfo._get_pk(reactant) == "SpeciesReference:R1/listOfReactants/0"
    assert SBMLDocumentInfo._get_pk(product) == "SpeciesReference:R1/listOfProducts/0"


def test_primary_keys_of_reactant_and_product_differ() -> None:
    """A reactant and a product without id of one reaction have distinct keys."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    reaction: libsbml.Reaction = model.createReaction()
    reaction.setId("R1")
    for sr in [reaction.createReactant(), reaction.createProduct()]:
        sr.setSpecies("x")
        sr.setStoichiometry(1.0)
    assert SBMLDocumentInfo._get_pk(
        reaction.getReactant(0)
    ) != SBMLDocumentInfo._get_pk(reaction.getProduct(0))


def test_primary_key_not_a_metaid() -> None:
    """A derived key never equals a metaId, which may contain a '.'."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    first: libsbml.Event = model.createEvent()
    first.setMetaId("listOfEvents.1")
    model.createEvent()
    keys = [SBMLDocumentInfo._get_pk(e) for e in model.getListOfEvents()]
    assert keys == ["Event:listOfEvents.1", "Event:listOfEvents/1"]


def test_equation_without_modifiers() -> None:
    """A reaction without modifiers has no trailing separator in its equation."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    reaction: libsbml.Reaction = model.createReaction()
    reaction.setReversible(False)
    for sr in [reaction.createReactant(), reaction.createProduct()]:
        sr.setStoichiometry(1.0)
    reaction.getReactant(0).setSpecies("x")
    reaction.getProduct(0).setSpecies("y")
    assert (
        SBMLDocumentInfo._equation_from_reaction(reaction, modifiers=True)
        == "x &#10142; y"
    )
    reaction.createModifier().setSpecies("e")
    assert (
        SBMLDocumentInfo._equation_from_reaction(reaction, modifiers=True)
        == "x &#10142; y [e]"
    )
