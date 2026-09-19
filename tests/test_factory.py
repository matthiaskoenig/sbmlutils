"""Testing the factory methods."""

import logging
import os
import re
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import libsbml
import numpy as np
import pytest

from sbmlutils import factory
from sbmlutils.factory import *
from sbmlutils.factory import Sbase, SbaseRef
from sbmlutils.io import read_sbml
from sbmlutils.metadata import BQB
from sbmlutils.reaction_equation import EquationPart, ReactionEquation
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


def test_model_units_hint_names_the_missing_unit_lazily(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the hint for a model unit which is not set.

    A strongly recommended unit warns, an optional one informs, and the key
    is a log argument rather than part of the message, so that every hint
    reaches a handler under one message template. `set_model_units` built the
    message with an f-string, which loses the template.
    """
    model = Model(
        "model_units",
        model_units=ModelUnits(
            substance=Units.mole, extent=Units.mole, volume=Units.litre
        ),
    )
    with caplog.at_level(logging.INFO, logger="sbmlutils.factory"):
        create_model(
            model=model,
            filepath=tmp_path / "model.xml",
            validation_options=ValidationOptions(units_consistency=False),
        )

    hints = {
        record.args[0]: (record.levelname, record.msg)
        for record in caplog.records
        if isinstance(record.args, tuple)
        and "should be set in 'model_units'" in record.msg
    }
    assert hints == {
        "time": ("WARNING", "'%s' should be set in 'model_units'."),
        "length": ("INFO", "'%s' should be set in 'model_units'."),
        "area": ("INFO", "'%s' should be set in 'model_units'."),
    }, caplog.text


def test_unit_reference_by_id() -> None:
    """Test that a unit can be referenced by its id string."""
    assert UnitDefinition.get_uid_for_unit("mymole") == "mymole"


def test_unit_reference_without_unit() -> None:
    """Test that no unit at all is no error."""
    assert UnitDefinition.get_uid_for_unit(None) is None


#: a unit of a type the annotations forbid, as it reaches the factory from
#: untyped data; declared `Any` so that the type checker does not flag the
#: deliberate misuse which the runtime guard is tested with
BAD_UNIT: Any = 1.0


def test_bad_unit_type_raises_value_error(tmp_path: Path) -> None:
    """Test that a unit which is neither a UnitDefinition nor an id is refused.

    `1.0` reached `libsbml.Parameter.setUnits` and surfaced as a SWIG
    `TypeError` about `argument 2 of type 'std::string const &'`, which names
    neither the offending value nor the element it was set on.
    """
    model = Model(sid="m", parameters=[Parameter("p", value=1.0, unit=BAD_UNIT)])
    with pytest.raises(ValueError, match="UnitDefinition"):
        create_model(
            model=model,
            filepath=tmp_path / "m.xml",
            validation_options=ValidationOptions(units_consistency=False),
        )


@pytest.mark.parametrize(
    "create",
    [
        lambda: Parameter("p", value=1.0, unit=BAD_UNIT),
        lambda: Species("s", compartment="c", substanceUnit=BAD_UNIT),
        lambda: SbaseRef("ref", unitRef=BAD_UNIT),
        lambda: UncertParameter(
            type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=1.0, unit=BAD_UNIT
        ),
        lambda: UncertSpan(
            type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
            valueLower=1.0,
            valueUpper=2.0,
            unit=BAD_UNIT,
        ),
    ],
    ids=[
        "Parameter.unit",
        "Species.substanceUnit",
        "SbaseRef.unitRef",
        "UncertParameter.unit",
        "UncertSpan.unit",
    ],
)
def test_bad_unit_type_warns_on_construction(
    create: Callable[[], object], caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a unit of a bad type is reported when the element is built.

    `ValueWithUnit` warned about it, every other unit attribute passed the
    value on silently until it reached `get_uid_for_unit`, which now raises.
    """
    with caplog.at_level(logging.WARNING, logger="sbmlutils.factory"):
        create()
    assert any(
        "must be a UnitDefinition or a unit id" in record.message
        and "float" in record.message
        for record in caplog.records
    ), caplog.text


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


def _event_test_model(version: int) -> tuple[libsbml.SBMLDocument, libsbml.Model]:
    """Build an SBML L3 model with the non-constant parameter 'p1' for event tests.

    Args:
        version: the SBML L3 version of the document

    Returns:
        the document and its model. The caller has to hold the document for
        as long as it uses the model: the model is owned by the document and
        dangles once the document is garbage collected.
    """
    doc = libsbml.SBMLDocument(3, version)
    model: libsbml.Model = doc.createModel()
    p1: libsbml.Parameter = model.createParameter()
    p1.setId("p1")
    p1.setValue(0.0)
    p1.setConstant(False)
    return doc, model


#: the SBML of an event with a trigger, a delay and a priority written in the
#: string authoring style, as it was written before they became `Trigger`,
#: `Priority` and `Delay` objects (captured at a59bd4ef)
EVENT_STRING_STYLE_SBML = """<event sboTerm="SBO:0000231" id="e1" name="e" useValuesFromTriggerTime="true">
  <trigger initialValue="false" persistent="true">
    <math xmlns="http://www.w3.org/1998/Math/MathML">
      <apply>
        <geq/>
        <csymbol encoding="text" definitionURL="http://www.sbml.org/sbml/symbols/time"> time </csymbol>
        <cn type="integer"> 10 </cn>
      </apply>
    </math>
  </trigger>
  <delay>
    <math xmlns="http://www.w3.org/1998/Math/MathML">
      <cn type="integer"> 2 </cn>
    </math>
  </delay>
  <priority>
    <math xmlns="http://www.w3.org/1998/Math/MathML">
      <cn type="integer"> 1 </cn>
    </math>
  </priority>
  <listOfEventAssignments>
    <eventAssignment variable="p1">
      <math xmlns="http://www.w3.org/1998/Math/MathML">
        <cn> 10 </cn>
      </math>
    </eventAssignment>
  </listOfEventAssignments>
</event>"""

#: the SBML of an event whose string trigger is configured by the
#: `trigger_persistent` and `trigger_initialValue` arguments (captured at a59bd4ef)
EVENT_TRIGGER_FLAGS_SBML = """<event sboTerm="SBO:0000231" id="e1" name="e" useValuesFromTriggerTime="true">
  <trigger initialValue="true" persistent="false">
    <math xmlns="http://www.w3.org/1998/Math/MathML">
      <apply>
        <geq/>
        <csymbol encoding="text" definitionURL="http://www.sbml.org/sbml/symbols/time"> time </csymbol>
        <cn type="integer"> 20 </cn>
      </apply>
    </math>
  </trigger>
  <listOfEventAssignments>
    <eventAssignment variable="p1">
      <math xmlns="http://www.w3.org/1998/Math/MathML">
        <cn> 20 </cn>
      </math>
    </eventAssignment>
  </listOfEventAssignments>
</event>"""


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize(
    "kwargs, expected",
    [
        (
            {
                "trigger": "time >= 10",
                "priority": "1",
                "delay": "2",
                "assignments": {"p1": 10.0},
            },
            EVENT_STRING_STYLE_SBML,
        ),
        (
            {
                "trigger": "time >= 20",
                "trigger_persistent": False,
                "trigger_initialValue": True,
                "assignments": {"p1": 20.0},
            },
            EVENT_TRIGGER_FLAGS_SBML,
        ),
    ],
    ids=["trigger_priority_delay", "trigger_flags"],
)
def test_event_string_style_writes_the_same_sbml(
    kwargs: dict[str, Any], expected: str, version: int
) -> None:
    """Test that the string authoring style writes the SBML it always wrote.

    `Event(trigger="time >= 10", priority="1", delay="2")` is the documented
    authoring style. The strings are normalized into `Trigger`, `Priority` and
    `Delay` objects, which must not change the SBML written from them.
    """
    doc, model = _event_test_model(version)
    Event("e1", name="e", sboTerm="SBO:0000231", **kwargs).create_sbml(model)

    assert model.getEvent("e1").toSBML() == expected
    del doc


def test_event_string_trigger_is_a_trigger() -> None:
    """Test that the strings of an event are normalized into objects."""
    event = Event("e1", trigger="time >= 10", priority="1", delay="2")

    assert isinstance(event.trigger, Trigger)
    assert event.trigger.math == "time >= 10"
    assert event.trigger.persistent is True
    assert event.trigger.initialValue is False
    assert isinstance(event.priority, Priority)
    assert event.priority.math == "1"
    assert isinstance(event.delay, Delay)
    assert event.delay.math == "2"


def test_event_trigger_flags_configure_a_string_trigger() -> None:
    """Test that `trigger_persistent` and `trigger_initialValue` still apply.

    They are arguments of `Event`, which configure the `Trigger` created from
    a trigger string.
    """
    event = Event(
        "e1",
        trigger="time >= 10",
        trigger_persistent=False,
        trigger_initialValue=True,
    )
    assert isinstance(event.trigger, Trigger)
    assert event.trigger.persistent is False
    assert event.trigger.initialValue is True

    doc, model = _event_test_model(2)
    event.create_sbml(model)
    trigger: libsbml.Trigger = model.getEvent("e1").getTrigger()
    assert trigger.getPersistent() is False
    assert trigger.getInitialValue() is True
    del doc


@pytest.mark.parametrize(
    "flag, value, attribute",
    [
        ("trigger_persistent", False, "persistent"),
        ("trigger_initialValue", True, "initialValue"),
    ],
)
def test_event_trigger_object_wins_over_the_trigger_flags(
    flag: str, value: bool, attribute: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a `Trigger` keeps its own value, and the conflict is logged."""
    trigger = Trigger("time >= 10", persistent=True, initialValue=False)

    kwargs: dict[str, Any] = {flag: value}
    with caplog.at_level("WARNING", logger="sbmlutils.factory"):
        event = Event("e1", trigger=trigger, **kwargs)

    assert event.trigger is trigger
    assert getattr(trigger, attribute) is (not value)
    assert flag in caplog.text


def test_event_trigger_flags_agreeing_with_the_trigger_object_do_not_warn(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a flag which agrees with the `Trigger` is not a conflict."""
    with caplog.at_level("WARNING", logger="sbmlutils.factory"):
        event = Event(
            "e1",
            trigger=Trigger("time >= 10", persistent=False, initialValue=True),
            trigger_persistent=False,
            trigger_initialValue=True,
        )

    assert isinstance(event.trigger, Trigger)
    assert event.trigger.persistent is False
    assert event.trigger.initialValue is True
    assert not caplog.records, [r.getMessage() for r in caplog.records]


def test_event_trigger_flags_without_a_trigger_warn(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a trigger flag on an event without a trigger is logged.

    An event without a trigger, which SBML allows from L3V2 on, has nothing
    the flag could configure.
    """
    with caplog.at_level("WARNING", logger="sbmlutils.factory"):
        event = Event("e1", trigger=None, trigger_persistent=False)

    assert event.trigger is None
    assert "trigger_persistent" in caplog.text


def test_event_none_writes_no_trigger_priority_or_delay() -> None:
    """Test that `None` writes no trigger, priority and delay at all."""
    doc, model = _event_test_model(2)
    Event("e1", trigger=None, assignments={"p1": 1.0}).create_sbml(model)

    event: libsbml.Event = model.getEvent("e1")
    assert not event.isSetTrigger()
    assert not event.isSetPriority()
    assert not event.isSetDelay()
    del doc


def test_event_children_without_math(caplog: pytest.LogCaptureFixture) -> None:
    """Test that a `Trigger`, `Priority` and `Delay` without math are written.

    SBML allows the trigger, the priority and the delay of an event without
    math from L3V2 on. `math=None` writes the element without math, and
    without an error.
    """
    doc, model = _event_test_model(2)
    with caplog.at_level("WARNING", logger="sbmlutils"):
        Event(
            "e1",
            trigger=Trigger(None),
            priority=Priority(None),
            delay=Delay(None),
            assignments={"p1": 1.0},
        ).create_sbml(model)

    event: libsbml.Event = model.getEvent("e1")
    for child in (event.getTrigger(), event.getPriority(), event.getDelay()):
        assert child is not None
        assert not child.isSetMath()
    assert not any(record.levelname == "ERROR" for record in caplog.records), [
        r.getMessage() for r in caplog.records if r.levelname == "ERROR"
    ]
    del doc


@pytest.mark.parametrize("element", ["trigger", "priority", "delay"])
@pytest.mark.parametrize("math", ["time >=", ""], ids=["unparsable", "empty"])
def test_event_unparsable_math_logs_an_error(
    element: str, math: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that math which does not parse is logged as an error.

    It used to become an element without math, silently. An empty string is
    math which does not parse like any other, it is not an element without
    math, which is `math=None`.
    """
    doc, model = _event_test_model(2)
    kwargs: dict[str, Any] = {"trigger": "time >= 10", element: math}
    with caplog.at_level("ERROR", logger="sbmlutils.factory"):
        Event("e1", assignments={"p1": 1.0}, **kwargs).create_sbml(model)

    errors = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert any(f"'{math}'" in message for message in errors), errors
    # the trigger, priority or delay; `libsbml.SBase` declares no `isSetMath`
    child: Any = getattr(model.getEvent("e1"), f"get{element.title()}")()
    assert not child.isSetMath()
    del doc


@pytest.mark.parametrize("version", [1, 2])
def test_event_children_id_written_from_l3v2(
    version: int, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that the id of a trigger, priority and delay is written from L3V2 on.

    Like a kinetic law, they only have an id attribute from SBML L3V2 on, and
    libsbml's `setId` fails with "unexpected attribute" below it. The caller
    cannot fix that by changing the element, so the id is dropped without an
    error.
    """
    doc, model = _event_test_model(version)
    with caplog.at_level("WARNING", logger="sbmlutils"):
        Event(
            "e1",
            trigger=Trigger("time >= 10", sid="t1"),
            priority=Priority("1", sid="pr1"),
            delay=Delay("2", sid="d1"),
            assignments={"p1": 1.0},
        ).create_sbml(model)

    event: libsbml.Event = model.getEvent("e1")
    for child, sid in (
        (event.getTrigger(), "t1"),
        (event.getPriority(), "pr1"),
        (event.getDelay(), "d1"),
    ):
        assert child.isSetId() is (version == 2)
        assert (f'id="{sid}"' in child.toSBML()) is (version == 2)
    assert not any(record.levelname == "ERROR" for record in caplog.records), [
        r.getMessage() for r in caplog.records if r.levelname == "ERROR"
    ]
    del doc


def test_nested_elements_log_no_authoring_hints(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a kinetic law, trigger, priority and delay log no authoring hints.

    `'name' should be set` and `'sboTerm' should be set` help somebody who
    writes a reaction or an event. The kinetic law of a reaction and the
    trigger, priority and delay of an event are created from a string in the
    documented authoring style, which has no place for their name or sboTerm,
    so a hint on them could not be acted upon.
    """
    doc, model = _event_test_model(2)
    model.createCompartment().setId("c")
    for sid in ("A", "B"):
        species: libsbml.Species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")

    with caplog.at_level("WARNING", logger="sbmlutils.factory"):
        Reaction(
            "r1", "A => B", formula="A", name="r1", sboTerm="SBO:0000176"
        ).create_sbml(model)
        Event(
            "e1",
            trigger="time >= 10",
            priority="1",
            delay="2",
            name="e1",
            sboTerm="SBO:0000231",
        ).create_sbml(model)

    assert "should be set" not in caplog.text, caplog.text
    del doc


def test_no_authoring_hints_is_confined_to_its_thread(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that suppressing the hints in one thread does not silence another.

    `sbmlutils.parser` writes a parsed model inside `no_authoring_hints()`.
    While the suppression was a class attribute it was global: a model
    definition written in another thread at the same time lost its hints,
    which are the only report it gets about a missing name or sboTerm.

    One thread writes a model inside the context, the main thread writes an
    equally unnamed model while that thread is provably still inside it. The
    threads are synchronized with events rather than with sleeps, and the log
    records are told apart by the thread which emitted them.
    """
    written = threading.Event()
    release = threading.Event()
    failure: list[BaseException] = []

    def write_without_hints() -> None:
        try:
            with Sbase.no_authoring_hints():
                create_model(
                    model=Model("suppressed", compartments=[Compartment("c", 1.0)]),
                    filepath=tmp_path / "suppressed.xml",
                    validation_options=ValidationOptions(units_consistency=False),
                )
                written.set()
                assert release.wait(timeout=30.0)
        except BaseException as err:
            failure.append(err)
        finally:
            written.set()

    thread = threading.Thread(target=write_without_hints, name="suppressed")
    with caplog.at_level(logging.WARNING, logger="sbmlutils.factory"):
        thread.start()
        try:
            assert written.wait(timeout=30.0)
            create_model(
                model=Model("hinted", compartments=[Compartment("c", 1.0)]),
                filepath=tmp_path / "hinted.xml",
                validation_options=ValidationOptions(units_consistency=False),
            )
        finally:
            release.set()
            thread.join(timeout=30.0)

    assert not failure, failure
    assert not thread.is_alive()
    hints = {
        record.threadName
        for record in caplog.records
        if "'name' should be set" in record.message
    }
    assert hints == {threading.current_thread().name}, caplog.text


@pytest.mark.parametrize(
    "flag, value, attribute, getter",
    [
        ("trigger_persistent", False, "persistent", "getPersistent"),
        ("trigger_initialValue", True, "initialValue", "getInitialValue"),
    ],
)
def test_event_trigger_flag_set_after_construction(
    flag: str, value: bool, attribute: str, getter: str
) -> None:
    """Test that a trigger flag set on the event after construction is written.

    `trigger_persistent` and `trigger_initialValue` were attributes of the
    event in 0.10, which a model definition could set after construction.
    They read and set the flags of `event.trigger`; a plain attribute would be
    ignored silently, and the event would fire at a different time.
    """
    event = Event("e1", trigger="time >= 10", assignments={"p1": 1.0})
    setattr(event, flag, value)
    assert getattr(event, flag) is value
    assert getattr(event.trigger, attribute) is value

    doc, model = _event_test_model(2)
    event.create_sbml(model)
    trigger: libsbml.Trigger = model.getEvent("e1").getTrigger()
    assert getattr(trigger, getter)() is value
    del doc


def test_event_trigger_flag_set_without_a_trigger_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a trigger flag set on an event without a trigger is logged.

    There is no trigger the flag could be set on, so it is not applied, and
    the warning says so instead of letting it vanish.
    """
    event = Event("e1", trigger=None)
    with caplog.at_level("WARNING", logger="sbmlutils.factory"):
        event.trigger_persistent = False
        event.trigger_initialValue = True

    assert event.trigger is None
    assert event.trigger_persistent is None
    assert event.trigger_initialValue is None
    assert "trigger_persistent" in caplog.text
    assert "trigger_initialValue" in caplog.text


@pytest.mark.parametrize(
    "element, value, expected",
    [
        ("trigger", "time >= 20", "time >= 20"),
        ("priority", "2", "2"),
        ("delay", "3", "3"),
        ("priority", 2, "2"),
        ("delay", 3.5, "3.5"),
    ],
)
def test_event_child_assigned_after_construction(
    element: str, value: str | float, expected: str
) -> None:
    """Test that math assigned after construction is normalized and written.

    In 0.10 `event.trigger = "time >= 20"` set a formula string. Assigned
    after construction, a formula string or a number is normalized into the
    object as it is by the constructor, rather than failing when the event is
    written.
    """
    event = Event(
        "e1", trigger="time >= 10", priority="1", delay="2", assignments={"p1": 1.0}
    )
    setattr(event, element, value)
    classes: dict[str, type[factory.Sbase]] = {
        "trigger": Trigger,
        "priority": Priority,
        "delay": Delay,
    }
    assert isinstance(getattr(event, element), classes[element])

    doc, model = _event_test_model(2)
    event.create_sbml(model)
    child: Any = getattr(model.getEvent("e1"), f"get{element.title()}")()
    assert libsbml.formulaToL3String(child.getMath()) == expected
    del doc


def test_event_trigger_assigned_after_construction_keeps_its_flags() -> None:
    """Test that a trigger string assigned after construction keeps the flags.

    In 0.10 the flags were attributes of the event, which a new trigger string
    did not change, so the `Trigger` created from it takes the `persistent`
    and `initialValue` of the trigger it replaces.
    """
    event = Event(
        "e1",
        trigger="time >= 10",
        trigger_persistent=False,
        trigger_initialValue=True,
    )
    event.trigger = "time >= 20"

    assert isinstance(event.trigger, Trigger)
    assert event.trigger.math == "time >= 20"
    assert event.trigger.persistent is False
    assert event.trigger.initialValue is True


@pytest.mark.parametrize(
    "element, value, cls, math",
    [
        ("trigger", 1, Trigger, "1"),
        ("priority", 1, Priority, "1"),
        ("delay", 2.5, Delay, "2.5"),
        ("delay", np.float64(0.5), Delay, "0.5"),
    ],
)
def test_event_numbers_are_normalized(
    element: str, value: float, cls: type[factory.Sbase], math: str
) -> None:
    """Test that a number given for a trigger, priority or delay is math.

    `Delay(5)` worked, `Event(delay=5)` failed when the event was written,
    since only a string was normalized into the object.
    """
    kwargs: dict[str, Any] = {"trigger": "time >= 10", element: value}
    event = Event("e1", assignments={"p1": 1.0}, **kwargs)
    child = getattr(event, element)
    assert isinstance(child, cls)
    assert child.math == math

    doc, model = _event_test_model(2)
    event.create_sbml(model)
    sbml_child: Any = getattr(model.getEvent("e1"), f"get{element.title()}")()
    assert libsbml.formulaToL3String(sbml_child.getMath()) == math
    del doc


@pytest.mark.parametrize("value", [True, [2.0]], ids=["bool", "list"])
def test_event_child_of_another_type_raises(value: Any) -> None:
    """Test that a value which is no math is rejected when it is given.

    A bool in particular is not converted: `str(True)` is the id `True`, not
    the constant `true`.
    """
    with pytest.raises(TypeError, match="delay"):
        Event("e1", trigger="time >= 10", delay=value)

    event = Event("e1", trigger="time >= 10")
    with pytest.raises(TypeError, match="delay"):
        event.delay = value


def _l2_event_test_model() -> tuple[libsbml.SBMLDocument, libsbml.Model]:
    """Build an SBML L2V4 model with the non-constant parameter 'p1'.

    Returns:
        the document and its model; the caller holds the document for as long
        as it uses the model
    """
    doc = libsbml.SBMLDocument(2, 4)
    model: libsbml.Model = doc.createModel()
    p1: libsbml.Parameter = model.createParameter()
    p1.setId("p1")
    p1.setValue(0.0)
    p1.setConstant(False)
    return doc, model


def test_event_written_at_l2_logs_no_error(caplog: pytest.LogCaptureFixture) -> None:
    """Test that an event written at SBML L2 logs no error.

    The `initialValue` and `persistent` of a trigger only exist from SBML L3
    on; setting them on an L2 trigger fails, which was logged as four errors
    for every event, although the caller cannot change anything about it.
    """
    doc, model = _l2_event_test_model()
    with caplog.at_level("WARNING", logger="sbmlutils"):
        Event(
            "e1",
            trigger="time >= 10",
            delay="2",
            assignments={"p1": 1.0},
            name="e1",
            sboTerm="SBO:0000231",
        ).create_sbml(model)

    event: libsbml.Event = model.getEvent("e1")
    assert event.getTrigger().isSetMath()
    assert event.getDelay().isSetMath()
    assert not any(record.levelname == "ERROR" for record in caplog.records), [
        r.getMessage() for r in caplog.records if r.levelname == "ERROR"
    ]
    del doc


def test_event_priority_at_l2_is_logged_and_not_written(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a priority written at SBML L2 is logged as an error.

    A priority only exists from SBML L3 on, libsbml creates none on an L2
    event. Writing one raised an `AttributeError`; it is logged instead, and
    the rest of the event is written.
    """
    doc, model = _l2_event_test_model()
    with caplog.at_level("ERROR", logger="sbmlutils.factory"):
        Event(
            "e1", trigger="time >= 10", priority="1", assignments={"p1": 1.0}
        ).create_sbml(model)

    event: libsbml.Event = model.getEvent("e1")
    assert not event.isSetPriority()
    assert event.getNumEventAssignments() == 1
    errors = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert len(errors) == 1, errors
    assert "priority" in errors[0]
    del doc


@pytest.mark.parametrize("formula", ["", "time >="], ids=["empty", "unparsable"])
def test_formula_which_does_not_parse_logs_one_error(
    formula: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that math which does not parse is logged as a single error.

    `ast_node_from_formula` logged the error of the libsbml parser as a
    second record, which for an empty formula is empty.
    """
    doc, model = _event_test_model(2)
    with caplog.at_level("ERROR", logger="sbmlutils.factory"):
        assert factory.ast_node_from_formula(model, formula) is None

    messages = [r.getMessage() for r in caplog.records]
    assert len(messages) == 1, messages
    assert f"'{formula}'" in messages[0]
    if formula:
        assert "syntax error" in messages[0]
    del doc


def test_constraint_unparsable_math_logs_an_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that constraint math which does not parse is logged as an error.

    `Constraint` passed the result of `parseL3FormulaWithModel` to `setMath`
    without checking it, so math which did not parse became a constraint
    without math, silently, unlike every other element with math.
    """
    doc, model = _event_test_model(2)
    with caplog.at_level("ERROR", logger="sbmlutils.factory"):
        Constraint("c1", math="p1 >").create_sbml(model)

    errors = [r.getMessage() for r in caplog.records if r.levelname == "ERROR"]
    assert any("'p1 >'" in message for message in errors), errors
    assert not model.getConstraint(0).isSetMath()
    del doc


@pytest.mark.parametrize(
    "create, formula",
    [
        (
            lambda: Model(
                "kinetic_law",
                compartments=[Compartment("c", 1.0)],
                species=[
                    Species("A", compartment="c", initialAmount=1.0),
                    Species("B", compartment="c", initialAmount=0.0),
                ],
                reactions=[Reaction("r1", "A => B", formula="A >")],
            ),
            "A >",
        ),
        (
            lambda: Model(
                "event_assignment",
                parameters=[Parameter("p1", value=0.0, constant=False)],
                events=[Event("e1", trigger="time >= 10", assignments={"p1": "p1 >"})],
            ),
            "p1 >",
        ),
        (
            lambda: Model(
                "uncertainty",
                packages=[Package.DISTRIB_V1],
                parameters=[
                    Parameter(
                        "p1",
                        value=1.0,
                        uncertainties=[Uncertainty(formula="normal(")],
                    )
                ],
            ),
            "normal(",
        ),
    ],
    ids=["KineticLaw", "EventAssignment", "Uncertainty"],
)
def test_unparsable_math_is_logged_at_every_formula_call_site(
    create: Callable[[], Model],
    formula: str,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that every formula which does not parse is reported as an error.

    `libsbml.parseL3FormulaWithModel` returns `None` for math which does not
    parse, and `libsbml.SBase.setMath(None)` leaves the element without math
    without failing. Each of the places which parses math on its own rather
    than through `ast_node_from_formula` must therefore check the result, so
    that math which does not parse is never dropped silently.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        create_model(
            model=create(),
            filepath=tmp_path / "model.xml",
            validation_options=ValidationOptions(units_consistency=False),
        )

    errors = [
        record.getMessage()
        for record in caplog.records
        if record.levelname == "ERROR" and record.name == "sbmlutils.factory"
    ]
    assert any(formula in message for message in errors), errors


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


# ---------------------------------------------------------------------------
# the gene products of a gene product association
# ---------------------------------------------------------------------------
def _gpa_model(association: str, gene_ids: tuple[str, ...]) -> Model:
    """Get a model whose single reaction has a gene product association.

    Args:
        association: the association, as an infix string of gene product ids
        gene_ids: the id of every gene product the model declares; each one
            gets a label of its own which is no id of the model, so that a
            check against the labels would find nothing

    Returns:
        the model definition
    """
    return Model(
        sid="gene_product_association",
        packages=[Package.FBC_V2],
        strict=False,
        compartments=[Compartment(sid="c", value=1.0)],
        species=[Species(sid="S1", compartment="c", initialAmount=1.0)],
        gene_products=[
            GeneProduct(sid=sid, label=f"label_of_{sid}") for sid in gene_ids
        ],
        reactions=[
            Reaction(sid="R1", equation="S1 ->", geneProductAssociation=association)
        ],
    )


def _missing_gene_products(
    association: str,
    gene_ids: tuple[str, ...],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> list[str]:
    """Create a model with an association and collect the gene products it misses.

    Args:
        association: the association, as an infix string of gene product ids
        gene_ids: the id of every gene product the model declares
        tmp_path: the directory the SBML file is written to
        caplog: pytest's log capture

    Returns:
        the message of every `GeneProduct missing in model` error, in order
    """
    caplog.clear()
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        create_model(
            model=_gpa_model(association, gene_ids),
            filepath=tmp_path / "gene_product_association.xml",
            validate=False,
        )
    return [
        record.getMessage()
        for record in caplog.records
        if "GeneProduct missing in model" in record.getMessage()
    ]


@pytest.mark.parametrize(
    "association, gene_ids",
    [
        # an id which carries `OR`, `and` or `or` inside it
        ("ORF1 and b0001", ("ORF1", "b0001")),
        ("brandy and sensor", ("brandy", "sensor")),
        ("ORF1 AND b0001", ("ORF1", "b0001")),
        ("brandy OR sensor", ("brandy", "sensor")),
        # the operators in both spellings, and groups
        ("(b0001 and b0002) or b0003", ("b0001", "b0002", "b0003")),
        ("(b0001 AND b0002) OR b0003", ("b0001", "b0002", "b0003")),
        # a single gene product, which is no operator at all
        ("ORF1", ("ORF1",)),
        # nested parentheses without a space around them
        ("(b0001 and(b0002 or b0003))", ("b0001", "b0002", "b0003")),
    ],
)
def test_gene_product_association_reports_no_gene_product_it_has(
    association: str,
    gene_ids: tuple[str, ...],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an association of gene products of the model reports none as missing.

    The check which warns about a gene product the model does not declare used
    to strip `(`, `)`, `and`, `AND`, `or` and `OR` out of the association with
    a chain of `str.replace`, which cuts those letters out of the middle of an
    id as well: `ORF1` became `F1` and `brandy` became `br y`, and every one of
    them was reported as a gene product missing from the model although it is
    right there.
    """
    assert _missing_gene_products(association, gene_ids, tmp_path, caplog) == []


def test_gene_product_association_reports_a_gene_product_which_is_missing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a gene product the model does not declare is still reported.

    The check exists to catch exactly this, so the tokenizer must not make it
    blind: only the operators are dropped, every other token is a gene product
    id and is looked up in the model.
    """
    messages = _missing_gene_products(
        "(ORF1 and b0001) or b9999", ("ORF1", "b0001"), tmp_path, caplog
    )

    assert len(messages) == 1, messages
    assert "b9999" in messages[0]


def test_gene_product_association_is_checked_against_the_ids_not_the_labels(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that the check resolves a token as a gene product id.

    `Reaction.create_sbml` writes the association with
    `setAssociation(infix, usingId=True, addMissingGP=False)`, so the string
    names the gene products by their id and not by their label; the check is
    `FbcModelPlugin.getGeneProduct`, which is the lookup by id
    (`getGeneProductByLabel` is the one by label).
    """
    messages = _missing_gene_products("label_of_ORF1", ("ORF1",), tmp_path, caplog)

    assert len(messages) == 1, messages
    assert "label_of_ORF1" in messages[0]


def _gpa_document(gene_ids: tuple[str, ...]) -> libsbml.SBMLDocument:
    """Build an fbc document holding the given gene products.

    Args:
        gene_ids: the id of every gene product the model declares

    Returns:
        the document, which the caller has to hold for as long as it uses any
        object of it
    """
    doc = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, 2, "fbc", 2))
    doc.setPackageRequired("fbc", False)
    model: libsbml.Model = doc.createModel()
    model.setId("gene_product_association")
    plugin: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    plugin.setStrict(False)
    for sid in gene_ids:
        gene_product: libsbml.GeneProduct = plugin.createGeneProduct()
        gene_product.setId(sid)
        gene_product.setLabel(f"label_of_{sid}")
    return doc


@pytest.mark.parametrize(
    "operator, is_operator",
    [
        ("and", True),
        ("AND", True),
        ("And", False),
        ("&", False),
        ("&&", False),
        ("or", True),
        ("OR", True),
        ("Or", False),
        ("|", False),
        ("||", False),
    ],
)
def test_gene_product_association_drops_the_operators_libsbml_parses(
    operator: str,
    is_operator: bool,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that the check drops exactly the operator spellings libsbml accepts.

    The association is written with libsbml's own infix parser, which accepts
    `and`, `AND`, `or` and `OR` and no other spelling of the two operators,
    neither `And` nor `&`, `&&`, `|` or `||`. The check drops the same four
    and reads every other token as a gene product id, so a spelling libsbml
    would refuse is reported as the gene product it parses as instead of
    passing silently.

    What libsbml accepts is measured here rather than assumed: the expectation
    of the parametrization is asserted against the parser first.
    """
    doc = _gpa_document(("b0001", "b0002"))
    plugin: libsbml.FbcModelPlugin = doc.getModel().getPlugin("fbc")
    infix = f"b0001 {operator} b0002"
    parsed = libsbml.FbcAssociation.parseFbcInfixAssociation(infix, plugin, True, False)
    assert (parsed is not None) is is_operator, infix

    messages = _missing_gene_products(infix, ("b0001", "b0002"), tmp_path, caplog)

    if is_operator:
        assert messages == []
    else:
        assert len(messages) == 1 and operator in messages[0], messages


def test_gene_product_association_without_a_space_before_a_group_is_refused(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that libsbml, not the check, is what refuses `and(` without a space.

    The check splits the association on parentheses, so `b0001 and(b0002)`
    names no gene product the model does not have and it says nothing.
    libsbml's own infix parser is stricter and wants whitespace behind an
    operator, so it refuses to parse that association at all; the user hears
    about it through the error `check()` logs for the `setAssociation` which
    would have written it. The check is a hint about missing gene products,
    never the syntax check of the association.
    """
    caplog.clear()
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(
            model=_gpa_model("b0001 and(b0002)", ("b0001", "b0002")),
            filepath=tmp_path / "gene_product_association.xml",
            validate=False,
        )

    messages = [record.getMessage() for record in caplog.records]
    assert [m for m in messages if "GeneProduct missing in model" in m] == []
    assert [m for m in messages if "set gpa" in m] != [], messages


def _fbc_reaction_test_model() -> tuple[libsbml.SBMLDocument, libsbml.Model]:
    """Build a minimal L3V2 fbc version 3 model with species 'A', 'B' and 'M'.

    fbc version 3 is the version which defines the key-value pair, so it is
    the version a species reference can carry one in.

    Returns:
        the document and its model; the caller has to hold the document for as
        long as it uses any object of it
    """
    doc = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, 2, "fbc", 3))
    doc.setPackageRequired("fbc", False)
    model: libsbml.Model = doc.createModel()
    model.setId("reaction_key_value_pairs")
    plugin: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    plugin.setStrict(False)
    model.createCompartment().setId("c")
    for sid in ("A", "B", "M"):
        species: libsbml.Species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")
    return doc, model


def test_reaction_speciesref_keeps_key_value_pairs() -> None:
    """Test that the key-value pairs of a reactant, product and modifier are written.

    `EquationPart.keyValuePairs` was declared and never read:
    `set_speciesref_fields` wrote the species, id, stoichiometry, metaId,
    sboTerm, name, notes and annotations of a part and dropped its key-value
    pairs, for all three roles alike. A `ModifierSpeciesReference` is an
    `SBase` like a `SpeciesReference` and carries them just as well.
    """
    _doc, model = _fbc_reaction_test_model()
    equation = ReactionEquation(
        reactants=[
            EquationPart(
                species="A",
                keyValuePairs=[
                    KeyValuePair(key="kr", value="1", uri="https://example.org/kr")
                ],
            )
        ],
        products=[
            EquationPart(
                species="B",
                keyValuePairs=[KeyValuePair(key="kp", value="2", uri=None)],
            )
        ],
        modifiers=[
            EquationPart(
                species="M",
                keyValuePairs=[KeyValuePair(key="km", value="3", uri=None)],
            )
        ],
    )
    Reaction("r1", equation).create_sbml(model)

    reaction: libsbml.Reaction = model.getReaction("r1")
    written: dict[str, tuple[str, str | None]] = {}
    for sref in (
        reaction.getReactant(0),
        reaction.getProduct(0),
        reaction.getModifier(0),
    ):
        plugin: libsbml.FbcSBasePlugin = sref.getPlugin("fbc")
        for kvp in plugin.getListOfKeyValuePairs():
            written[kvp.getKey()] = (
                kvp.getValue(),
                kvp.getUri() if kvp.isSetUri() else None,
            )

    assert written == {
        "kr": ("1", "https://example.org/kr"),
        "kp": ("2", None),
        "km": ("3", None),
    }


# ---------------------------------------------------------------------------
# the fbc charge, which libsbml keeps apart by fbc version
# ---------------------------------------------------------------------------
def _charge_document(fbc_version: int, charge: float | None) -> libsbml.SBMLDocument:
    """Create a species with a charge in a document of the given fbc version.

    Args:
        fbc_version: the fbc package version of the document, 2 or 3
        charge: the charge of the species, `None` for a species without one

    Returns:
        the document, which the caller has to hold for as long as it uses any
        object of it
    """
    doc = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, 2, "fbc", fbc_version))
    doc.setPackageRequired("fbc", False)
    model: libsbml.Model = doc.createModel()
    model.setId("charge")
    plugin: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    plugin.setStrict(False)
    compartment: libsbml.Compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setConstant(True)
    Species(sid="S1", compartment="c", initialAmount=1.0, charge=charge).create_sbml(
        model
    )
    return doc


def _written_charge(doc: libsbml.SBMLDocument) -> str | None:
    """Get the `fbc:charge` libsbml writes for the species `S1` of a document.

    The charge is read out of the SBML rather than through a getter, since the
    getter of the version the document is not at returns 0 for a charge which
    is set, which is the very confusion this is about.

    Args:
        doc: the document, which the caller holds

    Returns:
        the value of the `fbc:charge` attribute, `None` if the species has none
    """
    match = re.search(
        r'<species [^>]*fbc:charge="([^"]*)"', libsbml.writeSBMLToString(doc)
    )
    return match.group(1) if match is not None else None


@pytest.mark.parametrize(
    "fbc_version, charge, written",
    [
        # fbc version 2 writes an integer charge; an integral float is one
        (2, -2.0, "-2"),
        (2, 1, "1"),
        (2, 0, "0"),
        (2, 0.0, "0"),
        (2, None, None),
        # fbc version 3 writes a double charge, integral or not
        (3, 1, "1"),
        (3, -2.0, "-2"),
        (3, -2.5, "-2.5"),
        (3, 0, "0"),
        (3, None, None),
    ],
)
def test_species_charge_is_written_for_the_fbc_version_of_the_document(
    fbc_version: int, charge: float | None, written: str | None
) -> None:
    """Test that the charge given is the charge written, in both fbc versions.

    libsbml keeps the integer charge of fbc version 2 and the double charge of
    fbc version 3 apart and writes only the one of the version of the
    document, and `FbcSpeciesPlugin.setCharge` picks which of the two it sets
    from the python type of its argument. `Species._set_fields` passed the
    `charge` field through as it was, so a `float` in an fbc version 2 model
    and an `int` in an fbc version 3 model each set the charge of the other
    version: `fbc:charge` came out as `0` while the charge was reported as
    set. A charge of `0` and a species without a charge stay apart.
    """
    doc = _charge_document(fbc_version, charge)

    assert _written_charge(doc) == written


def test_species_charge_which_fbc_v2_cannot_write_is_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a non-integral charge in an fbc version 2 model is reported, not rounded.

    `fbc:charge` is an integer in fbc version 2, so a charge of `-2.5` cannot
    be written into such a document at all. Rounding it would write a charge
    the model never stated, so it is left unset and the species and the charge
    are named in an error.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.factory"):
        doc = _charge_document(2, -2.5)

    assert _written_charge(doc) is None
    errors = [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.ERROR
    ]
    assert len(errors) == 1, errors
    assert "S1" in errors[0] and "-2.5" in errors[0]


#: the prefix of every package namespace and `required` attribute of an
#: `<sbml>` start tag, in the order they are written
_NAMESPACE_PREFIX = re.compile(r'xmlns:([a-z]+)="http://www\.sbml\.org/sbml/level3')
_REQUIRED_PREFIX = re.compile(r"([a-z]+):required=")

#: a model which declares every package sbmlutils supports; written in a
#: process of its own by the test below
_PACKAGE_MODEL = """
from sbmlutils.factory import Model, Package, Parameter

model = Model(
    "packages",
    packages=[Package.COMP_V1, Package.DISTRIB_V1, Package.FBC_V3],
    parameters=[Parameter("p1", value=1.0)],
)
for line in model.get_sbml().splitlines():
    if line.startswith("<sbml"):
        print(line)
        break
"""


def _start_tag(model: Model) -> str:
    """Get the `<sbml>` start tag of the SBML of a model.

    Args:
        model: the model to write

    Returns:
        the line of the SBML which starts the `sbml` element
    """
    for line in model.get_sbml().splitlines():
        if line.startswith("<sbml"):
            return line
    raise AssertionError(f"No '<sbml>' start tag in the SBML of '{model.sid}'.")


@pytest.mark.parametrize(
    "packages",
    [
        [Package.COMP_V1, Package.DISTRIB_V1, Package.FBC_V3],
        [Package.FBC_V3, Package.DISTRIB_V1, Package.COMP_V1],
        [Package.DISTRIB_V1, Package.FBC_V3, Package.COMP_V1],
    ],
)
def test_package_namespaces_are_written_in_the_order_of_the_enum(
    packages: list[Package],
) -> None:
    """Test that the packages are declared in the definition order of `Package`.

    The order the packages are given in is not the order they are declared in:
    `Model.check_packages` normalizes them and the declaration follows the
    definition order of `Package`, which is `comp`, `distrib`, `fbc`.
    """
    tag = _start_tag(Model("packages", packages=packages))

    assert _NAMESPACE_PREFIX.findall(tag) == ["comp", "distrib", "fbc"]
    assert _REQUIRED_PREFIX.findall(tag) == ["comp", "distrib", "fbc"]


def test_package_namespaces_do_not_depend_on_the_hash_seed() -> None:
    """Test that two processes write the same `<sbml>` start tag.

    The packages of a model were collected in a `set`, which the declarations
    were written from in iteration order, so the same model definition wrote
    a different `<sbml>` element in every process: the order of a set of
    `Package` members depends on the hash seed of the process. Two seeds are
    enough to show it, they produced two different tags.
    """
    tags = {}
    for seed in ("0", "1"):
        process = subprocess.run(
            [sys.executable, "-c", _PACKAGE_MODEL],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": seed},
        )
        tags[seed] = process.stdout.strip()

    # a child which printed nothing would make two empty strings equal
    for seed, tag in tags.items():
        assert tag.startswith("<sbml "), (seed, process.stderr)
        assert _NAMESPACE_PREFIX.findall(tag) == ["comp", "distrib", "fbc"], tag
    assert tags["0"] == tags["1"], tags


@pytest.mark.parametrize("field", ["keyValuePairs"])
def test_document_does_not_offer_key_value_pairs(field: str) -> None:
    """Test that a document refuses the key-value pairs it cannot write.

    fbc version 3 gives a `<fbc:keyValuePair>` to every `SBase`, but libsbml
    5.21.2 attaches an `FbcSBMLDocumentPlugin` to the `<sbml>` element, which
    has no key-value-pair accessor at all: the pairs of a document could not
    be written (`create_sbml` failed with an `AttributeError` on the plugin)
    and a `<listOfKeyValuePairs>` written into the XML of an `<sbml>` element
    by hand is read without an error and is invisible afterwards. The keyword
    is passed through a mapping, the way the same check is made in
    `tests/test_distrib.py`: spelling it out is a type error, which is the
    point of the test.
    """
    model = Model(sid="document_key_value_pairs", name="a model")
    kwargs: dict[str, Any] = {field: None}
    with pytest.raises(TypeError, match=field):
        Document(model=model, **kwargs)


def _minimal_content() -> dict[str, Any]:
    """Get the content of a model which writes at every SBML level and version.

    Returns:
        the keyword arguments of a `Model`
    """
    return {
        "compartments": [Compartment("c", 1.0, name="compartment")],
        "species": [
            Species("S1", compartment="c", initialAmount=1.0, name="S1"),
        ],
    }


#: one case per kind of libsbml failure the survey of the unwrapped setters
#: found, as `(build, level, version, fragments of the one error)`. Every case
#: is a **value** which `factory.py` passes on to libsbml unchanged and which
#: libsbml refuses with a status code, so that the attribute was dropped in
#: silence before it was wrapped. An attribute the document has no place for
#: at all is the other half, see `_ATTRIBUTES_WITHOUT_A_PLACE`.
_SWALLOWED_ATTRIBUTES: list[Any] = [
    pytest.param(
        lambda: Model(
            sid="invalid_sid",
            name="a model",
            compartments=[Compartment("c", 1.0, name="compartment")],
            species=[
                Species("S1", compartment="not an sid", initialAmount=1.0, name="S1")
            ],
        ),
        3,
        1,
        ["compartment", "not an sid", "Species(S1"],
        id="invalid-sid",
    ),
    pytest.param(
        lambda: Model(
            sid="invalid_sbo_term",
            name="a model",
            parameters=[Parameter("p1", 1.0, name="p1", sboTerm="not an sbo term")],
            **_minimal_content(),
        ),
        3,
        1,
        ["sboTerm", "not an sbo term", "Parameter(p1"],
        id="invalid-sbo-term",
    ),
    pytest.param(
        lambda: Model(
            sid="invalid_metaid",
            name="a model",
            parameters=[Parameter("p1", 1.0, name="p1", metaId="meta id")],
            **_minimal_content(),
        ),
        3,
        1,
        ["metaId", "meta id", "Parameter(p1"],
        id="invalid-metaid",
    ),
    pytest.param(
        lambda: Model(
            sid="invalid_unit_id",
            name="a model",
            model_units=ModelUnits(
                time="not an sid",
                extent=Units.mole,
                substance=Units.mole,
                volume=Units.litre,
            ),
            **_minimal_content(),
        ),
        3,
        1,
        ["time unit", "not an sid", "Model(invalid_unit_id)"],
        id="invalid-unit-id",
    ),
    pytest.param(
        lambda: Model(
            sid="value_outside_an_enumeration",
            name="a model",
            packages=[Package.FBC_V3],
            objectives=[
                Objective(
                    sid="obj1",
                    name="objective",
                    objectiveType="maximize",
                    fluxObjectives=[
                        FluxObjective(
                            reaction="R1",
                            coefficient=1.0,
                            name="flux objective",
                            variableType="invalid",
                        )
                    ],
                )
            ],
            reactions=[Reaction("R1", "S1 ->", name="reaction")],
            **_minimal_content(),
        ),
        3,
        1,
        ["variableType", "FluxObjective("],
        id="value-outside-an-enumeration",
    ),
    pytest.param(
        lambda: Model(
            sid="invalid_chemical_formula",
            name="a model",
            packages=[Package.FBC_V3],
            compartments=[Compartment("c", 1.0, name="compartment")],
            species=[
                Species(
                    "S1",
                    compartment="c",
                    initialAmount=1.0,
                    name="S1",
                    chemicalFormula="not a formula",
                )
            ],
        ),
        3,
        1,
        ["chemicalFormula", "not a formula", "Species(S1"],
        id="invalid-chemical-formula",
    ),
    pytest.param(
        lambda: Model(
            sid="reference_the_element_cannot_carry",
            name="a model",
            packages=[Package.COMP_V1],
            ports=[Port(sid="p1_port", name="a port", portRef="another_port")],
            parameters=[Parameter("p1", 1.0, name="p1")],
            **_minimal_content(),
        ),
        3,
        1,
        ["portRef", "another_port", "Port(p1_port"],
        id="reference-the-element-cannot-carry",
    ),
    pytest.param(
        lambda: Model(
            sid="package_of_a_later_level",
            name="a model",
            packages=[Package.COMP_V1],
            **_minimal_content(),
        ),
        2,
        4,
        ["comp-v1", "SBML L2V4"],
        id="package-of-a-later-level",
    ),
]


@pytest.mark.parametrize("build, level, version, fragments", _SWALLOWED_ATTRIBUTES)
def test_attribute_libsbml_refuses_is_reported(
    build: Callable[[], Model],
    level: int,
    version: int,
    fragments: list[str],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an attribute libsbml refuses to write is reported once.

    A libsbml setter answers with a status code instead of raising, so an
    attribute it refuses used to be dropped in silence: the model definition
    asked for it, the written document did not carry it and validated. Every
    case here is one kind of refusal the survey of `factory.py` found: an
    invalid SId, an invalid SBO term, an invalid metaid, an invalid unit id,
    a value outside an enumeration, an invalid chemical formula, a reference
    the element cannot carry, and a package the SBML level cannot declare.
    An attribute the document has no place for at all is not an error per
    element, see `test_attribute_the_document_has_no_place_for_is_reported_once`.

    The document is written either way, which the file on disk shows.
    """
    model = build()
    sbml_path = tmp_path / f"{model.sid}.xml"
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=sbml_path,
            sbml_level=level,
            sbml_version=version,
            validate=False,
        )

    # `check` logs the status code as a record of its own, which belongs to
    # the report before it rather than being a report of its own
    errors = [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.ERROR
        and not record.getMessage().startswith("LibSBML returned error code")
    ]
    assert len(errors) == 1, errors
    for fragment in fragments:
        assert fragment in errors[0], errors[0]

    # the rest of the document is written all the same
    assert sbml_path.exists()
    doc: libsbml.SBMLDocument = read_sbml(source=sbml_path, validate=False)
    sbml_model: libsbml.Model = doc.getModel()
    assert sbml_model.getId() == model.sid
    assert sbml_model.getNumCompartments() == 1


#: one case per kind of attribute the document has no place for, as
#: `(build, level, version, fragments of the one warning)`. This is the other
#: half of `_SWALLOWED_ATTRIBUTES`: the value is fine and the document has
#: nowhere to put it, which one decision fixes for every element at once.
_ATTRIBUTES_WITHOUT_A_PLACE: list[Any] = [
    pytest.param(
        lambda: Model(
            sid="attribute_of_a_later_level",
            name="a model",
            parameters=[Parameter("p1", 1.0, name="p1")],
            compartments=[Compartment("c", 1.0, name="compartment")],
            species=[
                Species(
                    "S1",
                    compartment="c",
                    initialAmount=1.0,
                    name="S1",
                    conversionFactor="p1",
                )
            ],
        ),
        2,
        4,
        [
            "'conversionFactor'",
            "1 <species>",
            "Species(S1",
            "SBML L2V4 has no such attribute",
            "Write SBML Level 3 Version 2",
        ],
        id="attribute-of-a-later-level",
    ),
    pytest.param(
        lambda: Model(
            sid="attribute_of_a_later_package_version",
            name="a model",
            packages=[Package.FBC_V2],
            objectives=[
                Objective(
                    sid="obj1",
                    name="objective",
                    objectiveType="maximize",
                    fluxObjectives={"R1": 1.0},
                )
            ],
            reactions=[Reaction("R1", "S1 ->", name="reaction")],
            **_minimal_content(),
        ),
        3,
        1,
        [
            "'variableType'",
            "1 <fluxObjective>",
            "fbc version 2",
            "has no such attribute",
            "Declare fbc version 3",
        ],
        id="attribute-of-a-later-package-version",
    ),
]


@pytest.mark.parametrize(
    "build, level, version, fragments", _ATTRIBUTES_WITHOUT_A_PLACE
)
def test_attribute_the_document_has_no_place_for_is_reported_once(
    build: Callable[[], Model],
    level: int,
    version: int,
    fragments: list[str],
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an attribute the document cannot carry is one warning.

    The value is fine; the SBML level and version of the document, or the
    version of the package, has no such attribute, which the caller fixes
    with one decision for every element at once. Such a loss is collected for
    the document and reported once per element kind and attribute, not as an
    error per element.
    """
    model = build()
    sbml_path = tmp_path / f"{model.sid}.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=sbml_path,
            sbml_level=level,
            sbml_version=version,
            validate=False,
        )

    warnings = [m for m in _records(caplog, logging.WARNING) if "not written" in m]
    assert len(warnings) == 1, warnings
    for fragment in fragments:
        assert fragment in warnings[0], warnings[0]
    assert _records(caplog, logging.ERROR) == []
    assert sbml_path.exists()


def test_create_model_writes_into_a_directory_which_does_not_exist(
    tmp_path: Path,
) -> None:
    """Test that `create_model` writes the file a caller asks for.

    `libsbml.SBMLWriter.writeSBMLToFile` answers `False` for a path whose
    parent directory does not exist and writes nothing, which the writer
    discarded: `create_model` then validated the *path*, read an empty
    document from the file which was never written, printed `valid: TRUE`
    and returned a `FactoryResult` whose `sbml_path` does not exist.
    """
    sbml_path = tmp_path / "does" / "not" / "exist" / "model.xml"
    model = Model(
        sid="missing_directory",
        name="a model",
        compartments=[Compartment("c", 1.0, name="compartment")],
        species=[Species("S1", compartment="c", initialAmount=1.0, name="S1")],
    )

    result = create_model(
        model=model,
        filepath=sbml_path,
        validation_options=ValidationOptions(units_consistency=False),
    )

    assert result.sbml_path.exists()
    doc: libsbml.SBMLDocument = read_sbml(source=sbml_path, validate=False)
    assert doc.getModel().getId() == "missing_directory"


def test_create_model_raises_for_a_file_it_cannot_write(tmp_path: Path) -> None:
    """Test that a write which cannot be repaired stops `create_model`.

    A caller who asks for a file and gets none must not be told that the
    model is valid. This is about the file, not about the validation
    results: a document which does not validate is still written, and
    `create_model` still returns.
    """
    blocking_file = tmp_path / "a_file"
    blocking_file.write_text("not a directory", encoding="utf-8")
    sbml_path = blocking_file / "model.xml"
    model = Model(sid="unwritable", name="a model")

    with pytest.raises(OSError, match=re.escape(str(sbml_path))):
        create_model(model=model, filepath=sbml_path, validate=False)


def _named_rules_model() -> Model:
    """Get a model whose three assignment rules carry a name.

    A `<rule>` has no `name` attribute below SBML L3V2, so the names of this
    model are written at L3V2 and lost at L3V1.

    Returns:
        the model
    """
    return Model(
        sid="named_rules",
        name="a model whose rules carry a name",
        compartments=[Compartment("c", 1.0, name="compartment")],
        parameters=[
            Parameter("k1", 1.0, name="k1", constant=False),
            Parameter("k2", 1.0, name="k2", constant=False),
            Parameter("k3", 1.0, name="k3", constant=False),
        ],
        rules=[
            AssignmentRule("k1", "2.0", name="the first rule"),
            AssignmentRule("k2", "3.0", name="the second rule"),
            AssignmentRule("k3", "4.0", name="the third rule"),
        ],
    )


def _records(caplog: pytest.LogCaptureFixture, level: int) -> list[str]:
    """Get the messages logged at exactly the given level.

    Args:
        caplog: the pytest log capture
        level: the level to filter on

    Returns:
        the formatted messages
    """
    return [r.getMessage() for r in caplog.records if r.levelno == level]


def test_attribute_of_a_later_level_is_reported_once_per_document(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that one decision is reported once, not once per element.

    A `<rule>` has no `name` below SBML L3V2, which `create_model` writes by
    default, so a model whose rules carry a name loses every one of them.
    Reporting each on its own buried the one decision which fixes all of them
    (write L3V2) under one error per rule; `examples/icg/model_body.py` alone
    produced 57 of them. The losses are collected for the document and
    reported once per element kind and attribute.
    """
    model = _named_rules_model()
    with caplog.at_level(logging.DEBUG, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=tmp_path / "model.xml",
            sbml_level=3,
            sbml_version=1,
            validate=False,
        )

    warnings = [m for m in _records(caplog, logging.WARNING) if "not written" in m]
    assert len(warnings) == 1, warnings
    assert "assignmentRule" in warnings[0]
    assert "'name'" in warnings[0]
    assert "3 " in warnings[0]
    assert "SBML L3V1" in warnings[0]
    assert "Level 3 Version 2" in warnings[0]
    assert _records(caplog, logging.ERROR) == []
    # the detail of every single loss is available at debug
    assert (
        len([m for m in _records(caplog, logging.DEBUG) if "the first rule" in m]) == 1
    )


def test_the_same_model_written_at_l3v2_keeps_the_names(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the positive control: at SBML L3V2 a rule carries its name."""
    model = _named_rules_model()
    sbml_path = tmp_path / "model.xml"
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=sbml_path,
            sbml_level=3,
            sbml_version=2,
            validate=False,
        )

    assert [m for m in _records(caplog, logging.WARNING) if "not written" in m] == []
    assert _records(caplog, logging.ERROR) == []
    assert "the first rule" in sbml_path.read_text(encoding="utf-8")


def test_attribute_of_a_later_level_is_reported_for_a_parameter(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the same report for an SBML Level 1 document.

    A `<parameter>` of an SBML L1 document has no `constant` attribute, so a
    `constant=False` parameter silently becomes a constant one.
    """
    model = Model(
        sid="l1_parameters",
        name="a model with parameters which are not constant",
        compartments=[Compartment("c", 1.0, name="compartment")],
        parameters=[
            Parameter("k1", 1.0, name="k1", constant=False),
            Parameter("k2", 1.0, name="k2", constant=False),
        ],
    )
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=tmp_path / "model.xml",
            sbml_level=1,
            sbml_version=2,
            validate=False,
        )

    constant = [
        m
        for m in _records(caplog, logging.WARNING)
        if "'constant'" in m and "<parameter>" in m
    ]
    assert len(constant) == 1, constant
    assert "2 <parameter> element(s)" in constant[0]
    assert "SBML L1V2" in constant[0]


def test_two_documents_report_only_their_own_attribute_losses(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that the collection of one document does not reach the next.

    The collection is held in a `ContextVar` which is reset when the scope
    of the document ends, so a second `create_model` starts empty.
    """
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        create_model(
            model=_named_rules_model(),
            filepath=tmp_path / "first.xml",
            sbml_level=3,
            sbml_version=1,
            validate=False,
        )
        first = [m for m in _records(caplog, logging.WARNING) if "not written" in m]
        caplog.clear()
        create_model(
            model=_named_rules_model(),
            filepath=tmp_path / "second.xml",
            sbml_level=3,
            sbml_version=1,
            validate=False,
        )
        second = [m for m in _records(caplog, logging.WARNING) if "not written" in m]

    assert len(first) == 1, first
    assert second == first


#: a model whose only package content is one construct, without `packages=`,
#: as `(build, namespace fragment, content fragment)`
_PACKAGE_FROM_CONTENT: list[Any] = [
    pytest.param(
        lambda: Model(
            sid="only_a_gene_product",
            name="a model with a gene product",
            gene_products=[GeneProduct(sid="g1", label="G1", name="gene")],
            **_minimal_content(),
        ),
        "fbc/version3",
        "<fbc:geneProduct",
        id="gene-product",
    ),
    pytest.param(
        lambda: Model(
            sid="only_an_objective",
            name="a model with an objective",
            objectives=[
                Objective(
                    sid="obj1",
                    name="objective",
                    objectiveType="maximize",
                    fluxObjectives={"R1": 1.0},
                )
            ],
            reactions=[Reaction("R1", "S1 ->", name="reaction")],
            **_minimal_content(),
        ),
        "fbc/version3",
        "<fbc:objective",
        id="objective",
    ),
    pytest.param(
        lambda: Model(
            sid="only_key_value_pairs",
            name="a model with key-value pairs",
            parameters=[
                Parameter(
                    "k",
                    1.0,
                    name="k",
                    keyValuePairs=[
                        KeyValuePair(key="kind", value="test", uri="https://x.org")
                    ],
                )
            ],
            **_minimal_content(),
        ),
        "fbc/version3",
        "<keyValuePair",
        id="key-value-pairs",
    ),
    pytest.param(
        lambda: Model(
            sid="only_an_uncertainty",
            name="a model with an uncertainty",
            parameters=[
                Parameter(
                    "k",
                    1.0,
                    name="k",
                    uncertainties=[
                        Uncertainty(
                            sid="unc1",
                            name="uncertainty",
                            uncertParameters=[
                                UncertParameter(
                                    type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=1.0
                                )
                            ],
                        )
                    ],
                )
            ],
            **_minimal_content(),
        ),
        "distrib/version1",
        "<distrib:uncertainty",
        id="uncertainty",
    ),
]


@pytest.mark.parametrize("build, namespace, content", _PACKAGE_FROM_CONTENT)
def test_model_declares_the_package_its_content_needs(
    build: Callable[[], Model],
    namespace: str,
    content: str,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that the main model declares the package its content engages.

    `Model._required_packages` reads off which packages the content of a
    model needs and was only asked of the model definitions of a document,
    never of the model itself. A top level model whose only fbc content was a
    gene product, an objective or a key-value pair therefore declared no fbc,
    and writing it reached a plugin which does not exist: the key-value pair
    raised `AttributeError`, the gene product and the objective wrote
    nothing.
    """
    model = build()
    sbml_path = tmp_path / f"{model.sid}.xml"
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=sbml_path,
            validation_options=ValidationOptions(units_consistency=False),
        )

    sbml = sbml_path.read_text(encoding="utf-8")
    assert namespace in sbml, sbml
    assert content in sbml, sbml
    assert _records(caplog, logging.ERROR) == []


def test_the_declared_fbc_version_wins_over_the_content(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that an explicit fbc version is not raised by the content.

    A key-value pair needs fbc version 3, but a model which asks for fbc
    version 2 gets fbc version 2: the caller stated the version of the
    document. The pairs which cannot be written there are reported, see
    `KeyValuePair.create_pairs`.
    """
    model = Model(
        sid="explicit_fbc_v2",
        name="a model which asks for fbc version 2",
        packages=[Package.FBC_V2],
        parameters=[
            Parameter(
                "k",
                1.0,
                name="k",
                keyValuePairs=[
                    KeyValuePair(key="kind", value="test", uri="https://x.org")
                ],
            )
        ],
        **_minimal_content(),
    )
    sbml_path = tmp_path / "model.xml"
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(model=model, filepath=sbml_path, validate=False)

    sbml = sbml_path.read_text(encoding="utf-8")
    assert "fbc/version2" in sbml
    assert "fbc/version3" not in sbml
    assert "keyValuePair" not in sbml
    errors = _records(caplog, logging.ERROR)
    assert len(errors) == 1, errors
    assert "fbc version 3, the document is fbc version 2" in errors[0]


@pytest.mark.parametrize("sbo_term", ["SBO:0000011", "SBO_0000011"])
def test_sbo_term_of_a_species_reference_is_normalized(
    sbo_term: str, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a species reference takes an SBO term in either spelling.

    `Sbase._set_fields` turns the `SBO_0000011` of a model definition into
    the `SBO:0000011` an SBML document is written with, and an `EquationPart`
    handed its `sboTerm` over as it was, so the same string was accepted on a
    species and refused by libsbml on a reactant.
    """
    model = Model(
        sid="species_reference_sbo_term",
        name="a model whose reactant states an sboTerm",
        compartments=[Compartment("c", 1.0, name="compartment")],
        species=[
            Species(
                "S1", compartment="c", initialAmount=1.0, name="S1", sboTerm=sbo_term
            ),
            Species("S2", compartment="c", initialAmount=0.0, name="S2"),
        ],
        reactions=[
            Reaction(
                "R1",
                ReactionEquation(
                    reactants=[
                        EquationPart(species="S1", stoichiometry=1.0, sboTerm=sbo_term)
                    ],
                    products=[EquationPart(species="S2", stoichiometry=1.0)],
                ),
                name="reaction",
            )
        ],
    )
    sbml_path = tmp_path / "model.xml"
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(model=model, filepath=sbml_path, validate=False)

    assert _records(caplog, logging.ERROR) == []
    doc: libsbml.SBMLDocument = read_sbml(source=sbml_path, validate=False)
    sref: libsbml.SpeciesReference = doc.getModel().getReaction("R1").getReactant(0)
    assert sref.getSBOTermID() == "SBO:0000011"
    assert doc.getModel().getSpecies("S1").getSBOTermID() == "SBO:0000011"


def test_an_sbase_attribute_of_a_package_element_advises_the_sbml_version(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the advice for an `SBase` attribute of a package element.

    A `<comp:replacedElement>` has no `comp:id` below SBML L3V2 although comp
    version 1 is the only version of comp there is: the `id` of an element of
    a package is the `id` of an `SBase`, which came with L3V2. The advice is
    therefore the SBML version, not a later version of comp.
    """
    model = Model(
        sid="replaced_element_id",
        name="a model which names its replacement",
        packages=[Package.COMP_V1],
        model_definitions=[
            ModelDefinition(
                sid="md1",
                name="a model definition",
                parameters=[Parameter("k", 1.0, name="k")],
            )
        ],
        submodels=[Submodel(sid="sub1", modelRef="md1", name="submodel")],
        parameters=[
            Parameter(
                "k",
                1.0,
                name="k",
                replacedBy=None,
            )
        ],
        replaced_elements=[
            ReplacedElement(
                sid="k_RE",
                name="the replacement of k",
                metaId="meta_k_RE",
                elementRef="k",
                submodelRef="sub1",
                idRef="k",
            )
        ],
    )
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        create_model(
            model=model,
            filepath=tmp_path / "model.xml",
            sbml_level=3,
            sbml_version=1,
            validate=False,
        )

    reports = [
        m
        for m in _records(caplog, logging.WARNING)
        if "<replacedElement>" in m and "'id'" in m
    ]
    assert len(reports) == 1, reports
    assert "comp version 1 of an SBML L3V1 document" in reports[0]
    assert reports[0].endswith("Write SBML Level 3 Version 2 to keep it.")


@pytest.mark.parametrize(
    "plugin_of, element_name",
    [("species", "species"), ("reaction", "reaction"), ("model", "model")],
)
def test_an_attribute_of_a_plugin_is_reported_and_does_not_raise(
    plugin_of: str,
    element_name: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that the report names the element of a libsbml plugin.

    `_check_attribute` is handed the object the attribute was set on, which
    for the fbc attributes of a species, of a reaction and of a model is the
    fbc **plugin** of the element. A plugin has no `getElementName` at all
    (measured with libsbml 5.21.2), so building the report from it raised
    `AttributeError`, which `_create_object` re-raises and which would take
    the whole file with it: the report would be the failure. No input
    reaches that branch today, since the three plugin setters answer success
    at every fbc version, so the branch is forced here.
    """
    ns = libsbml.SBMLNamespaces(3, 1)
    ns.addPackageNamespace("fbc", 2)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(ns)
    libsbml_model: libsbml.Model = doc.createModel()
    libsbml_model.setId("m")
    species: libsbml.Species = libsbml_model.createSpecies()
    species.setId("S1")
    reaction: libsbml.Reaction = libsbml_model.createReaction()
    reaction.setId("R1")
    owner = {
        "species": species,
        "reaction": reaction,
        "model": libsbml_model,
    }[plugin_of]
    plugin = owner.getPlugin("fbc")

    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        written = factory._check_attribute(
            libsbml.LIBSBML_UNEXPECTED_ATTRIBUTE,
            plugin,
            "chemicalFormula",
            "H2O",
            "an element",
        )

    assert written is False
    messages = _records(caplog, logging.WARNING)
    assert len(messages) == 1, messages
    assert "'chemicalFormula' of 'an element'" in messages[0]
    assert "fbc version 2 of an SBML L3V1 document" in messages[0]

    # inside a document the same loss is grouped under the element of the
    # plugin, which is what the element name of the report has to be
    with (
        factory.collect_attribute_losses(),
        caplog.at_level(logging.WARNING, logger="sbmlutils"),
    ):
        caplog.clear()
        factory._check_attribute(
            libsbml.LIBSBML_UNEXPECTED_ATTRIBUTE,
            plugin,
            "chemicalFormula",
            "H2O",
            "an element",
        )
    grouped = _records(caplog, logging.WARNING)
    assert len(grouped) == 1, grouped
    assert f"<{element_name}> element(s)" in grouped[0]
