"""Tests for the comp package."""

import logging
import os
from pathlib import Path
from typing import Any

import libsbml
import pytest
from structural import snapshot
from test_roundtrip import requires_testsuite, testsuite_case

from sbmlutils import comp
from sbmlutils.factory import *
from sbmlutils.factory import PortType, SbaseRef, create_objects
from sbmlutils.io import read_sbml
from sbmlutils.metadata import SBO
from sbmlutils.validation import ValidationOptions, validate_doc


def create_port_doc() -> libsbml.SBMLDocument:
    """Test create port."""
    sbmlns = libsbml.SBMLNamespaces(3, 1, "comp", 1)
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("toy_update")
    model.setName("toy (UPDATE submodel)")
    model.setSBOTerm(SBO.CONTINUOUS_FRAMEWORK)

    objects = [
        Compartment(
            sid="extern",
            value=1.0,
            constant=True,
            name="external compartment",
        ),
        Species(
            sid="A",
            name="A",
            initialConcentration=10.0,
            hasOnlySubstanceUnits=True,
            compartment="extern",
        ),
        Species(
            sid="C",
            name="C",
            initialConcentration=0,
            hasOnlySubstanceUnits=True,
            compartment="extern",
        ),
        Parameter(sid="EX_A", value=1.0, constant=False, sboTerm="SBO:0000613"),
        Parameter(sid="EX_C", value=1.0, constant=False, sboTerm="SBO:0000613"),
    ]
    create_objects(model, obj_iter=objects)
    return doc


def test_create_ports_dict() -> None:
    """Test create ports from dict."""
    doc: libsbml.SBMLDocument = create_port_doc()
    model = doc.getModel()

    comp.create_ports(
        model,
        portType=PortType.PORT,
        idRefs={
            "extern_port": "extern",
            "A_port": "A",
            "C_port": "C",
            "EX_A_port": "EX_A",
            "EX_C_port": "EX_C",
        },
    )

    comp_model = model.getPlugin("comp")
    ports = comp_model.getListOfPorts()
    assert ports is not None
    assert comp_model.getNumPorts() == 5
    assert comp_model.getPort("extern_port")
    assert comp_model.getPort("A_port")
    assert comp_model.getPort("C_port")
    assert comp_model.getPort("EX_A_port")
    assert comp_model.getPort("EX_C_port")
    assert comp_model.getPort("tests") is None


def test_create_ports_list() -> None:
    """Test create ports from list."""
    doc: libsbml.SBMLDocument = create_port_doc()
    model = doc.getModel()

    comp.create_ports(
        model, portType=PortType.PORT, idRefs=["extern", "A", "C", "EX_A", "EX_C"]
    )

    comp_model = model.getPlugin("comp")
    ports = comp_model.getListOfPorts()
    assert ports is not None
    assert comp_model.getNumPorts() == 5
    assert comp_model.getPort("extern_port")
    assert comp_model.getPort("A_port")
    assert comp_model.getPort("C_port")
    assert comp_model.getPort("EX_A_port")
    assert comp_model.getPort("EX_C_port")
    assert comp_model.getPort("tests") is None


def _write(model: Model, tmp_path: Path) -> libsbml.SBMLDocument:
    """Write a model at SBML L3V2 and read it back.

    Args:
        model: the model to write
        tmp_path: the directory the SBML is written to

    Returns:
        the document which was written
    """
    create_model(
        model=model,
        filepath=tmp_path / f"{model.sid}.xml",
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )
    return read_sbml(tmp_path / f"{model.sid}.xml")


def _reaction_model(sid: str, reaction: Reaction) -> Model:
    """Create a model around a single reaction `S1 -> S2`.

    Args:
        sid: the id of the model
        reaction: the reaction

    Returns:
        the model
    """
    return Model(
        sid=sid,
        compartments=[Compartment("c", 1.0)],
        species=[
            Species("S1", compartment="c", initialConcentration=1.0),
            Species("S2", compartment="c", initialConcentration=0.0),
        ],
        reactions=[reaction],
    )


def test_comp_is_declared_only_for_comp_content(tmp_path: Path) -> None:
    """Test that a model declares comp if and only if it uses comp."""
    plain = Model(sid="plain", parameters=[Parameter("k", 1.0)])
    doc = _write(plain, tmp_path)
    assert not doc.isPackageEnabled("comp")

    with_port = Model(sid="with_port", parameters=[Parameter("k", 1.0, port=True)])
    doc = _write(with_port, tmp_path)
    assert doc.isPackageEnabled("comp")
    comp_model: libsbml.CompModelPlugin = doc.getModel().getPlugin("comp")
    assert comp_model.getPort("k_port").getIdRef() == "k"


