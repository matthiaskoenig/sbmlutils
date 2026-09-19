"""Tests for the comp package."""

import logging
import os
import re
from pathlib import Path
from typing import Any

import libsbml
import pytest
from structural import roundtrip_document, snapshot, structural_diff
from test_roundtrip import requires_testsuite, testsuite_case

from sbmlutils import comp
from sbmlutils.factory import *
from sbmlutils.factory import PortType, SbaseRef, create_objects
from sbmlutils.io import read_sbml
from sbmlutils.layout import Layout, SpeciesGlyph
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


def _write(model: Model, tmp_path: Path, validate: bool = True) -> libsbml.SBMLDocument:
    """Write a model at SBML L3V2 and read it back.

    Args:
        model: the model to write
        tmp_path: the directory the SBML is written to
        validate: whether the written document is validated, which a test
            about what is written rather than about validity turns off

    Returns:
        the document which was written
    """
    create_model(
        model=model,
        filepath=tmp_path / f"{model.sid}.xml",
        sbml_level=3,
        sbml_version=2,
        validate=validate,
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


def test_port_in_a_kinetic_law_declares_comp() -> None:
    """Test that comp content is found wherever an element is nested.

    A local parameter is neither in a list of the model nor in one of a
    reaction, it is in the kinetic law of the reaction. The construct was the
    `replacedBy` of the local parameter, which it no longer offers: no
    `<comp:replacedBy>` on a `<localParameter>` is valid, see the class
    docstring of `LocalParameter`. Its port is the comp construct it does
    carry, and it is nested exactly where the replacedBy was.
    """
    model = _reaction_model(
        "nested_port",
        Reaction(
            "r1",
            "S1 -> S2",
            formula=KineticLaw(
                math="k * S1",
                local_parameters=[LocalParameter("k", 1.0, metaId="meta_k", port=True)],
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
    # the message of the check which must fire, not just the field name: a
    # `ValueError` of `check_packages` would name `packages` as well
    message = f"'{field}' is not supported on ModelDefinition 'md1'"
    with pytest.raises(ValueError, match=re.escape(message)):
        ModelDefinition(sid="md1", name="model definition", **{field: value})

    model_definition = ModelDefinition(sid="md1", name="model definition")
    setattr(model_definition, field, value)
    model = Model(
        sid="rejected_field",
        packages=[Package.COMP_V1],
        model_definitions=[model_definition],
    )
    with pytest.raises(ValueError, match=re.escape(message)):
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

    # the main model gains the `fbc:strict` of a model which declares fbc,
    # although it asked for neither: fbc requires the attribute on a model
    # which carries the fbc plugin, and a document whose model has no
    # `fbc:strict` is reported by libsbml with the error 2020209
    main_fbc: libsbml.FbcModelPlugin = doc.getModel().getPlugin("fbc")
    assert main_fbc.isSetStrict()
    assert main_fbc.getStrict() is False

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


def _mathml(sbase: Any) -> str:
    """Get the MathML of an element which carries math, on one line.

    Args:
        sbase: the libsbml object whose `getMath()` is written out

    Returns:
        the MathML string with its whitespace collapsed
    """
    return " ".join(libsbml.writeMathMLToString(sbase.getMath()).split())


def _uncertainty_math(sbase: libsbml.SBase, key: str) -> dict[str, str]:
    """Get the MathML of the uncert parameters of the uncertainties of an element.

    Args:
        sbase: the libsbml object the uncertainties are written on
        key: the prefix of the keys of the returned map

    Returns:
        the MathML of every uncert parameter which carries math
    """
    math: dict[str, str] = {}
    plugin: libsbml.DistribSBasePlugin | None = sbase.getPlugin("distrib")
    if plugin is None:
        return math
    for index in range(plugin.getNumUncertainties()):
        uncertainty: libsbml.Uncertainty = plugin.getUncertainty(index)
        for child_index in range(uncertainty.getNumUncertParameters()):
            child: libsbml.UncertParameter = uncertainty.getUncertParameter(child_index)
            if child.isSetMath():
                math[f"{key} uncertainty {index}.{child_index}"] = _mathml(child)
    return math


def _math_of_model(model: libsbml.Model) -> dict[str, str]:
    """Get the MathML of every element of a model which carries math.

    Args:
        model: the libsbml.Model, or the libsbml.ModelDefinition which
            subclasses it, to walk

    Returns:
        the MathML by a key which names the element but not the model, so
        that the map of a model and the map of a model definition of the same
        content can be compared
    """
    math: dict[str, str] = {}
    for function in model.getListOfFunctionDefinitions():
        math[f"function {function.getId()}"] = _mathml(function)
    for assignment in model.getListOfInitialAssignments():
        math[f"initialAssignment {assignment.getSymbol()}"] = _mathml(assignment)
    for rule in model.getListOfRules():
        math[f"rule {rule.getIdAttribute() or rule.getVariable()}"] = _mathml(rule)
    for constraint in model.getListOfConstraints():
        math[f"constraint {constraint.getIdAttribute()}"] = _mathml(constraint)
    for reaction in model.getListOfReactions():
        if reaction.isSetKineticLaw():
            math[f"kineticLaw {reaction.getId()}"] = _mathml(reaction.getKineticLaw())
    for event in model.getListOfEvents():
        if event.isSetTrigger():
            math[f"trigger {event.getId()}"] = _mathml(event.getTrigger())
        if event.isSetPriority():
            math[f"priority {event.getId()}"] = _mathml(event.getPriority())
        if event.isSetDelay():
            math[f"delay {event.getId()}"] = _mathml(event.getDelay())
        for event_assignment in event.getListOfEventAssignments():
            math[f"eventAssignment {event_assignment.getVariable()}"] = _mathml(
                event_assignment
            )
    for parameter in model.getListOfParameters():
        math.update(_uncertainty_math(parameter, f"parameter {parameter.getId()}"))

    model_fbc: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
    if model_fbc is not None:
        for objective in model_fbc.getListOfObjectives():
            for flux_objective in objective.getListOfFluxObjectives():
                math.update(
                    _uncertainty_math(
                        flux_objective, f"fluxObjective {flux_objective.getId()}"
                    )
                )
        for udc in model_fbc.getListOfUserDefinedConstraints():
            for component in udc.getListOfUserDefinedConstraintComponents():
                math.update(
                    _uncertainty_math(component, f"component {component.getId()}")
                )
    return math


def _math_against_time_kwargs(sid: str) -> dict[str, Any]:
    """Build the content of a model whose math everywhere names its own parameters.

    `time` and `avogadro` are SBML csymbols unless the model which the
    formula is parsed against declares a parameter of that name, so the
    written MathML says which model libsbml resolved the math against.

    Args:
        sid: the id of the model

    Returns:
        the keyword arguments of a `Model` or a `ModelDefinition`; `packages`
        is not among them, a model definition does not take it
    """
    return {
        "sid": sid,
        "name": "math which names a parameter called time",
        "compartments": [Compartment("c", 1.0, name="cell")],
        "species": [
            Species("S1", compartment="c", initialConcentration=1.0, name="S1")
        ],
        "parameters": [
            Parameter("time", 2.0, name="a parameter called time"),
            Parameter("avogadro", 3.0, name="a parameter called avogadro"),
            Parameter("p_assigned", 0.0, constant=False, name="assigned"),
            Parameter("p_rate", 0.0, constant=False, name="integrated"),
            Parameter("p_algebraic", 0.0, constant=False, name="algebraic"),
            Parameter("p_initial", None, name="initially assigned"),
            Parameter(
                "p_uncertain",
                1.0,
                name="uncertain",
                uncertainties=[
                    Uncertainty(sid="unc_p", formula="normal(time, avogadro)")
                ],
            ),
        ],
        "functions": [Function("f_time", "lambda(x, x * time)", name="function")],
        "assignments": [
            InitialAssignment("p_initial", "time + avogadro", name="initial")
        ],
        "rules": [AssignmentRule("p_assigned", "time * 2")],
        "rate_rules": [RateRule("p_rate", "avogadro", name="rate rule")],
        "algebraic_rules": [
            AlgebraicRule("alg1", "p_algebraic - time", name="algebraic")
        ],
        "reactions": [
            Reaction(
                "r1",
                "S1 ->",
                formula="time * S1 * avogadro",
                name="degradation",
            )
        ],
        "events": [
            Event(
                "e1",
                trigger="time >= 10",
                priority="avogadro",
                delay="time",
                assignments={"p_assigned": "time * avogadro"},
                name="event",
            )
        ],
        "constraints": [Constraint("con1", math="time > 0", name="constraint")],
        "objectives": [
            Objective(
                "obj1",
                objectiveType="maximize",
                active=True,
                name="objective",
                fluxObjectives=[
                    FluxObjective(
                        reaction="r1",
                        coefficient=1.0,
                        sid="fo1",
                        name="flux objective",
                        uncertainties=[
                            Uncertainty(sid="unc_fo", formula="normal(time, avogadro)")
                        ],
                    )
                ],
            )
        ],
        "user_defined_constraints": [
            UserDefinedConstraint(
                sid="udc1",
                name="user defined constraint",
                lowerBound="time",
                upperBound="avogadro",
                components=[
                    UserDefinedConstraintComponent(
                        sid="udcc1",
                        name="component",
                        variable="p_assigned",
                        coefficient="time",
                        variableType="linear",
                        uncertainties=[
                            Uncertainty(
                                sid="unc_udcc", formula="normal(time, avogadro)"
                            )
                        ],
                    )
                ],
            )
        ],
    }


def test_math_of_a_model_definition_is_parsed_against_it(tmp_path: Path) -> None:
    """Test that the math of a model definition resolves its own ids.

    libsbml answers `getModel()` of an element inside a `<comp:modelDefinition>`
    with the model of the *document*, so an element writer which reaches for
    the model that way parses the math of a model definition against the
    wrong model. It is silent: `time` and `avogadro` are written as the SBML
    csymbol instead of as a reference to the parameter of that name, and the
    document validates. The same content is written here as the model of a
    document and as a model definition; both must write the same math.
    """
    top = Model(
        packages=[Package.FBC_V3, Package.DISTRIB_V1],
        **_math_against_time_kwargs("math_top"),
    )
    doc_top = _write(top, tmp_path, validate=False)

    main = Model(
        sid="math_main",
        name="a main model without a parameter called time",
        packages=[Package.COMP_V1, Package.FBC_V3, Package.DISTRIB_V1],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[ModelDefinition(**_math_against_time_kwargs("math_md"))],
    )
    doc_md = _write(main, tmp_path, validate=False)

    math_top = _math_of_model(doc_top.getModel())
    math_md = _math_of_model(doc_md.getPlugin("comp").getModelDefinition("math_md"))

    # not vacuous: every element type which carries math is in the map
    assert len(math_top) == 14, sorted(math_top)
    assert math_md == math_top

    # and both are right, not just equal: the parameters of the model, not
    # the csymbols of the same name. The function definition is the one
    # element which names the csymbol, in a model definition and in the model
    # of a document alike: it is created before the parameters of the model
    # exist (the creation order of `Model._fill_sbml`), and a function
    # definition may not reference a parameter of the model in SBML anyway.
    for key, mathml in math_md.items():
        if key == "function f_time":
            assert "symbols/time" in mathml
            continue
        assert "symbols/time" not in mathml, key
        assert "symbols/avogadro" not in mathml, key


def test_model_definition_writes_its_comp_and_package_content(tmp_path: Path) -> None:
    """Test the constructs the class docstring of `ModelDefinition` claims.

    A model definition carries its own comp content (a submodel, ports, a
    replaced element, a replaced by, a deletion), its model history, its
    key-value pairs and a layout, all through the plugins libsbml attaches to
    a `<comp:modelDefinition>`.
    """
    model = Model(
        sid="model_definition_constructs",
        name="a model with a model definition which uses every plugin",
        packages=[Package.COMP_V1],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(
                sid="md_inner",
                name="the inner model definition",
                parameters=[Parameter("k_inner", 1.0, name="inner parameter")],
                compartments=[Compartment("c", 1.0, name="inner cell")],
            ),
            ModelDefinition(
                sid="md_full",
                name="a model definition with comp content",
                keyValuePairs=[
                    KeyValuePair(key="kind", value="test", uri="https://example.org")
                ],
                creators=[
                    Creator(
                        familyName="König",
                        givenName="Matthias",
                        email="koenigmx@hu-berlin.de",
                        organization="Humboldt-University Berlin",
                    )
                ],
                compartments=[Compartment("c", 1.0, name="cell", port=True)],
                species=[
                    Species(
                        "S1",
                        compartment="c",
                        initialConcentration=1.0,
                        name="S1",
                        replacedBy=ReplacedBy(
                            sid="rby", elementRef="S1", submodelRef="sub_inner"
                        ),
                    )
                ],
                parameters=[Parameter("k", 1.0, name="rate constant")],
                submodels=[Submodel(sid="sub_inner", modelRef="md_inner")],
                ports=[Port(sid="k_port", idRef="k", name="port of k")],
                replaced_elements=[
                    ReplacedElement(
                        sid="re1", elementRef="c", submodelRef="sub_inner", idRef="c"
                    )
                ],
                deletions=[
                    Deletion(sid="del1", submodelRef="sub_inner", idRef="k_inner")
                ],
                layouts=[
                    Layout(
                        sid="layout1",
                        width=100.0,
                        height=100.0,
                        species_glyphs=[
                            SpeciesGlyph(
                                "glyph_S1", species="S1", x=1.0, y=1.0, text="S1"
                            )
                        ],
                    )
                ],
            ),
        ],
    )
    doc = _write(model, tmp_path)

    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    md: libsbml.ModelDefinition = doc_comp.getModelDefinition("md_full")
    md_comp: libsbml.CompModelPlugin = md.getPlugin("comp")

    assert md_comp.getNumSubmodels() == 1
    assert md_comp.getSubmodel("sub_inner").getModelRef() == "md_inner"
    # the explicit port and the one of the `port=True` compartment
    assert {
        md_comp.getPort(index).getId() for index in range(md_comp.getNumPorts())
    } == {
        "k_port",
        "c_port",
    }
    assert md_comp.getSubmodel("sub_inner").getNumDeletions() == 1
    assert md_comp.getSubmodel("sub_inner").getDeletion(0).getIdRef() == "k_inner"

    compartment_comp: libsbml.CompSBasePlugin = md.getCompartment("c").getPlugin("comp")
    assert compartment_comp.getNumReplacedElements() == 1
    assert compartment_comp.getReplacedElement(0).getSubmodelRef() == "sub_inner"
    species_comp: libsbml.CompSBasePlugin = md.getSpecies("S1").getPlugin("comp")
    assert species_comp.isSetReplacedBy()
    assert species_comp.getReplacedBy().getSubmodelRef() == "sub_inner"

    assert md.isSetModelHistory()
    assert md.getModelHistory().getCreator(0).getFamilyName() == "König"

    md_fbc: libsbml.FbcModelPlugin = md.getPlugin("fbc")
    assert md_fbc.getNumKeyValuePairs() == 1
    assert md_fbc.getKeyValuePair(0).getKey() == "kind"

    md_layout: libsbml.LayoutModelPlugin = md.getPlugin("layout")
    assert md_layout.getNumLayouts() == 1
    assert md_layout.getLayout(0).getNumSpeciesGlyphs() == 1

    # none of it landed on the model of the document
    main_comp: libsbml.CompModelPlugin = doc.getModel().getPlugin("comp")
    assert main_comp.getNumPorts() == 0
    assert main_comp.getNumSubmodels() == 0


def test_a_model_definition_can_instantiate_another_one(tmp_path: Path) -> None:
    """Test a submodel of a model definition which names another one.

    The document holds two model definitions, the main model instantiates the
    first and the first instantiates the second; flattening resolves both
    levels.
    """
    model = Model(
        sid="nested_model_definitions",
        name="a model of nested model definitions",
        packages=[Package.COMP_V1],
        submodels=[Submodel(sid="outer", modelRef="md_outer", name="outer submodel")],
        model_definitions=[
            ModelDefinition(
                sid="md_inner",
                name="the inner model definition",
                compartments=[Compartment("c", 1.0, name="inner cell")],
                parameters=[Parameter("k_inner", 3.0, name="inner parameter")],
            ),
            ModelDefinition(
                sid="md_outer",
                name="the outer model definition",
                compartments=[Compartment("c", 1.0, name="outer cell")],
                parameters=[Parameter("k_outer", 2.0, name="outer parameter")],
                submodels=[
                    Submodel(sid="inner", modelRef="md_inner", name="inner submodel")
                ],
            ),
        ],
    )
    sbml_path = tmp_path / "nested_model_definitions.xml"
    create_model(
        model=model,
        filepath=sbml_path,
        sbml_level=3,
        sbml_version=2,
        validation_options=ValidationOptions(units_consistency=False),
    )

    flat_path = tmp_path / "nested_model_definitions_flat.xml"
    working_dir = os.getcwd()
    try:
        comp.flatten_sbml(sbml_path=sbml_path, sbml_flat_path=flat_path)
    finally:
        os.chdir(working_dir)

    doc_flat = read_sbml(flat_path)
    model_flat: libsbml.Model = doc_flat.getModel()
    ids = {element.getId() for element in model_flat.getListOfAllElements()}
    assert "outer__k_outer" in ids
    assert "outer__inner__k_inner" in ids


def test_an_empty_model_definition_is_written(tmp_path: Path) -> None:
    """Test that a model definition without content is written and validates."""
    model = Model(
        sid="empty_model_definition",
        name="a model with an empty model definition",
        packages=[Package.COMP_V1],
        parameters=[Parameter("k_top", 1.0, "dimensionless", name="parameter")],
        model_definitions=[ModelDefinition(sid="md_empty", name="nothing in here")],
    )
    doc = _write(model, tmp_path)

    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    md: libsbml.ModelDefinition = doc_comp.getModelDefinition("md_empty")
    assert md is not None
    assert md.getName() == "nothing in here"
    assert md.getListOfAllElements().getSize() == 0

    result = validate_doc(doc, options=ValidationOptions())
    assert result.errors == []


def test_strict_of_a_model_definition_is_reported_once(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that the dropped `fbc:strict` is reported once per document.

    A reader of the written document sees `fbc:strict` unset on every model
    definition, so only a model definition which claims `True` loses
    something, and the document says it once however many model definitions
    claim it.
    """
    model = Model(
        sid="strict_reported_once",
        name="a model with three model definitions",
        packages=[Package.COMP_V1, Package.FBC_V3],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(sid="md_strict_1", name="first", strict=True),
            ModelDefinition(sid="md_strict_2", name="second", strict=True),
            ModelDefinition(sid="md_not_strict", name="third", strict=False),
            ModelDefinition(sid="md_silent", name="fourth"),
        ],
    )
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        _write(model, tmp_path)

    warnings = [
        record.getMessage()
        for record in caplog.records
        if "strict" in record.getMessage() and record.levelname == "WARNING"
    ]
    assert len(warnings) == 1, warnings
    assert "md_strict_1" in warnings[0]
    assert "md_strict_2" in warnings[0]
    assert "md_not_strict" not in warnings[0]
    assert "md_silent" not in warnings[0]


def test_a_rejected_model_definition_reports_nothing_else(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a rejected model definition is rejected before anything is written.

    The fields of a model definition are checked before the libsbml object is
    created, so a model definition which is rejected neither leaves an empty
    `<comp:modelDefinition>` behind nor reports its dropped `strict`.
    """
    model_definition = ModelDefinition(sid="md_rejected", name="rejected", strict=True)
    model_definition.packages = [Package.FBC_V3]
    model = Model(
        sid="rejected_before_writing",
        name="a model with a rejected model definition",
        packages=[Package.COMP_V1],
        model_definitions=[model_definition],
    )

    with (
        caplog.at_level(logging.WARNING, logger="sbmlutils"),
        pytest.raises(ValueError, match="'packages' is not supported"),
    ):
        create_model(
            model=model,
            filepath=tmp_path / "rejected_before_writing.xml",
            validation_options=ValidationOptions(units_consistency=False),
        )

    assert not [record for record in caplog.records if "strict" in record.getMessage()]


def test_a_model_definition_cannot_be_written_as_a_document(tmp_path: Path) -> None:
    """Test that a model definition is not accepted as the model of a document.

    A `<comp:modelDefinition>` lives next to the `<model>` of a document, it
    is not one: writing a `ModelDefinition` on its own used to produce a
    document without a model, and failed deep inside the comp plugin lookup.
    """
    model_definition = ModelDefinition(
        sid="md_alone",
        name="a model definition on its own",
        parameters=[Parameter("k", 1.0, name="rate constant")],
    )

    with pytest.raises(ValueError, match="not the model of a document"):
        create_model(
            model=model_definition,
            filepath=tmp_path / "md_alone.xml",
            validation_options=ValidationOptions(units_consistency=False),
        )
    with pytest.raises(ValueError, match="not the model of a document"):
        model_definition.get_sbml()


def test_a_model_definition_id_which_collides_is_reported(tmp_path: Path) -> None:
    """Test a model definition whose id collides with another model.

    comp requires the id of a model definition to be unique among the models
    of the document. libsbml writes the document either way, so `create_model`
    writes it and validation reports it (libsbml 1010302), the same as for
    any other invalid document this package writes.
    """
    with_main_model = Model(
        sid="collides_with_the_main_model",
        name="a model whose model definition takes its id",
        packages=[Package.COMP_V1],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(
                sid="collides_with_the_main_model",
                name="the same id as the model of the document",
            )
        ],
    )
    doc = _write(with_main_model, tmp_path)
    result = validate_doc(doc, options=ValidationOptions(units_consistency=False))
    assert {error.getErrorId() for error in result.errors} == {1010302}

    with_each_other = Model(
        sid="model_definitions_collide",
        name="a model with two model definitions of one id",
        packages=[Package.COMP_V1],
        parameters=[Parameter("k_top", 1.0, name="parameter of the main model")],
        model_definitions=[
            ModelDefinition(sid="md", name="the first"),
            ModelDefinition(sid="md", name="the second"),
        ],
    )
    doc = _write(with_each_other, tmp_path)
    assert doc.getPlugin("comp").getNumModelDefinitions() == 2
    result = validate_doc(doc, options=ValidationOptions(units_consistency=False))
    assert {error.getErrorId() for error in result.errors} == {1010302}


def _nested_port_content() -> dict[str, Any]:
    """Get the content of a model whose nested elements each carry a port.

    Every element here lives inside another element rather than in a list of
    the model, or is an element of a package: the kinetic law of a reaction
    with its local parameter, the trigger, priority, delay and assignment of
    an event, an uncertainty and a key-value pair of a parameter, and the
    fbc objectives and user-defined constraints with their children. A
    constraint and an event are in a list of the model, but neither wrote its
    port either.

    The elements whose port names them by their metaid, a local parameter and
    an event assignment, carry one; see `Sbase._port_reference`.

    Returns:
        the keyword arguments of a `Model` or a `ModelDefinition`
    """
    return {
        "compartments": [Compartment("c", 1.0, name="compartment")],
        "species": [
            Species("S1", compartment="c", initialConcentration=1.0, name="S1"),
            Species("S2", compartment="c", initialConcentration=0.0, name="S2"),
        ],
        "parameters": [
            Parameter("k", 1.0, name="k"),
            Parameter("lb", -1000.0, name="lower bound"),
            Parameter("ub", 1000.0, name="upper bound"),
            Parameter("p1", 0.0, constant=False, name="p1"),
            Parameter(
                "p2",
                2.0,
                name="p2",
                uncertainties=[
                    Uncertainty(
                        sid="unc1",
                        name="uncertainty",
                        port=True,
                        uncertParameters=[
                            UncertParameter(
                                type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                                value=0.1,
                            )
                        ],
                    )
                ],
            ),
        ],
        "reactions": [
            Reaction(
                "r1",
                "S1 -> S2",
                name="reaction",
                formula=KineticLaw(
                    math="kf * S1",
                    sid="klaw1",
                    port=True,
                    local_parameters=[
                        LocalParameter(
                            "kf", 1.0, name="kf", metaId="meta_kf", port=True
                        )
                    ],
                ),
            )
        ],
        "events": [
            Event(
                "e1",
                name="event",
                port=True,
                trigger=Trigger("time >= 10", sid="t1", port=True),
                priority=Priority("1", sid="pr1", port=True),
                delay=Delay("2", sid="d1", port=True),
                assignments=[
                    EventAssignment(
                        "p1", "1.0", sid="ea1", metaId="meta_ea1", port=True
                    )
                ],
            )
        ],
        "constraints": [
            Constraint("con1", math="p1 >= 0", name="constraint", port=True)
        ],
        "gene_products": [GeneProduct("gp1", label="gp1", name="gene", port=True)],
        "objectives": [
            Objective(
                "obj1",
                name="objective",
                port=True,
                fluxObjectives=[
                    FluxObjective(
                        reaction="r1",
                        coefficient=1.0,
                        sid="fo1",
                        name="flux objective",
                        port=True,
                    )
                ],
            )
        ],
        "user_defined_constraints": [
            UserDefinedConstraint(
                sid="udc1",
                name="user defined constraint",
                lowerBound="lb",
                upperBound="ub",
                port=True,
                components=[
                    UserDefinedConstraintComponent(
                        variable="r1",
                        coefficient="k",
                        sid="udcc1",
                        name="component",
                        port=True,
                    )
                ],
            )
        ],
    }


#: the port every element of `_nested_port_content` is expected to be given,
#: as `port id -> (reference, target)`
_NESTED_PORTS: dict[str, tuple[str, str]] = {
    "klaw1_port": ("idRef", "klaw1"),
    "kf_port": ("metaIdRef", "meta_kf"),
    "e1_port": ("idRef", "e1"),
    "t1_port": ("idRef", "t1"),
    "pr1_port": ("idRef", "pr1"),
    "d1_port": ("idRef", "d1"),
    "ea1_port": ("metaIdRef", "meta_ea1"),
    "con1_port": ("idRef", "con1"),
    "gp1_port": ("idRef", "gp1"),
    "obj1_port": ("idRef", "obj1"),
    "fo1_port": ("idRef", "fo1"),
    "udc1_port": ("idRef", "udc1"),
    "udcc1_port": ("idRef", "udcc1"),
    "unc1_port": ("idRef", "unc1"),
}


def _ports(model: libsbml.Model) -> dict[str, tuple[str, str]]:
    """Read the ports of a model as `port id -> (reference, target)`.

    Args:
        model: the libsbml.Model, or libsbml.ModelDefinition, to read; its
            document is held by the caller

    Returns:
        the reference each port names its element by, and the name it uses
    """
    comp_model: libsbml.CompModelPlugin = model.getPlugin("comp")
    ports: dict[str, tuple[str, str]] = {}
    for k in range(comp_model.getNumPorts()):
        port: libsbml.Port = comp_model.getPort(k)
        for reference, is_set, get in [
            ("portRef", port.isSetPortRef, port.getPortRef),
            ("idRef", port.isSetIdRef, port.getIdRef),
            ("unitRef", port.isSetUnitRef, port.getUnitRef),
            ("metaIdRef", port.isSetMetaIdRef, port.getMetaIdRef),
        ]:
            if is_set():
                ports[port.getId()] = (reference, get())
    return ports


def test_port_of_a_nested_element_is_written(tmp_path: Path) -> None:
    """Test that every element which can be the target of a port gets one.

    A kinetic law, a local parameter, an event with its trigger, priority,
    delay and assignments, a constraint, an uncertainty, a key-value pair and
    the fbc gene products, objectives, flux objectives, user-defined
    constraints and their components used to accept a `port` which nothing
    wrote, while the document declared comp for it all the same.
    """
    model = Model(
        sid="nested_ports",
        name="ports on nested elements",
        packages=[Package.COMP_V1, Package.DISTRIB_V1, Package.FBC_V3],
        **_nested_port_content(),
    )
    doc = _write(model, tmp_path, validate=False)

    assert _ports(doc.getModel()) == _NESTED_PORTS


def test_port_of_a_nested_element_of_a_model_definition_is_written(
    tmp_path: Path,
) -> None:
    """Test that such a port is written into the model definition it belongs to.

    libsbml answers `getModel()` of an element inside a
    `<comp:modelDefinition>` with the model of the document, so a port
    created from that lookup would land on the main model.
    """
    model = Model(
        sid="nested_ports_in_a_model_definition",
        name="ports on the nested elements of a model definition",
        packages=[Package.COMP_V1],
        model_definitions=[
            ModelDefinition(
                sid="md1", name="a model definition", **_nested_port_content()
            )
        ],
    )
    doc = _write(model, tmp_path, validate=False)

    assert _ports(doc.getModel()) == {}
    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    assert _ports(doc_comp.getModelDefinition("md1")) == _NESTED_PORTS


def test_document_with_a_port_on_a_nested_element_validates(tmp_path: Path) -> None:
    """Test that the ports written for the nested elements validate.

    A port names its element by `comp:idRef`, except a local parameter and an
    event assignment, which it names by `comp:metaIdRef`: libsbml resolves a
    `comp:idRef` with `Model.getElementBySId`, which answers with neither of
    the two, so a port naming them by their id is rejected (1020702) or makes
    the flattened model invalid (1090105).
    """
    model = Model(
        sid="nested_ports_validate",
        name="ports on nested elements",
        packages=[Package.COMP_V1, Package.DISTRIB_V1, Package.FBC_V3],
        **_nested_port_content(),
    )
    doc = _write(model, tmp_path, validate=False)

    assert len(_ports(doc.getModel())) == len(_NESTED_PORTS)
    result = validate_doc(doc, options=ValidationOptions(units_consistency=False))
    assert [
        (error.getErrorId(), error.getShortMessage()) for error in result.errors
    ] == []


def test_roundtrip_keeps_the_port_of_a_nested_element(tmp_path: Path) -> None:
    """Test that the ports of the nested elements survive a round trip.

    The parser reads every `<comp:port>` into `Model.ports`, so a port whose
    element is written by the `port=` shorthand comes back as a `Port` of the
    model and must be written unchanged, its reference included.
    """
    model = Model(
        sid="nested_ports_roundtrip",
        name="ports on nested elements",
        packages=[Package.COMP_V1, Package.DISTRIB_V1, Package.FBC_V3],
        **_nested_port_content(),
    )
    sbml_path = tmp_path / f"{model.sid}.xml"
    create_model(model=model, filepath=sbml_path, validate=False)

    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)

    assert _ports(doc_in.getModel()) == _NESTED_PORTS
    assert [str(d) for d in structural_diff(doc_in, doc_out)] == []


def test_replaced_by_of_a_kinetic_law_is_written(tmp_path: Path) -> None:
    """Test that the replacedBy of a kinetic law is written onto it.

    A kinetic law is written without the `libsbml.Model` which
    `Sbase.create_replaced_by` needs, so its replacedBy used to be accepted
    and silently dropped. libsbml attaches the comp plugin of an `SBase` to a
    `<kineticLaw>`, writes the `<comp:replacedBy>` there, reads it back and
    validates the document.
    """
    model = Model(
        sid="replaced_by_on_a_kinetic_law",
        name="a kinetic law which is replaced by one of a submodel",
        packages=[Package.COMP_V1],
        model_definitions=[
            ModelDefinition(
                sid="md1",
                name="the submodel",
                compartments=[Compartment("c", 1.0, name="compartment")],
                species=[
                    Species("S1", compartment="c", initialConcentration=1.0, name="S1"),
                    Species("S2", compartment="c", initialConcentration=0.0, name="S2"),
                ],
                reactions=[
                    Reaction(
                        "r1",
                        "S1 -> S2",
                        name="reaction of the submodel",
                        formula=KineticLaw(math="2.0 * S1", sid="klaw_sub"),
                    )
                ],
            )
        ],
        submodels=[Submodel(sid="sub1", modelRef="md1")],
        compartments=[Compartment("c", 1.0, name="compartment")],
        species=[
            Species("S1", compartment="c", initialConcentration=1.0, name="S1"),
            Species("S2", compartment="c", initialConcentration=0.0, name="S2"),
        ],
        reactions=[
            Reaction(
                "r1",
                "S1 -> S2",
                name="reaction",
                formula=KineticLaw(
                    math="1.0 * S1",
                    sid="klaw_top",
                    replacedBy=ReplacedBy(
                        sid="rby",
                        elementRef="klaw_top",
                        submodelRef="sub1",
                        idRef="klaw_sub",
                    ),
                ),
            )
        ],
    )
    doc = _write(model, tmp_path, validate=False)

    klaw: libsbml.KineticLaw = doc.getModel().getReaction("r1").getKineticLaw()
    klaw_comp: libsbml.CompSBasePlugin = klaw.getPlugin("comp")
    assert klaw_comp.isSetReplacedBy()
    replaced_by: libsbml.ReplacedBy = klaw_comp.getReplacedBy()
    assert (replaced_by.getSubmodelRef(), replaced_by.getIdRef()) == (
        "sub1",
        "klaw_sub",
    )


@pytest.mark.parametrize("field", ["replacedBy"])
def test_local_parameter_does_not_offer_a_replaced_by(field: str) -> None:
    """Test that a local parameter refuses the replacedBy it cannot write.

    libsbml writes a `<comp:replacedBy>` on a `<localParameter>` and reads it
    back, but no such replacement is valid, see the class docstring of
    `LocalParameter`. The field is refused by the constructor instead of
    being accepted and written into a document which cannot validate. The
    keyword is passed through a mapping, the way the same check is made in
    `tests/test_distrib.py`: spelling it out is a type error, which is the
    point of the test.
    """
    with pytest.raises(TypeError, match=field):
        LocalParameter("kf", 1.0, **{field: None})


#: an element of `sbmlutils.factory` which does not offer `replacedBy`,
#: because libsbml attaches no `CompSBasePlugin` to the libsbml element it
#: creates (measured with libsbml 5.21.2: `getPlugin("comp")` answers with a
#: plain `SBasePlugin`, which has no `createReplacedBy`), or because no
#: `<comp:replacedBy>` on it is valid
_NO_REPLACED_BY: list[Any] = [
    pytest.param(Priority, {"math": "1"}, id="Priority"),
    pytest.param(GeneProduct, {"sid": "gp1", "label": "gp1"}, id="GeneProduct"),
    pytest.param(Objective, {"sid": "obj1"}, id="Objective"),
    pytest.param(
        FluxObjective, {"reaction": "r1", "coefficient": 1.0}, id="FluxObjective"
    ),
    pytest.param(
        UserDefinedConstraint,
        {"lowerBound": "lb", "upperBound": "ub"},
        id="UserDefinedConstraint",
    ),
    pytest.param(
        UserDefinedConstraintComponent,
        {"coefficient": "k", "variable": "r1"},
        id="UserDefinedConstraintComponent",
    ),
    pytest.param(Uncertainty, {"sid": "unc1"}, id="Uncertainty"),
    pytest.param(
        KeyValuePair, {"key": "k", "value": "v", "uri": None}, id="KeyValuePair"
    ),
]


@pytest.mark.parametrize("cls, kwargs", _NO_REPLACED_BY)
def test_replaced_by_is_not_offered_where_it_cannot_be_written(
    cls: type, kwargs: dict[str, Any]
) -> None:
    """Test that an element which cannot carry a replacedBy does not offer one.

    Seven of them are elements of a package (`fbc:geneProduct`,
    `fbc:objective`, `fbc:fluxObjective`, `fbc:userDefinedConstraint`,
    `fbc:userDefinedConstraintComponent`, `distrib:uncertainty`,
    `fbc:keyValuePair`) and one is core (`priority`); libsbml attaches no
    `CompSBasePlugin` to any of them, so it can neither write nor read a
    `<comp:replacedBy>` there, and `Sbase.create_replaced_by` used to fail
    with an `AttributeError` on the plugin.
    """
    with pytest.raises(TypeError, match="replacedBy"):
        cls(replacedBy=None, **kwargs)


@pytest.mark.parametrize("field", ["uncertainties", "keyValuePairs"])
def test_key_value_pair_does_not_offer_what_libsbml_drops(field: str) -> None:
    """Test that a key-value pair offers neither of the two fields it loses.

    libsbml writes neither a `<distrib:listOfUncertainties>` nor a nested
    `<fbc:listOfKeyValuePairs>` inside a `<fbc:keyValuePair>`: both are
    created on the plugin without an error and are gone from the written
    XML (measured with libsbml 5.21.2).
    """
    with pytest.raises(TypeError, match=field):
        KeyValuePair(key="k", value="v", uri=None, **{field: None})


def test_port_of_a_key_value_pair_is_written(tmp_path: Path) -> None:
    """Test that a key-value pair writes the port it accepts.

    A `<fbc:keyValuePair>` is the target of a `<comp:port>` like any other
    element: libsbml resolves its `fbc:id` with `Model.getElementBySId` and
    the document validates (measured with libsbml 5.21.2). The pair is
    written from `Sbase._set_fields` of the element it belongs to, which
    passes the model down for it.
    """
    model = Model(
        sid="key_value_pair_port",
        name="a port on a key-value pair",
        packages=[Package.COMP_V1, Package.FBC_V3],
        parameters=[
            Parameter(
                "k",
                1.0,
                name="k",
                keyValuePairs=[
                    KeyValuePair(
                        key="kind",
                        value="test",
                        uri="https://example.org",
                        sid="kvp1",
                        port=True,
                    )
                ],
            )
        ],
    )
    doc = _write(model, tmp_path, validate=False)

    assert _ports(doc.getModel()) == {"kvp1_port": ("idRef", "kvp1")}
    result = validate_doc(doc, options=ValidationOptions(units_consistency=False))
    assert [error.getErrorId() for error in result.errors] == []
