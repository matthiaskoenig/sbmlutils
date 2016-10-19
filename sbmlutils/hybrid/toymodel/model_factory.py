# -*- coding=utf-8 -*-
"""
This module creates the sub-models and combined comp model for the toy model.

The toy model consists hereby of
- a FBA submodels
- deterministic ODE models
- and stochastic ODE models

The SBML comp extension is used for hierarchical model composition, i.e. to create
the main model and the kinetic model parts.
"""
from libsbml import *

import sbmlutils.sbmlio as sbml_io
import sbmlutils.annotation as sbml_annotation
import sbmlutils.comp as comp
from sbmlutils import factory as mc

XMLOutputStream.setWriteTimestamp(False)

# TODO: add SBOterms for fluxBounds, species, ...

########################################################################
# General model information
########################################################################
version = 2
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Wholecell Toy Model</h1>
    <h2>Description</h2>
    <p>This is a toy model for coupling models with different modeling frameworks via comp.</p>

    <div class="dc:publisher">This file has been produced by
      <a href="https://livermetabolism.com/contact.html" title="Matthias Koenig" target="_blank">Matthias Koenig</a>.
      </div>

    <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2016 Matthias Koenig</div>
      <div class="dc:license">
      <p>Redistribution and use of any part of this model, with or without modification, are permitted provided that
      the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions
              and the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of
              conditions and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>
        This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
             the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.</p>
      </div>
    </body>
""")
creators = [
    mc.Creator(familyName='Koenig', givenName='Matthias', email='konigmatt@googlemail.com',
               organization='Humboldt University Berlin', site='http://livermetabolism.com')
]
main_units = {
    'time': 's',
    'extent': UNIT_KIND_ITEM,
    'substance': UNIT_KIND_ITEM,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}
units = [
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0)]),
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0),
                   (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('per_s', [(UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('item_per_s', [(UNIT_KIND_ITEM, 1.0),
                           (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('item_per_m3', [(UNIT_KIND_ITEM, 1.0),
                            (UNIT_KIND_METRE, -3.0)]),
]

UNIT_AMOUNT = UNIT_KIND_ITEM
UNIT_AREA = 'm2'
UNIT_VOLUME = 'm3'
UNIT_CONCENTRATION = 'item_per_m3'
UNIT_FLUX = 'item_per_s'


def add_generic_info(model):
    """ Adds the shared information to the models.

    :param model: SBMLModel instance
    :return:
    """
    sbml_annotation.set_model_history(model, creators)
    mc.create_objects(model, units)
    mc.set_main_units(model, main_units)
    model.setNotes(notes)


####################################################
# ODE flux bounds
####################################################
def create_ode_bounds(sbml_file):
    """"
    Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("toy_ode_bounds")
    model.setName("ODE bound calculation submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    objects = [
        # parameters
        mc.Parameter(sid='ub_R1', value=1.0, unit=UNIT_FLUX, name='ub_r1', constant=False),
        mc.Parameter(sid='k1', value=-0.2, unit="per_s", name="k1", constant=False),

        # rate rules
        mc.RateRule(sid="ub_R1", value="k1*ub_R1")
    ]
    mc.create_objects(model, objects)

    # ports
    comp._create_port(model, pid="ub_R1_port", idRef="ub_R1", portType=comp.PORT_TYPE_PORT)

    sbml_io.write_and_check(doc, sbml_file)