@pytest.mark.parametrize(
    "reaction, port_sid, id_ref",
    [
        (
            Reaction(
                "r1",
                "S1 -> S2",
                formula="k * S1",
                pars=[Parameter("k", 1.0, port=True)],
            ),
            "k_port",
            "k",
        ),
        (
            Reaction(
                "r1",
                "S1 -> S2",
                formula="k * S1",
                pars=[Parameter("k", 1.0, constant=False)],
                rules=[AssignmentRule("k", "2.0", sid="rule_k", port=True)],
            ),
            "rule_k_port",
            "rule_k",
        ),
    ],
    ids=["parameter", "rule"],
)
def test_port_in_a_reaction_declares_comp(
    reaction: Reaction, port_sid: str, id_ref: str, tmp_path: Path
) -> None:
    """Test that a port on a parameter or a rule of a reaction declares comp.

    `Reaction.pars` and `Reaction.rules` are written as elements of the
    model. Comp used to be declared on every model; since it is declared only
    for comp content, a port inside a reaction was not found, and writing the
    port raised an `AttributeError` on the missing comp plugin.
    """
    doc = _write(_reaction_model("nested_port", reaction), tmp_path)

    assert doc.isPackageEnabled("comp")
    comp_model: libsbml.CompModelPlugin = doc.getModel().getPlugin("comp")
    assert comp_model.getPort(port_sid).getIdRef() == id_ref


def test_replaced_by_in_a_kinetic_law_declares_comp() -> None:
    """Test that comp content is found wherever an element is nested.

    A local parameter is neither in a list of the model nor in one of a
    reaction, it is in the kinetic law of the reaction.
    """
    replaced_by = ReplacedBy(sid="rby", elementRef="k", submodelRef="sub")
    model = _reaction_model(
        "nested_replaced_by",
        Reaction(
            "r1",
            "S1 -> S2",
            formula=KineticLaw(
                math="k * S1",
                local_parameters=[LocalParameter("k", 1.0, replacedBy=replaced_by)],
            ),
        ),
    )
    assert model._has_comp_content()
    assert not _reaction_model(
        "plain", Reaction("r1", "S1 -> S2", formula="k * S1")
    )._has_comp_content()


def _event_model(sid: str, event: Event) -> Model:
    """Create a model around a single event which assigns the parameter `p1`.

    Args:
        sid: the id of the model
        event: the event

    Returns:
        the model
    """
    return Model(
        sid=sid,
        parameters=[Parameter("p1", 0.0, constant=False)],
        events=[event],
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"trigger": Trigger("time >= 10", sid="t1", port=True)},
        {"trigger": "time >= 10", "priority": Priority("1", sid="pr1", port=True)},
        {"trigger": "time >= 10", "delay": Delay("2", sid="d1", port=True)},
    ],
    ids=["trigger", "priority", "delay"],
)
def test_port_on_an_event_child_is_comp_content(kwargs: dict[str, Any]) -> None:
    """Test that a port on a trigger, priority or delay is found.

    They are held by the `Event`, which is walked like every other element
    of the model, see `Model._has_comp_content`.
    """
    event = Event("e1", assignments={"p1": 1.0}, **kwargs)
    assert _event_model("event_child_port", event)._has_comp_content()
    assert not _event_model(
        "plain", Event("e1", trigger="time >= 10", priority="1", delay="2")
    )._has_comp_content()


def test_replaced_by_on_a_trigger_is_written() -> None:
    """Test that the replacedBy of a trigger is written onto the trigger."""
    sbmlns = libsbml.SBMLNamespaces(3, 2, "comp", 1)
    doc = libsbml.SBMLDocument(sbmlns)
    model: libsbml.Model = doc.createModel()
    p1: libsbml.Parameter = model.createParameter()
    p1.setId("p1")
    p1.setConstant(False)

    trigger = Trigger(
        "time >= 10",
        sid="t1",
        replacedBy=ReplacedBy(sid="rby", elementRef="t_sub", submodelRef="sub"),
    )
    Event("e1", trigger=trigger, assignments={"p1": 1.0}).create_sbml(model)

    trigger_comp: libsbml.CompSBasePlugin = (
        model.getEvent("e1").getTrigger().getPlugin("comp")
    )
    assert trigger_comp.isSetReplacedBy()
    assert trigger_comp.getReplacedBy().getSubmodelRef() == "sub"


