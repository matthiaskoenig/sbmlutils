"""Tests for the comp package."""

import logging
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