####################################################
# FBA submodel
####################################################
def create_fba(sbml_file):
    """
    Create the fba model.
    FBA submodel in FBC v2 which uses parameters as flux bounds.
    """
    sbmlns = SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 2)
    sbmlns.addPackageNamespace("comp", 1)

    doc_fba = SBMLDocument(sbmlns)
    doc_fba.setPackageRequired("comp", True)
    mdoc = doc_fba.getPlugin("comp")
    doc_fba.setPackageRequired("fbc", False)
    model = doc_fba.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(False)

    # model
    model.setId('toy_fba')
    model.setName('FBA submodel')
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)
    add_generic_info(model)

    # Compartments
    compartments = [
        mc.Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment', spatialDimension=3),
        mc.Compartment(sid='cell', value=1.0, unit=UNIT_VOLUME, constant=True, name='cell', spatialDimension=3),
        mc.Compartment(sid='membrane', value=1.0, unit=UNIT_AREA, constant=True, name='membrane', spatialDimension=2),
    ]
    mc.create_objects(model, compartments)

    # Species
    species = [
        # external
        mc.Species(sid='A', name="A", value=10, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern", boundaryCondition=True),
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern", boundaryCondition=True),
        # internal
        mc.Species(sid='B1', name="B1", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="cell"),
        mc.Species(sid='B2', name="B2", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="cell"),
    ]
    mc.create_objects(model, species)

    parameters = [
        # bounds
        mc.Parameter(sid="ub_R1", name="ub R1", value=1.0, unit=UNIT_FLUX, constant=False),
        mc.Parameter(sid="lb", name="lower bound", value=0.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub", name="upper bound", value=1000.0, unit=UNIT_FLUX, constant=True),
    ]
    mc.create_objects(model, parameters)

    # reactions with constant flux
    r1 = mc.create_reaction(model, rid="R1", name="A import (R1)", fast=False, reversible=True,
                            reactants={"A": 1}, products={"B1": 1}, compartment='membrane')
    r2 = mc.create_reaction(model, rid="R2", name="B1 <-> B2 (R2)", fast=False, reversible=True,
                            reactants={"B1": 1}, products={"B2": 1}, compartment='cell')
    r3 = mc.create_reaction(model, rid="R3", name="B2 export (R3)", fast=False, reversible=True,
                            reactants={"B2": 1}, products={"C": 1}, compartment='membrane')

    # flux bounds
    mc.set_flux_bounds(r1, lb="lb", ub="ub_R1")
    mc.set_flux_bounds(r2, lb="lb", ub="ub")
    mc.set_flux_bounds(r3, lb="lb", ub="ub")

    # objective function
    mc.create_objective(mplugin, oid="R3_maximize", otype="maximize", fluxObjectives={"R3": 1.0})

    # create ports
    comp._create_port(model, pid="R3_port", idRef="R3", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_R1_port", idRef="ub_R1", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="cell_port", idRef="cell", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="extern_port", idRef="extern", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc_fba, sbml_file)


####################################################
# ODE species update
####################################################
def create_ode_update(sbml_file):
    """
        Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()
    model.setId("toy_ode_update")
    model.setName("ODE metabolite update submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    compartments = [
        mc.Compartment(sid='extern', value=1.0, unit="m3", constant=True, name='external compartment', spatialDimension=3),
    ]
    mc.create_objects(model, compartments)

    # only update the boundarySpecies in the reactions
    species = [
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern", boundaryCondition=False),
    ]
    mc.create_objects(model, species)

    parameters = [
        mc.Parameter(sid="vR3", name="vR3 (FBA flux)", value=0.1, constant=True, unit="item_per_s"),
    ]
    mc.create_objects(model, parameters)

    # kinetic reaction (MMK)
    mc.create_reaction(model, rid="R3", name="-> C", fast=False, reversible=False,
                       reactants={}, products={"C": 1}, formula="vR3", compartment="extern")

    comp._create_port(model, pid="vR3_port", idRef="vR3", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="extern_port", idRef="extern", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc, sbml_file)


####################################################
# ODE/SSA model
####################################################
def create_ode_model(sbml_file):
    """" Kinetic submodel (coupled model to FBA). """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()
    model.setId("toy_ode_model")
    model.setName("ODE/SSA submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    compartments = [
        mc.Compartment(sid='extern', value=1.0, unit="m3", constant=True, name='external compartment', spatialDimension=3),
    ]
    mc.create_objects(model, compartments)

    species = [
        # external
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern", boundaryCondition=False),
        mc.Species(sid='D', name="D", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern", boundaryCondition=False),
    ]
    mc.create_objects(model, species)

    parameters = [
        mc.Parameter(sid="k_R4", name="k R4", value=0.1, constant=True, unit="per_s"),
    ]
    mc.create_objects(model, parameters)

    # kinetic reaction (MMK)
    mc.create_reaction(model, rid="R4", name="C -> D", fast=False, reversible=False,
                       reactants={"C": 1}, products={"D": 1}, formula="k_R4*C", compartment="extern")

    comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="extern_port", idRef="extern", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc, sbml_file)


########################################################################################################################
if __name__ == "__main__":
    from simsettings import *
    import os

    os.chdir(out_dir)

    # write & check sbml
    create_ode_bounds(ode_bounds_file)
    create_fba(fba_file)
    create_ode_update(ode_update_file)
    create_ode_model(ode_model_file)