def test_port_without_comp_raises_a_value_error() -> None:
    """Test that a port written into a model without comp names the element."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()

    with pytest.raises(ValueError, match="port of Parameter 'k'"):
        Parameter("k", 1.0, port=True).create_sbml(model)


def test_port_needs_an_id(caplog: pytest.LogCaptureFixture) -> None:
    """Test that a port is not created for an element without an id.

    A rule has no id unless it is given one, so `port=True` has nothing to
    reference. The port used to be written as `None_port` with the id
    reference `None`.
    """
    sbmlns = libsbml.SBMLNamespaces(3, 2, "comp", 1)
    doc = libsbml.SBMLDocument(sbmlns)
    model: libsbml.Model = doc.createModel()
    k: libsbml.Parameter = model.createParameter()
    k.setId("k")
    k.setConstant(False)

    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        AssignmentRule("k", "2.0", port=True).create_sbml(model)

    comp_model: libsbml.CompModelPlugin = model.getPlugin("comp")
    assert comp_model.getNumPorts() == 0
    assert any("port" in record.getMessage() for record in caplog.records)


def _nested_sbaseref_chain(prefix: str) -> SbaseRef:
    """Build a three level chain of nested `sBaseRef` for a test.

    Args:
        prefix: distinguishes the `idRef` of every level across the ports,
            replaced elements, replaced by and deletions of one test

    Returns:
        the first level, whose own `sBaseRef` holds the second, whose own
        `sBaseRef` holds the third
    """
    return SbaseRef(
        sid=f"{prefix}_L1",
        idRef=f"{prefix}_target_L1",
        sBaseRef=SbaseRef(
            sid=f"{prefix}_L2",
            idRef=f"{prefix}_target_L2",
            sBaseRef=SbaseRef(
                sid=f"{prefix}_L3",
                idRef=f"{prefix}_target_L3",
            ),
        ),
    )


def _assert_nested_sbaseref_chain(sbaseref: libsbml.SBaseRef, prefix: str) -> None:
    """Walk a three level nested `sBaseRef` chain built by `_nested_sbaseref_chain`.

    Args:
        sbaseref: the first level, as read back from a written document
        prefix: the prefix `_nested_sbaseref_chain` was built with
    """
    assert sbaseref.getIdRef() == f"{prefix}_target_L1"
    level2 = sbaseref.getSBaseRef()
    assert level2.getIdRef() == f"{prefix}_target_L2"
    level3 = level2.getSBaseRef()
    assert level3.getIdRef() == f"{prefix}_target_L3"
    assert not level3.isSetSBaseRef()


def test_nested_sbaseref_chain_is_written(tmp_path: Path) -> None:
    """Test that a three deep chain of nested `sBaseRef` survives a write and re-read.

    The SBML spec allows an `sBaseRef` to continue a reference into a
    submodel of the referenced submodel, to arbitrary depth. Every subclass
    of `SbaseRef` inherits the field: a port, a replaced element, a replaced
    by and a deletion each get their own chain here.
    """
    model = Model(
        sid="nested_sbaseref",
        compartments=[
            Compartment("c1", 1.0),
            Compartment(
                "c2",
                1.0,
                replacedBy=ReplacedBy(
                    sid="rby1",
                    elementRef="c2",
                    submodelRef="sub1",
                    sBaseRef=_nested_sbaseref_chain("rby"),
                ),
            ),
        ],
        submodels=[Submodel(sid="sub1", modelRef="emd1")],
        ports=[
            Port(sid="port1", idRef="c1", sBaseRef=_nested_sbaseref_chain("port")),
        ],
        replaced_elements=[
            ReplacedElement(
                sid="re1",
                elementRef="c1",
                submodelRef="sub1",
                sBaseRef=_nested_sbaseref_chain("re"),
            ),
        ],
        deletions=[
            Deletion(
                sid="del1",
                submodelRef="sub1",
                idRef="deleted_x",
                sBaseRef=_nested_sbaseref_chain("del"),
            ),
        ],
    )
    doc = _write(model, tmp_path)
    sbml_model: libsbml.Model = doc.getModel()
    cmodel: libsbml.CompModelPlugin = sbml_model.getPlugin("comp")

    port: libsbml.Port = cmodel.getPort("port1")
    _assert_nested_sbaseref_chain(port.getSBaseRef(), "port")

    c1_comp: libsbml.CompSBasePlugin = sbml_model.getCompartment("c1").getPlugin("comp")
    replaced_element: libsbml.ReplacedElement = c1_comp.getReplacedElement(0)
    _assert_nested_sbaseref_chain(replaced_element.getSBaseRef(), "re")

    c2_comp: libsbml.CompSBasePlugin = sbml_model.getCompartment("c2").getPlugin("comp")
    replaced_by: libsbml.ReplacedBy = c2_comp.getReplacedBy()
    _assert_nested_sbaseref_chain(replaced_by.getSBaseRef(), "rby")

    deletion: libsbml.Deletion = cmodel.getSubmodel("sub1").getDeletion(0)
    _assert_nested_sbaseref_chain(deletion.getSBaseRef(), "del")


def test_replaced_element_sets_id_once(caplog: pytest.LogCaptureFixture) -> None:
    """Test that `SbaseRef._set_fields` sets the id of the created object once.

    `SbaseRef._set_fields` used to set the id both through the base class
    (`Sbase._set_fields`, which routes it through `setId`/`setIdAttribute`
    depending on the element) and again, unconditionally and unchecked, in
    `SbaseRef._set_fields` itself. The redundant call never actually raised
    the two ERROR log lines a first, superficial read suggests: the base
    call is only checked when it neither succeeds nor is skipped because the
    id is not a core attribute of the SBML level and version written (which
    logs at DEBUG, not ERROR), so the second, unchecked call never surfaced
    a visible symptom; it was simply dead code, which this test pins down by
    counting the calls directly. No ERROR is logged either, which is
    asserted too since that was the originally reported symptom.
    """
    sbmlns = libsbml.SBMLNamespaces(3, 2, "comp", 1)
    doc = libsbml.SBMLDocument(sbmlns)
    model: libsbml.Model = doc.createModel()
    model.setId("m1")
    c: libsbml.Compartment = model.createCompartment()
    c.setId("c1")
    c.setConstant(True)
    c.setSpatialDimensions(3.0)
    c.setSize(1.0)
    cplugin: libsbml.CompSBasePlugin = c.getPlugin("comp")
    obj: libsbml.ReplacedElement = cplugin.createReplacedElement()

    set_id_calls: list[str] = []
    original_set_id = obj.setId

    def _spy_set_id(value: str) -> int:
        set_id_calls.append(value)
        return original_set_id(value)

    obj.setId = _spy_set_id  # ty: ignore[invalid-assignment]

    replaced_element = ReplacedElement(sid="re1", elementRef="c1", submodelRef="sub1")
    with caplog.at_level(logging.DEBUG, logger="sbmlutils"):
        replaced_element._set_fields(obj, model)

    assert set_id_calls == ["re1"]
    assert [r for r in caplog.records if r.levelname == "ERROR"] == []
    assert obj.getId() == "re1"


def test_submodel_without_model_ref_is_written_without_raising(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a `Submodel` without a `modelRef` does not raise.

    `comp:modelRef` is a required attribute, so a `Submodel` without one
    writes a document which is not valid, but `create_model` reports, it
    never blocks (see the module docstring of `validation.py`): the
    libsbml `TypeError` this used to raise (`Submodel_setModelRef` refuses
    a null string) is guarded, one ERROR names the submodel instead, and
    validation reports the missing attribute on the written document.
    """
    model = Model(sid="submodel_without_model_ref", submodels=[Submodel(sid="sub1")])

    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        doc = _write(model, tmp_path)

    assert any("sub1" in record.getMessage() for record in caplog.records), (
        "no ERROR named the submodel"
    )

    cmodel: libsbml.CompModelPlugin = doc.getModel().getPlugin("comp")
    submodel: libsbml.Submodel = cmodel.getSubmodel("sub1")
    assert not submodel.isSetModelRef()

    result = validate_doc(doc, options=ValidationOptions(units_consistency=False))
    assert any(error.getErrorId() == 1020607 for error in result.errors), (
        "validation did not report the missing comp:modelRef"
    )


