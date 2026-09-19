"""Tests for the comp package."""

import logging
from pathlib import Path
from typing import Any

import libsbml
import pytest

from sbmlutils import comp
from sbmlutils.factory import *
from sbmlutils.factory import PortType, create_objects
from sbmlutils.io import read_sbml
from sbmlutils.metadata import SBO
from sbmlutils.validation import ValidationOptions


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
