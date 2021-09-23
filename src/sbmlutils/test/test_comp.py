"""
Tests for the comp module.
"""
import libsbml

from sbmlutils import comp
from sbmlutils.factory import *
from sbmlutils.factory import PORT_TYPE_PORT, create_objects
from sbmlutils.metadata.sbo import SBO


def create_port_doc() -> libsbml.SBMLDocument:
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
    doc: libsbml.SBMLDocument = create_port_doc()
    model = doc.getModel()

    comp.create_ports(
        model,
        portType=PORT_TYPE_PORT,
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
    assert comp_model.getPort("test") is None


def test_create_ports_list() -> None:
    doc: libsbml.SBMLDocument = create_port_doc()
    model = doc.getModel()

    comp.create_ports(
        model, portType=PORT_TYPE_PORT, idRefs=["extern", "A", "C", "EX_A", "EX_C"]
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
    assert comp_model.getPort("test") is None