@requires_testsuite
def test_nested_sbaseref_chain_matches_test_suite_case_01132(tmp_path: Path) -> None:
    """Test the written chain against the one carried by test suite case 01132.

    A second oracle beyond `test_nested_sbaseref_chain_is_written`: case
    01132 replaces `S1` (a reference into `sub3`, continued through
    `sub2`'s `sub1` into `sub1`'s own `S1`) with a chain nested two deep,
    `<species id="S1">`'s own `comp:replacedElement` (`idRef="sub2"`,
    `submodelRef="sub3"`) holding a `comp:sBaseRef` (`idRef="sub1"`)
    which holds a further `comp:sBaseRef` (`idRef="S1"`). The same chain is
    built here with the factory and both are reduced to the snapshot
    `tests/structural.py` uses to judge a round trip; the element id path
    of the built chain is identical to the source's by construction (same
    species id, same references, one `replacedElement`), so the attributes
    of the three matching keys are compared directly, which is the
    assertion an unrestricted `structural_diff` of the whole two documents
    would also make for these three keys, the rest of the two documents
    being unrelated content.
    """
    source_doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(
        str(testsuite_case("01132"))
    )
    source_snapshot = snapshot(source_doc)

    model = Model(
        sid="chain_from_01132",
        compartments=[Compartment("C", 10.0, constant=True)],
        species=[
            Species(
                "S1",
                compartment="C",
                initialAmount=5.0,
                hasOnlySubstanceUnits=False,
                boundaryCondition=False,
                constant=True,
            ),
        ],
        submodels=[
            Submodel(sid="sub1", modelRef="moddef1"),
            Submodel(sid="sub2", modelRef="moddef2"),
            Submodel(sid="sub3", modelRef="moddef3"),
        ],
        replaced_elements=[
            ReplacedElement(
                sid="re_for_S1",
                elementRef="S1",
                submodelRef="sub3",
                idRef="sub2",
                sBaseRef=SbaseRef(
                    sid="chain_L2",
                    idRef="sub1",
                    sBaseRef=SbaseRef(sid="chain_L3", idRef="S1"),
                ),
            ),
        ],
    )
    doc = _write(model, tmp_path)
    built_snapshot = snapshot(doc)

    chain_keys = [
        ("comp.replacedElement", "model/species:S1/replacedElement[sub3/idRef=sub2]"),
        (
            "comp.sBaseRef",
            "model/species:S1/replacedElement[sub3/idRef=sub2]/sBaseRef",
        ),
        (
            "comp.sBaseRef",
            "model/species:S1/replacedElement[sub3/idRef=sub2]/sBaseRef/sBaseRef",
        ),
    ]
    for key in chain_keys:
        assert key in source_snapshot, f"the source does not carry {key}"
        assert key in built_snapshot, f"the written chain does not carry {key}"
        assert source_snapshot[key] == built_snapshot[key]


