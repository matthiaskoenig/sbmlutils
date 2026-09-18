"""Testing the factory methods."""

from pathlib import Path
from typing import Any

import libsbml
import numpy as np
import pytest

from sbmlutils import factory
from sbmlutils.factory import *
from sbmlutils.io import read_sbml
from sbmlutils.metadata import BQB
from sbmlutils.reaction_equation import EquationPart
from sbmlutils.validation import ValidationOptions

compartment_value_data = [
    (
        1.0,
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        1,
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        np.nan,
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1.0",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "NaN",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "exp(10)",
        True,
        {"compartments": 1, "parameters": 0, "initial_assignments": 1, "rules": 0},
    ),
    (
        1.0,
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        1,
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1.0",
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "1",
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 0},
    ),
    (
        "exp(10)",
        False,
        {"compartments": 1, "parameters": 0, "initial_assignments": 0, "rules": 1},
    ),
]


@pytest.mark.parametrize("value,constant,expected", compartment_value_data)
def test_compartment_value(
    value: Any, constant: bool, expected: dict, tmp_path: Path
) -> None:
    """Test compartment value."""
    m1: ModelDict = {
        "sid": "compartment_value",
        "compartments": [Compartment(sid="C", value=value, constant=constant)],
    }

    result = create_model(
        model=Model(**m1),
        filepath=tmp_path / "model.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )

    doc: libsbml.SBMLDocument = read_sbml(source=result.sbml_path)
    model: libsbml.Model = doc.getModel()
    assert model.getNumCompartments() == expected["compartments"]
    assert model.getNumInitialAssignments() == expected["initial_assignments"]
    assert model.getNumRules() == expected["rules"]


parameter_value_data = [
    (1.0, True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    (1, True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    (np.nan, True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1.0", True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1", True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("NaN", True, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("exp(10)", True, {"parameters": 1, "initial_assignments": 1, "rules": 0}),
    (1.0, False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    (1, False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1.0", False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("1", False, {"parameters": 1, "initial_assignments": 0, "rules": 0}),
    ("exp(10)", False, {"parameters": 1, "initial_assignments": 0, "rules": 1}),
]


@pytest.mark.parametrize("value,constant,expected", parameter_value_data)
def test_parameter_value(
    value: Any, constant: bool, expected: dict, tmp_path: Path
) -> None:
    """Test parameter value."""
    m1: ModelDict = {
        "sid": "parameter_value",
        "parameters": [Parameter(sid="p", value=value, constant=constant)],
    }

    result = create_model(
        model=Model(**m1),
        filepath=tmp_path / "model.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )

    doc: libsbml.SBMLDocument = read_sbml(source=result.sbml_path)
    model: libsbml.Model = doc.getModel()
    assert model.getNumParameters() == expected["parameters"]
    assert model.getNumInitialAssignments() == expected["initial_assignments"]
    assert model.getNumRules() == expected["rules"]


def test_reaction_creation() -> None:
    """Test Equation.

    bA: A_ext => A; (scale_f*(Vmax_bA/Km_A)*(A_ext - A))/(1 dimensionless + A_ext/Km_A + A/Km_A);
    """
    mmole_per_s = UnitDefinition("mmole_per_s", "mmole/s")
    rt = Reaction(
        sid="bA",
        name="bA (A import)",
        equation="A_ext => A []",
        compartment="membrane",
        pars=[],
        rules=[],
        formula=(
            "scale_f*(Vmax_bA/Km_A)*(A_ext - A))/(1 dimensionless + A_ext/Km_A + A/Km_A",
            mmole_per_s,
        ),
    )
    assert rt


def test_event() -> None:
    """Test event."""
    objects = [
        Parameter(sid="p1", value=0.0, constant=False),
        Event(sid="e1", trigger="time >= 10", assignments={"p1": 10.0}),
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    factory.create_objects(model, obj_iter=objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 1


def test_event2() -> None:
    """Test event."""
    objects = [
        Compartment("c", value=1.0),
        Species("S1", initialAmount=1.0, compartment="c"),
        Parameter(sid="p1", value=0.0, constant=False),
        Event(
            sid="e1", trigger="time >= 100", assignments={"p1": 10.0, "S1": "p1 + 10"}
        ),
    ]

    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()
    factory.create_objects(model, obj_iter=objects)

    events = model.getListOfEvents()
    assert len(events) == 1
    e = model.getEvent("e1")
    assert e is not None
    assert e.getId() == "e1"
    assignments = e.getListOfEventAssignments()
    assert len(assignments) == 2


def test_create_model_serializations(tmp_path: Path) -> None:
    """Create the antimony and markdown serialization next to the SBML file."""
    model = Model(
        sid="serializations",
        compartments=[Compartment(sid="c", value=1.0)],
        species=[Species(sid="S1", initialConcentration=10.0, compartment="c")],
        parameters=[Parameter(sid="k1", value=0.1)],
        reactions=[Reaction(sid="J0", equation="S1 -> ", formula="k1 * S1")],
    )
    result = create_model(
        model=model,
        filepath=tmp_path / "model.xml",
        validation_options=ValidationOptions(units_consistency=False),
        create_antimony=True,
        create_markdown=True,
    )
    assert result.antimony_path == tmp_path / "model.ant"
    assert result.markdown_path == tmp_path / "model.md"
    ant_str = result.antimony_path.read_text(encoding="utf-8")
    assert "model" in ant_str
    assert "J0:" in ant_str
    md_str = result.markdown_path.read_text(encoding="utf-8")
    assert "# model: serializations" in md_str
    assert "k1 = 0.1" in md_str


def test_create_model_no_serializations(tmp_path: Path) -> None:
    """No additional files are written by default."""
    model = Model(
        sid="no_serializations",
        parameters=[Parameter(sid="k1", value=0.1)],
    )
    result = create_model(
        model=model,
        filepath=tmp_path / "model.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )
    assert result.antimony_path is None
    assert result.markdown_path is None
    assert not (tmp_path / "model.ant").exists()
    assert not (tmp_path / "model.md").exists()


def test_assignment_rule_keeps_its_id() -> None:
    """Test that a rule id is written and does not overwrite the variable.

    `libsbml.Rule.setId` aliases the `variable` attribute: it returns -16 and
    is a no-op, so rule ids were silently lost. `setIdAttribute` is the L3V2
    accessor which actually sets the id.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    parameter = model.createParameter()
    parameter.setId("S1")
    parameter.setConstant(False)

    rule = AssignmentRule("S1", value="2 * 3", sid="my_rule")
    rule.create_sbml(model)

    sbml_rule = model.getRule(0)
    assert sbml_rule.getVariable() == "S1"
    assert sbml_rule.getIdAttribute() == "my_rule"


def test_rule_without_id_is_written_without_id(tmp_path: Path) -> None:
    """Test that a rule without an id is written without one.

    `AssignmentRule` and `RateRule` used to generate the id
    `AssignmentRule_<variable>` and `RateRule_<variable>` for a rule without
    one. `libsbml.Rule.setId` is a no-op, so the generated id was never
    written, until the ids of rules were set through `setIdAttribute`: then
    every rule written at SBML L3V2 gained an id which the model definition
    never had.
    """
    model = Model(
        sid="rules",
        parameters=[
            Parameter("p1", 0.0, constant=False),
            Parameter("p2", 0.0, constant=False),
        ],
        rules=[AssignmentRule("p1", "time")],
        rate_rules=[RateRule("p2", "1.0")],
    )
    assert [rule.sid for rule in [*model.rules, *model.rate_rules]] == [None, None]

    create_model(
        model=model,
        filepath=tmp_path / "rules.xml",
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    doc: libsbml.SBMLDocument = read_sbml(tmp_path / "rules.xml")
    sbml_model: libsbml.Model = doc.getModel()
    assert sbml_model.getNumRules() == 2
    rule: libsbml.Rule
    for rule in sbml_model.getListOfRules():
        assert not rule.isSetIdAttribute(), (
            f"the rule of '{rule.getVariable()}' gained the id "
            f"'{rule.getIdAttribute()}'"
        )


def test_unit_definition_from_units() -> None:
    """Test that a UnitDefinition can be built from explicit units."""
    udef = UnitDefinition(
        "mM",
        units=[Unit("mole", 1.0, -3, 1.0), Unit("litre", -1.0, 0, 1.0)],
        name="millimolar",
    )
    assert udef.units is not None
    assert len(udef.units) == 2
    assert udef.units[0].kind == "mole"
    assert udef.units[0].scale == -3


def test_unit_definition_preserves_scale() -> None:
    """Test that an explicit scale survives writing to SBML.

    `create_sbml` used to hardcode `scale = 0`, so a source using
    `scale="-3" multiplier="1"` came back as `scale="0" multiplier="0.001"`.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    udef = UnitDefinition("mM", units=[Unit("mole", 1.0, -3, 1.0)])
    udef.create_sbml(model)

    sbml_udef = model.getUnitDefinition("mM")
    assert sbml_udef.getUnit(0).getScale() == -3
    assert sbml_udef.getUnit(0).getMultiplier() == 1.0


def test_unit_definition_non_pint_sid() -> None:
    """Test that a unit id which pint cannot parse is representable.

    The SBML test suite uses the ids `substance`, `volume` and `time`, and
    `definition` defaults to `sid`, so these used to raise UndefinedUnitError.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    udef = UnitDefinition("substance", units=[Unit("mole", 1.0, 0, 1.0)])
    udef.create_sbml(model)

    assert model.getUnitDefinition("substance") is not None


def test_model_units_accepts_list() -> None:
    """Test that Model.units accepts a list of UnitDefinitions."""
    model = Model(
        "test",
        units=[UnitDefinition("mM", units=[Unit("mole", 1.0, -3, 1.0)])],
    )
    assert isinstance(model.units, list)
    assert model.units[0].sid == "mM"


def test_model_units_accepts_units_class() -> None:
    """Test that the `class U(Units)` authoring style still works."""

    class U(Units):
        mM = UnitDefinition("mM", "mmole/liter")

    model = Model("test", units=U)
    assert isinstance(model.units, list)
    assert any(udef.sid == "mM" for udef in model.units)


def test_unit_reference_by_id() -> None:
    """Test that a unit can be referenced by its id string."""
    assert UnitDefinition.get_uid_for_unit("mymole") == "mymole"


def test_unit_definition_name() -> None:
    """Test that a name is only derived from a pint definition.

    A pint expression is the readable label of a definition and is used as its
    name. With explicit units the definition is only the id, and deriving a
    name from it would invent a name the source never had, which is exactly
    what a round trip must not do.
    """
    assert UnitDefinition("substance", units=[Unit("mole")]).name is None
    assert UnitDefinition("mM", "mmole/liter").name == "mmole/liter"
    assert (
        UnitDefinition("substance", units=[Unit("mole")], name="amount").name
        == "amount"
    )


def test_unit_definition_from_units_writes_no_name() -> None:
    """Test that a definition with explicit units writes no name attribute."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    UnitDefinition("substance", units=[Unit("mole")]).create_sbml(model)

    assert not model.getUnitDefinition("substance").isSetName()


def test_reaction_formula_string_is_a_kinetic_law() -> None:
    """Test that a formula string is normalized into a KineticLaw."""
    reaction = Reaction("r1", "S1 -> S2", formula="k1 * S1")
    assert isinstance(reaction.formula, KineticLaw)
    assert reaction.formula.math == "k1 * S1"
    assert reaction.formula.local_parameters == []


def test_reaction_formula_tuple_keeps_the_unit() -> None:
    """Test that the unit of a `(math, unit)` tuple is kept.

    `Formula` parsed the unit and `create_sbml` then used only the math, so
    the unit was silently dropped.
    """
    reaction = Reaction("r1", "S1 -> S2", formula=("k1 * S1", "mole_per_s"))
    assert isinstance(reaction.formula, KineticLaw)
    assert reaction.formula.unit == "mole_per_s"


def test_local_parameters_are_local() -> None:
    """Test that local parameters are written into the kinetic law.

    `Reaction.pars` creates global model parameters, which collide when two
    reactions use the same local parameter id.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.createCompartment().setId("c")
    for sid in ("S1", "S2"):
        species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")

    reaction = Reaction(
        "r1",
        "S1 -> S2",
        formula=KineticLaw(math="k * S1", local_parameters=[LocalParameter("k", 0.5)]),
    )
    reaction.create_sbml(model)

    assert model.getNumParameters() == 0, "a local parameter leaked into the model"
    klaw = model.getReaction("r1").getKineticLaw()
    assert klaw.getNumLocalParameters() == 1
    assert klaw.getLocalParameter(0).getId() == "k"
    assert klaw.getLocalParameter(0).getValue() == 0.5


def _create_kinetic_law_reaction(
    level: int, version: int, sid: str = "kl1"
) -> tuple[libsbml.SBMLDocument, libsbml.Model]:
    """Build a one-reaction model at the given SBML level/version.

    Args:
        level: the SBML level of the document
        version: the SBML version of the document
        sid: the id to set on the KineticLaw

    Returns:
        the created libsbml.SBMLDocument and its libsbml.Model. The document
        must be kept alive by the caller for as long as the model is used:
        libsbml.Model is owned by its SBMLDocument, and once the document is
        garbage collected, the model becomes a dangling reference.
    """
    doc = libsbml.SBMLDocument(level, version)
    model = doc.createModel()
    model.createCompartment().setId("c")
    for species_id in ("S1", "S2"):
        species = model.createSpecies()
        species.setId(species_id)
        species.setCompartment("c")

    klaw = KineticLaw(math="S1", sid=sid)
    reaction = Reaction("r1", "S1 -> S2", formula=klaw)
    reaction.create_sbml(model)
    return doc, model


def test_kinetic_law_id_not_written_before_l3v2(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a KineticLaw id is silently skipped below SBML L3V2.

    `libsbml.KineticLaw` only gained an `id` attribute in L3V2; on an older
    level/version, including this package's own default of L3V1, attempting
    `setId` fails with an "unexpected attribute" libsbml error. The id must
    be skipped without logging an error, since the caller cannot fix this by
    changing anything about the `KineticLaw` itself.
    """
    with caplog.at_level("WARNING"):
        doc, model = _create_kinetic_law_reaction(level=3, version=1)

    klaw = model.getReaction("r1").getKineticLaw()
    assert not klaw.isSetId()
    assert not any(record.levelname == "ERROR" for record in caplog.records), [
        r.message for r in caplog.records if r.levelname == "ERROR"
    ]
    del doc


def test_kinetic_law_id_written_from_l3v2() -> None:
    """Test that a KineticLaw id is written from SBML L3V2 onward."""
    doc, model = _create_kinetic_law_reaction(level=3, version=2)

    klaw = model.getReaction("r1").getKineticLaw()
    assert klaw.isSetId()
    assert klaw.getId() == "kl1"
    del doc


@pytest.mark.parametrize("version", [1, 2])
def test_constraint_id_written_from_l3v2(
    version: int, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a Constraint id is written from SBML L3V2 on, and only then.

    A constraint, like a kinetic law, only has an `id` attribute from SBML
    L3V2 on. Below, libsbml's `setId` fails with "unexpected attribute", which
    `Sbase._set_fields` used to log as an error for every constraint of a
    model written at the default L3V1, e.g. `examples/model.py`. The caller
    cannot fix that by changing the constraint, so the id is dropped without
    an error.
    """
    doc = libsbml.SBMLDocument(3, version)
    model: libsbml.Model = doc.createModel()
    k: libsbml.Parameter = model.createParameter()
    k.setId("k")
    k.setValue(1.0)
    k.setConstant(True)

    with caplog.at_level("WARNING"):
        Constraint("c1", math="k > 0").create_sbml(model)

    constraint: libsbml.Constraint = model.getConstraint(0)
    assert constraint.isSetMath()
    assert constraint.isSetId() is (version == 2)
    assert not any(record.levelname == "ERROR" for record in caplog.records), [
        r.message for r in caplog.records if r.levelname == "ERROR"
    ]


def test_event_use_values_from_trigger_time_is_honoured() -> None:
    """Test that useValuesFromTriggerTime is written.

    `_set_fields` called `setUseValuesFromTriggerTime(True)` unconditionally,
    discarding the constructor argument, which changes simulation results.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    event = Event(
        "e1",
        trigger="time >= 10",
        assignments={"S1": 5.0},
        useValuesFromTriggerTime=False,
    )
    event.create_sbml(model)

    assert model.getEvent("e1").getUseValuesFromTriggerTime() is False


def test_event_without_id_is_written_without_id() -> None:
    """Test that an event without an id is written without one.

    The id of an event is optional in SBML. `Event` required it as a `str`, so
    the parser named an event without an id `event<k>`.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    p1: libsbml.Parameter = model.createParameter()
    p1.setId("p1")
    p1.setValue(0.0)
    p1.setConstant(False)

    Event(None, trigger="time >= 10", assignments={"p1": 10.0}).create_sbml(model)

    event: libsbml.Event = model.getEvent(0)
    assert not event.isSetId()
    assert event.getNumEventAssignments() == 1


def test_event_assignments_accept_a_dict() -> None:
    """Test that the dict authoring style still works."""
    event = Event("e1", trigger="time >= 10", assignments={"S1": 5.0})
    assert len(event.assignments) == 1
    assert event.assignments[0].variable == "S1"
    assert event.assignments[0].value == 5.0


def test_event_assignments_keep_sbase_fields() -> None:
    """Test that an EventAssignment carries its own metaId and sboTerm."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    event = Event(
        "e1",
        trigger="time >= 10",
        assignments=[EventAssignment("S1", 5.0, metaId="ea1", sboTerm="SBO:0000064")],
    )
    event.create_sbml(model)

    ea = model.getEvent("e1").getEventAssignment(0)
    assert ea.getVariable() == "S1"
    assert ea.getMetaId() == "ea1"
    assert ea.getSBOTermID() == "SBO:0000064"


def test_reaction_reversible_overrides_the_equation() -> None:
    """Test that an explicit `reversible` is honoured.

    `Reaction.reversible` was stored and never read; `_set_fields` used
    `equation.reversible`, so `Reaction(equation='A => B', reversible=True)`
    silently emitted `reversible="false"`.
    """
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.createCompartment().setId("c")
    for sid in ("A", "B"):
        species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")

    reaction = Reaction("r1", "A => B", reversible=True)
    reaction.create_sbml(model)

    assert model.getReaction("r1").getReversible() is True


def _reaction_test_model() -> tuple[libsbml.SBMLDocument, libsbml.Model]:
    """Build a minimal L3V2 model with species 'A', 'B' and 'M' for reaction tests."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.createCompartment().setId("c")
    for sid in ("A", "B", "M"):
        species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")
    return doc, model


def test_reaction_modifier_keeps_sbase_fields() -> None:
    """Test that a modifier's metaId, sboTerm, name, notes and annotation survive.

    `set_speciesref_fields` used to only set `species`, `sid`, `constant`,
    `stoichiometry`, `metaId` and `sboTerm` on a species reference; `name`,
    `notes` and `annotations` were silently dropped, for reactants, products
    and modifiers alike. This asserts against the actual created
    `libsbml.ModifierSpeciesReference`, not against the python `EquationPart`
    it was built from, so it fails if `set_speciesref_fields` stops writing
    any of these.
    """
    _doc, model = _reaction_test_model()
    equation = ReactionEquation(
        reactants=[EquationPart(species="A")],
        products=[EquationPart(species="B")],
        modifiers=[
            EquationPart(
                species="M",
                metaId="mod1",
                sboTerm="SBO:0000019",
                name="modifiername",
                notes="a modifier",
                annotations=[(BQB.IS, "uniprot/P35557")],
            )
        ],
    )
    reaction = Reaction("r1", equation)
    reaction.create_sbml(model)

    modifier: libsbml.ModifierSpeciesReference = model.getReaction("r1").getModifier(0)
    assert modifier.getMetaId() == "mod1"
    assert modifier.getSBOTermID() == "SBO:0000019"
    assert modifier.getName() == "modifiername"
    assert "a modifier" in modifier.getNotesString()
    assert modifier.getNumCVTerms() == 1
    assert "P35557" in modifier.getCVTerm(0).getResourceURI(0)


def test_reaction_reactant_keeps_name_notes_and_annotations() -> None:
    """Test that a reactant's name, notes and annotation survive, not only its metadata.

    Only `metaId`/`sboTerm`/`constant`/`stoichiometry` were set on a
    `SpeciesReference` before this task; `name`, `notes` and `annotations`
    were dropped for reactants and products exactly like for modifiers.
    """
    _doc, model = _reaction_test_model()
    equation = ReactionEquation(
        reactants=[
            EquationPart(
                species="A",
                name="reactantname",
                notes="a reactant",
                annotations=[(BQB.IS, "uniprot/P35557")],
            )
        ],
        products=[EquationPart(species="B")],
    )
    reaction = Reaction("r1", equation)
    reaction.create_sbml(model)

    reactant: libsbml.SpeciesReference = model.getReaction("r1").getReactant(0)
    assert reactant.getName() == "reactantname"
    assert "a reactant" in reactant.getNotesString()
    assert reactant.getNumCVTerms() == 1
    assert "P35557" in reactant.getCVTerm(0).getResourceURI(0)


def test_reaction_speciesref_name_with_space_is_rejected_by_libsbml(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a space-containing species reference name is silently dropped by libsbml.

    `libsbml.SimpleSpeciesReference.setName` (5.21.1) erroneously applies SId
    syntax validation to `name`, which SBML defines as a plain `string`, so
    any name that is not a valid SId, such as one containing a space, is
    rejected with rc=-4 and never set. This is a libsbml defect, not a bug in
    this package (see the comment in `set_speciesref_fields`), but it must be
    surfaced as a warning rather than fail completely silently, and this
    pins that behaviour with a test rather than leaving it to be
    rediscovered by surprise.
    """
    import logging

    _doc, model = _reaction_test_model()
    equation = ReactionEquation(
        reactants=[EquationPart(species="A")],
        products=[EquationPart(species="B")],
        modifiers=[EquationPart(species="M", name="a modifier name")],
    )
    reaction = Reaction("r1", equation)
    with caplog.at_level(logging.WARNING, logger="sbmlutils.factory"):
        reaction.create_sbml(model)

    modifier: libsbml.ModifierSpeciesReference = model.getReaction("r1").getModifier(0)
    assert modifier.getName() == ""
    assert "could not be set" in caplog.text, (
        "the rejected name should be logged, not silently dropped"
    )
