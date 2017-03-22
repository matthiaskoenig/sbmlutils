"""
Unit tests for the comp module.
"""

from __future__ import print_function, absolute_import

import libsbml

from sbmlutils.comp import flattenExternalModelDefinitions
from sbmlutils import sbmlio
from sbmlutils import validation
from sbmlutils.tests import data
from sbmlutils import comp
from sbmlutils import factory as fac


def create_port_doc():
    sbmlns = libsbml.SBMLNamespaces(3, 1, 'comp', 1)
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("toy_update")
    model.setName("toy (UPDATE submodel)")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    objects = [
        fac.Compartment(sid='extern', value=1.0, unit="m3", constant=True, name='external compartment'),
        fac.Species(sid='A', name="A", value=10.0, hasOnlySubstanceUnits=True, compartment="extern"),
        fac.Species(sid='C', name="C", value=0, hasOnlySubstanceUnits=True, compartment="extern"),
        fac.Parameter(sid="EX_A", value=1.0, constant=False, sboTerm="SBO:0000613"),
        fac.Parameter(sid="EX_C", value=1.0, constant=False, sboTerm="SBO:0000613"),
    ]
    fac.create_objects(model, objects)
    return doc


def test_create_ports_dict():
    doc = create_port_doc()
    model = doc.getModel()

    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs={"extern_port": "extern",
                              "A_port": "A",
                              "C_port": "C",
                              "EX_A_port": "EX_A",
                              "EX_C_port": "EX_C"})

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


def test_create_ports_list():
    doc = create_port_doc()
    model = doc.getModel()

    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["extern", "A", "C", "EX_A", "EX_C"])

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


def test_flattenExternalModelDefinition():
    sbml_path = data.DFBA_EMD_SBML
    print(sbml_path)
    doc = sbmlio.read_sbml(sbml_path)

    # test that resource could be read
    assert doc is not None
    # test that model in document
    assert doc.getModel() is not None
    print(doc)
    print(doc.getModel().getId())

    # check that model exists
    doc_no_emd = flattenExternalModelDefinitions(doc, validate=True)
    assert doc_no_emd is not None

    # check that there are no external model definitions
    comp_doc_no_emd = doc_no_emd.getPlugin("comp")
    assert 0 == comp_doc_no_emd.getNumExternalModelDefinitions()

    # check that all model definitions are still there
    assert 3 == comp_doc_no_emd.getNumModelDefinitions()

    # check model consistency
    Nall, Nerr, Nwarn = validation.check_doc(doc_no_emd)
    # assert Nall == 0
    # FIXME: currently not possible to flatten, add test when fixing method