class U(Units):
    """Units of the model definitions below."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    per_min = UnitDefinition("per_min", "1/min")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")


def _model_definition_with_every_element() -> ModelDefinition:
    """Build a model definition which holds one element of every type a model has.

    Returns:
        the model definition, which `test_model_definition_writes_every_element_type`
        writes and reads back
    """
    return ModelDefinition(
        sid="md1",
        name="model definition 1",
        sboTerm=SBO.CONTINUOUS_FRAMEWORK,
        units=U,
        model_units=ModelUnits(
            time=U.min,
            extent=U.mmole,
            substance=U.mmole,
            volume=U.litre,
        ),
        conversionFactor="cf",
        creators=[
            Creator(
                familyName="König",
                givenName="Matthias",
                email="koenigmx@hu-berlin.de",
                organization="Humboldt-University Berlin",
            )
        ],
        functions=[Function("f_double", "lambda(x, 2*x)", name="double")],
        compartments=[Compartment("c", 1.0, unit=U.litre, name="cell")],
        species=[
            Species(
                "S1",
                compartment="c",
                initialConcentration=1.0,
                substanceUnit=U.mmole,
                name="S1",
                charge=-1.0,
                chemicalFormula="C6H12O6",
            )
        ],
        parameters=[
            Parameter("cf", 1.0, U.dimensionless, name="conversion factor"),
            Parameter("k", 1.0, U.per_min, name="rate constant"),
            Parameter(
                "p_assigned", 0.0, U.dimensionless, constant=False, name="assigned"
            ),
            Parameter(
                "p_rate", 0.0, U.dimensionless, constant=False, name="integrated"
            ),
            Parameter(
                "p_algebraic", 0.0, U.dimensionless, constant=False, name="algebraic"
            ),
            Parameter("p_initial", None, U.dimensionless, name="initially assigned"),
        ],
        assignments=[
            InitialAssignment("p_initial", "k * 2", U.dimensionless, name="initial")
        ],
        rules=[AssignmentRule("p_assigned", "k * 3", U.dimensionless)],
        rate_rules=[RateRule("p_rate", "k", U.dimensionless, name="rate rule")],
        algebraic_rules=[
            AlgebraicRule("alg1", "p_algebraic - k", U.dimensionless, name="algebraic")
        ],
        reactions=[
            Reaction(
                "r1",
                "S1 ->",
                formula=("k * S1 * c", U.mmole_per_min),
                name="degradation",
                geneProductAssociation="g1",
            )
        ],
        events=[
            Event("e1", trigger="time >= 10", assignments={"k": 5.0}, name="event")
        ],
        constraints=[
            Constraint(
                "con1",
                math="k > 0",
                message='<body xmlns="http://www.w3.org/1999/xhtml">k &gt; 0</body>',
                name="constraint",
            )
        ],
        gene_products=[GeneProduct("g1", label="G1", name="gene 1")],
        objectives=[
            Objective(
                "obj1",
                objectiveType="maximize",
                active=True,
                fluxObjectives={"r1": 1.0},
                name="objective",
            )
        ],
    )


def test_model_definition_writes_every_element_type(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a model definition writes every element type a model holds.

    A `ModelDefinition` is a `Model`: everything a model can hold is written
    into the `<comp:modelDefinition>`, its unit definitions included. Only
    compartments and species could be passed at all before.
    """
    model = Model(
        sid="model_definition_elements",
        packages=[Package.COMP_V1, Package.FBC_V3],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[_model_definition_with_every_element()],
    )
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        doc = _write(model, tmp_path)

    # the gene product the association names is looked up in the model
    # definition, which holds it, and not in the model of the document
    assert not [
        record
        for record in caplog.records
        if "GeneProduct missing" in record.getMessage()
    ]

    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    md: libsbml.ModelDefinition = doc_comp.getModelDefinition("md1")
    assert md is not None
    assert md.getName() == "model definition 1"

    # units and model units
    assert md.getUnitDefinition("mmole_per_min") is not None
    assert md.getUnitDefinition("per_min") is not None
    assert md.getTimeUnits() == "min"
    assert md.getExtentUnits() == "mmole"
    assert md.getSubstanceUnits() == "mmole"
    assert md.getVolumeUnits() == "litre"
    assert md.getConversionFactor() == "cf"
    assert md.isSetModelHistory()

    # core content
    assert md.getFunctionDefinition("f_double") is not None
    assert md.getCompartment("c") is not None
    assert md.getSpecies("S1") is not None
    assert md.getNumParameters() == 6
    assert md.getNumInitialAssignments() == 1
    assert md.getNumRules() == 3
    assert md.getRule("p_assigned").getTypeCode() == libsbml.SBML_ASSIGNMENT_RULE
    assert md.getRule("p_rate").getTypeCode() == libsbml.SBML_RATE_RULE
    assert md.getNumConstraints() == 1
    assert md.getReaction("r1") is not None
    assert md.getEvent("e1") is not None
    algebraic = [
        rule
        for rule in md.getListOfRules()
        if rule.getTypeCode() == libsbml.SBML_ALGEBRAIC_RULE
    ]
    assert len(algebraic) == 1

    # fbc content
    md_fbc: libsbml.FbcModelPlugin = md.getPlugin("fbc")
    assert md_fbc.getGeneProduct("g1") is not None
    assert md_fbc.getObjective("obj1") is not None
    assert md_fbc.getActiveObjectiveId() == "obj1"
    reaction_fbc: libsbml.FbcReactionPlugin = md.getReaction("r1").getPlugin("fbc")
    assert reaction_fbc.getGeneProductAssociation() is not None
    species_fbc: libsbml.FbcSpeciesPlugin = md.getSpecies("S1").getPlugin("fbc")
    assert species_fbc.getChemicalFormula() == "C6H12O6"


