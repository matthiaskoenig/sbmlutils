"""Test the SBML report information."""

import io
import json
from pathlib import Path

import libsbml
import pytest

from sbmlutils.report.sbmlinfo import SBMLDocumentInfo, clean_empty
from sbmlutils.resources import EXAMPLES_DIR, REPRESSILATOR_SBML

REACTION_SBML = EXAMPLES_DIR / "reaction.xml"


def test_json_preserves_zero_and_false() -> None:
    """Removing empty entries must preserve model values and boolean flags."""
    assert clean_empty(
        {"value": 0.0, "constant": False, "empty": None, "values": [0, False, ""]}
    ) == {"value": 0.0, "constant": False, "values": [0, False]}
    doc = libsbml.SBMLDocument(3, 2)
    parameter = doc.createModel().createParameter()
    parameter.setId("p")
    parameter.setValue(0.0)
    parameter.setConstant(False)
    info = SBMLDocumentInfo(doc)
    serialized = json.loads(info.to_json())["model"]["parameters"][0]
    assert serialized["value"] == 0.0
    assert serialized["constant"] is False


def test_report_without_initial_assignment_math() -> None:
    """L3V2 allows an initial assignment without math; it is still reportable."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    parameter = model.createParameter()
    parameter.setId("p")
    parameter.setConstant(True)
    parameter.setUnits("dimensionless")
    model.createInitialAssignment().setSymbol("p")
    info = SBMLDocumentInfo(doc)
    assert info.info["model"]["initialAssignments"][0]["math"] is None
    assert info.info["model"]["parameters"][0]["assignment"]["math"] is None


def test_report_preserves_neutral_species_charge() -> None:
    """A charge of zero means neutral, rather than an unset FBC attribute."""
    namespaces = libsbml.SBMLNamespaces(3, 2)
    namespaces.addPackageNamespace("fbc", 2)
    doc = libsbml.SBMLDocument(namespaces)
    model = doc.createModel()
    model.createCompartment().setId("c")
    species = model.createSpecies()
    species.setId("S")
    species.setCompartment("c")
    species.getPlugin("fbc").setCharge(0)
    data = json.loads(SBMLDocumentInfo(doc).to_json())
    assert data["model"]["species"][0]["fbc"]["charge"] == 0


@pytest.mark.parametrize(
    "unit_id",
    [
        "mole",
        "dimensionless",
        "second",
        "litre",
        "metre",
        "gram",
        "avogadro",
        "custom",
        "unset",
        "invalid",
    ],
)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("version", [1, 2])
def test_parameter_units_match_libsbml_without_model_analysis(
    unit_id: str, local: bool, version: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Direct L3 unit resolution matches native analysis for both parameter types."""
    from sbmlutils.report.units import udef_to_string

    doc = libsbml.SBMLDocument(3, version)
    model = doc.createModel()
    definition = model.createUnitDefinition()
    definition.setId("custom")
    unit = definition.createUnit()
    unit.setKind(libsbml.UNIT_KIND_MOLE)
    unit.setScale(-3)
    unit.setMultiplier(2)
    unit.setExponent(2)
    reaction = model.createReaction()
    reaction.setId("R")
    law = reaction.createKineticLaw()
    parameter = law.createLocalParameter() if local else model.createParameter()
    parameter.setId("p")
    if unit_id != "unset":
        parameter.setUnits(unit_id)
    expected = udef_to_string(parameter.getDerivedUnitDefinition())

    def forbidden(*_args: object) -> None:
        raise AssertionError("Parameter requested whole-model unit analysis")

    monkeypatch.setattr(type(parameter), "getDerivedUnitDefinition", forbidden)
    info = SBMLDocumentInfo(doc)
    actual = (
        info.info["model"]["reactions"][0]["kineticLaw"]["localParameters"][0]
        if local
        else info.info["model"]["parameters"][0]
    )
    assert actual["derivedUnits"] == expected


def test_parameter_unit_cache_is_scoped_to_model_and_traversal() -> None:
    """Same-named units in different models or changed definitions stay distinct."""
    namespaces = libsbml.SBMLNamespaces(3, 2)
    namespaces.addPackageNamespace("comp", 1)
    doc = libsbml.SBMLDocument(namespaces)
    main = doc.createModel()
    main.setId("main")
    nested = doc.getPlugin("comp").createModelDefinition()
    nested.setId("nested")
    for model, multiplier in [(main, 1), (nested, 2)]:
        definition = model.createUnitDefinition()
        definition.setId("custom")
        unit = definition.createUnit()
        unit.setKind(libsbml.UNIT_KIND_MOLE)
        unit.setExponent(1)
        unit.setScale(0)
        unit.setMultiplier(multiplier)
        parameter = model.createParameter()
        parameter.setId("p")
        parameter.setUnits("custom")
    info = SBMLDocumentInfo(doc)
    assert info.info["model"]["parameters"][0]["derivedUnits"] == "mol"
    assert info.info["modelDefinitions"][0]["parameters"][0]["derivedUnits"] == "2 mol"
    main.getUnitDefinition("custom").getUnit(0).setMultiplier(3)
    assert info.create_info()["model"]["parameters"][0]["derivedUnits"] == "3 mol"


def test_report_can_skip_expensive_representations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A lightweight report never invokes unit analysis, XML or LaTeX rendering."""
    doc = _anonymous_events_doc()

    def forbidden(*_args: object) -> None:
        raise AssertionError("An expensive representation was requested")

    monkeypatch.setattr(libsbml.Parameter, "getDerivedUnitDefinition", forbidden)
    monkeypatch.setattr(libsbml.SBase, "toSBML", forbidden)
    monkeypatch.setattr("sbmlutils.report.sbmlinfo.astnode_to_latex", forbidden)
    info = SBMLDocumentInfo(
        doc, include_derived_units=False, include_xml=False, include_math=False
    )
    parameter = info.info["model"]["parameters"][0]
    assert parameter["value"] == 0.0
    assert parameter["derivedUnits"] is None
    assert parameter["xml"] is None
    assert info.info["model"]["events"][0]["trigger"]["math"] is None


def test_json_file_and_stream_match_string(tmp_path: Path) -> None:
    """Streaming JSON preserves the same report as the string API."""
    info = SBMLDocumentInfo(_anonymous_events_doc())
    stream = io.StringIO()
    info.write_json(stream)
    path = tmp_path / "report.json"
    info.write_json(path)
    assert stream.getvalue() == info.to_json()
    assert path.read_text(encoding="utf-8") == info.to_json()


def test_unnamed_element_index_scales_linearly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A report scans a parent list once to index all its unnamed elements."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    for _ in range(100):
        model.createConstraint().setMath(libsbml.parseL3Formula("true"))
    scanned = 0
    original = libsbml.ListOfConstraints.__iter__

    def count_items(self: libsbml.ListOfConstraints):
        nonlocal scanned
        for item in original(self):
            scanned += 1
            yield item

    monkeypatch.setattr(libsbml.ListOfConstraints, "__iter__", count_items)
    info = SBMLDocumentInfo(doc)
    assert scanned == 200  # one report traversal and one indexing traversal
    assert [c["pk"] for c in info.info["model"]["constraints"]] == [
        f"Constraint:listOfConstraints/{k}" for k in range(100)
    ]
    # An index must not survive a traversal when the document can be edited.
    model.removeConstraint(0)
    assert len(info.create_info()["model"]["constraints"]) == 99


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
    ("stoichiometry", "expected"),
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