def test_model_definition_units_are_written(tmp_path: Path) -> None:
    """Test that the unit definitions of a model definition are written.

    The `units` of a model definition were commented out of its writer, so a
    model definition could not carry a unit at all and its elements could
    only reference the units of the main model. They are written into the
    `<comp:modelDefinition>` now, where they belong.
    """
    model = Model(
        sid="model_definition_units",
        packages=[Package.COMP_V1],
        units=[UnitDefinition("min", "min")],
        parameters=[Parameter("k_top", 1.0, "min", name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(
                sid="md_units",
                name="model definition with units",
                units=[
                    UnitDefinition("mmole_per_min", "mmole/min"),
                    UnitDefinition("per_min", "1/min"),
                ],
                model_units=ModelUnits(time="per_min"),
                parameters=[
                    Parameter("k", 1.0, "mmole_per_min", name="flux"),
                ],
            )
        ],
    )
    doc = _write(model, tmp_path)

    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    md: libsbml.ModelDefinition = doc_comp.getModelDefinition("md_units")
    assert md.getNumUnitDefinitions() == 2
    udef: libsbml.UnitDefinition = md.getUnitDefinition("mmole_per_min")
    assert udef is not None
    assert udef.getNumUnits() == 2
    assert md.getParameter("k").getUnits() == "mmole_per_min"
    assert md.getTimeUnits() == "per_min"

    # the units of the model definition are its own, the main model keeps its
    assert doc.getModel().getNumUnitDefinitions() == 1
    assert doc.getModel().getUnitDefinition("mmole_per_min") is None


@pytest.mark.parametrize(
    "field, value",
    [
        ("packages", [Package.FBC_V3]),
        ("model_definitions", [ModelDefinition(sid="nested", name="nested")]),
        (
            "external_model_definitions",
            [ExternalModelDefinition(sid="emd", source="other.xml", modelRef="other")],
        ),
    ],
)
def test_model_definition_rejects_document_level_fields(
    field: str, value: Any, tmp_path: Path
) -> None:
    """Test that the fields of the document are rejected on a model definition.

    A package is declared on the `<sbml>` element and a `<comp:modelDefinition>`
    or `<comp:externalModelDefinition>` is a child of it, so none of the three
    has a place on a model definition; comp does not nest model definitions at
    all. They are rejected rather than silently ignored, both when the model
    definition is constructed and when it is written, since the lists of a
    model are commonly populated by assignment afterwards.
    """
    with pytest.raises(ValueError, match=field):
        ModelDefinition(sid="md1", name="model definition", **{field: value})

    model_definition = ModelDefinition(sid="md1", name="model definition")
    setattr(model_definition, field, value)
    model = Model(
        sid="rejected_field",
        packages=[Package.COMP_V1],
        model_definitions=[model_definition],
    )
    with pytest.raises(ValueError, match=field):
        create_model(
            model=model,
            filepath=tmp_path / "rejected_field.xml",
            validation_options=ValidationOptions(units_consistency=False),
        )


def test_model_definition_does_not_write_fbc_strict(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that `fbc:strict` is not written on a model definition.

    libsbml writes `fbc:strict` twice on a `<comp:modelDefinition>`, once
    through the model it subclasses and once through the element itself, and
    the document it then writes is not readable XML ("Duplicate XML
    attribute"). The attribute is not written and the model definition which
    asked for it is reported; the document stays readable.
    """
    model = Model(
        sid="model_definition_strict",
        packages=[Package.COMP_V1, Package.FBC_V3],
        strict=True,
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(
                sid="md_strict",
                name="model definition which asks to be strict",
                strict=True,
                gene_products=[GeneProduct("g1", label="G1", name="gene 1")],
            )
        ],
    )
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        doc = _write(model, tmp_path)

    assert any(
        "md_strict" in record.getMessage() and "strict" in record.getMessage()
        for record in caplog.records
    ), "no warning named the model definition which set 'strict'"

    sbml = (tmp_path / "model_definition_strict.xml").read_text(encoding="utf-8")
    definition_line = [
        line for line in sbml.splitlines() if "comp:modelDefinition " in line
    ]
    assert len(definition_line) == 1
    assert "fbc:strict" not in definition_line[0]

    # the document is readable, which is what not writing the attribute buys;
    # the only error it carries is the missing `fbc:strict` itself, which
    # libsbml reports while reading, not a "Duplicate XML attribute"
    assert [
        doc.getError(index).getErrorId() for index in range(doc.getNumErrors())
    ] == [2020209]
    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    md_fbc: libsbml.FbcModelPlugin = doc_comp.getModelDefinition("md_strict").getPlugin(
        "fbc"
    )
    assert not md_fbc.isSetStrict()
    # the main model writes its own `fbc:strict` as before
    assert doc.getModel().getPlugin("fbc").getStrict() is True


def test_written_model_definition_validates(tmp_path: Path) -> None:
    """Test that a document with a full model definition validates.

    All checks of `sbmlutils.validation` run, the unit consistency check
    included. The one error a model definition with fbc content cannot avoid
    is libsbml 2020209 ("Strict attribute required on <model>"), because
    libsbml cannot write `fbc:strict` on a `<comp:modelDefinition>` without
    making the document unreadable, see `ModelDefinition`.
    """
    model = Model(
        sid="model_definition_validates",
        packages=[Package.COMP_V1, Package.FBC_V3],
        parameters=[Parameter("k_top", 1.0, U.per_min, name="parameter of the model")],
        model_definitions=[_model_definition_with_every_element()],
    )
    create_model(
        model=model,
        filepath=tmp_path / "model_definition_validates.xml",
        sbml_level=3,
        sbml_version=2,
    )
    doc = read_sbml(tmp_path / "model_definition_validates.xml")
    result = validate_doc(doc, options=ValidationOptions())
    # reported once for every consistency check `ValidationOptions` runs
    assert {error.getErrorId() for error in result.errors} == {2020209}
    assert result.warnings == []


def test_submodel_instantiates_a_model_definition(tmp_path: Path) -> None:
    """Test that a submodel of the main model resolves a model definition.

    The elements of the model definition are in the flattened model, which is
    the check that the written model definition is a model libsbml can
    instantiate.
    """
    model = Model(
        sid="model_definition_submodel",
        packages=[Package.COMP_V1],
        submodels=[Submodel(sid="sub1", modelRef="md_sub")],
        model_definitions=[
            ModelDefinition(
                sid="md_sub",
                name="the instantiated model definition",
                units=[UnitDefinition("per_min", "1/min")],
                compartments=[Compartment("c", 1.0, name="cell")],
                species=[
                    Species(
                        "S1", compartment="c", initialConcentration=10.0, name="S1"
                    ),
                    Species("S2", compartment="c", initialConcentration=0.0, name="S2"),
                ],
                parameters=[Parameter("k", 0.1, "per_min", name="rate constant")],
                reactions=[
                    Reaction("r1", "S1 -> S2", formula="k * S1", name="conversion")
                ],
            )
        ],
    )
    sbml_path = tmp_path / "model_definition_submodel.xml"
    create_model(
        model=model,
        filepath=sbml_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    flat_path = tmp_path / "model_definition_submodel_flat.xml"
    working_dir = os.getcwd()
    try:
        comp.flatten_sbml(sbml_path=sbml_path, sbml_flat_path=flat_path)
    finally:
        os.chdir(working_dir)

    doc_flat = read_sbml(flat_path)
    model_flat: libsbml.Model = doc_flat.getModel()
    ids = {element.getId() for element in model_flat.getListOfAllElements()}
    assert "sub1__S1" in ids
    assert "sub1__S2" in ids
    assert "sub1__k" in ids
    assert "sub1__r1" in ids
    # the unit definition of the model definition is flattened like its
    # elements, under the id the flattener prefixes with the submodel
    unit_definition: libsbml.UnitDefinition = model_flat.getUnitDefinition(
        "sub1__per_min"
    )
    assert unit_definition is not None
    assert model_flat.getParameter("sub1__k").getUnits() == "sub1__per_min"


def test_document_declares_the_packages_its_model_definitions_need(
    tmp_path: Path,
) -> None:
    """Test that the document declares what the content of a model definition needs.

    A model definition is a model of its own but has no way to declare a
    package: a package is declared on the `<sbml>` element, which is written
    from the packages of the model of the document. So the document looks
    into its model definitions, the way it declares comp for a model which
    uses a comp construct without asking for the package.
    """
    model = Model(
        sid="model_definition_packages",
        packages=[Package.COMP_V1],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(
                sid="md_fbc",
                name="model definition which needs fbc",
                gene_products=[GeneProduct("g1", label="G1", name="gene 1")],
            ),
            ModelDefinition(
                sid="md_distrib",
                name="model definition which needs distrib",
                parameters=[
                    Parameter(
                        "k",
                        1.0,
                        name="uncertain parameter",
                        uncertainties=[Uncertainty(sid="unc", formula="normal(1, 1)")],
                    )
                ],
            ),
        ],
    )
    doc = _write(model, tmp_path)

    assert doc.isPackageEnabled("comp")
    assert doc.isPackageEnabled("fbc")
    assert doc.isPackageEnabled("distrib")

    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    md_fbc: libsbml.FbcModelPlugin = doc_comp.getModelDefinition("md_fbc").getPlugin(
        "fbc"
    )
    assert md_fbc.getGeneProduct("g1").getLabel() == "G1"
    parameter: libsbml.Parameter = doc_comp.getModelDefinition(
        "md_distrib"
    ).getParameter("k")
    parameter_distrib: libsbml.DistribSBasePlugin = parameter.getPlugin("distrib")
    assert parameter_distrib.getNumUncertainties() == 1


def test_a_plain_model_definition_declares_no_further_package(tmp_path: Path) -> None:
    """Test that a model definition without package content declares none.

    The document declares the packages the content of its model definitions
    needs, and nothing beyond that: a model definition of plain core content
    leaves the document with comp alone.
    """
    model = Model(
        sid="model_definition_core_only",
        packages=[Package.COMP_V1],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(
                sid="md_core",
                name="model definition of core content",
                compartments=[Compartment("c", 1.0, name="cell")],
                parameters=[Parameter("k", 1.0, name="rate constant")],
            )
        ],
    )
    doc = _write(model, tmp_path)

    assert doc.isPackageEnabled("comp")
    assert not doc.isPackageEnabled("fbc")
    assert not doc.isPackageEnabled("distrib")


def test_a_model_definition_keeps_the_fbc_version_of_the_document(
    tmp_path: Path,
) -> None:
    """Test that a model definition does not add a second version of fbc.

    The content of a model definition says that it needs fbc, not which
    version of it: a document which already declares one keeps it.
    """
    model = Model(
        sid="model_definition_fbc_v2",
        packages=[Package.COMP_V1, Package.FBC_V2],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(
                sid="md_fbc_v2",
                name="model definition which needs fbc",
                gene_products=[GeneProduct("g1", label="G1", name="gene 1")],
            )
        ],
    )
    doc = _write(model, tmp_path)

    fbc_plugin: libsbml.SBMLDocumentPlugin = doc.getPlugin("fbc")
    assert fbc_plugin.getPackageVersion() == 2
