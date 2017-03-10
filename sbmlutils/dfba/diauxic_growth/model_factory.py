# -*- coding=utf-8 -*-
"""
This module creates the sub-models and combined comp model for the diauxic model.

Submodels are
- a FBA submodel
- deterministic ODE models

Questions:
- how are the metabolite concentrations kept >= 0 ?
    It seems that the relative change in flux bounds, relative
    to the hard bounds on the exchanges avoids negative concentrations

-----------------------------------------------
Along with the system of dynamic equations, several
additional constraints must be imposed for a realistic prediction
of the metabolite concentrations and the metabolic
fluxes. These include non-negative metabolite and flux levels,
limits on the rate of change of fluxes, and any additional
nonlinear constraints on the transport fluxes.
-----------------------------------------------
vO2:  -> O2
vGlcxt:  -> Glcxt
Ac_out = Ac  # rule

v1: 39.43 Ac + 35 O2 -> X
v2: 9.46 Glcxt + 12.92 O2 -> X
v3: 9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X
v4: 19.23 Glcxt -> 12.12 Ac + X

objective: max(biomass) = max (w1*v1 + w2*v2 + w3*v3 + w4*v4) = max(µ),
            w1 = w2 = w3 = w4 [gdw/mmol]

boundaries:
    # rate of change boundaries => set new lower and upper bound based on
    # the maximal allowed change in boundary over time
    # |d/dt v| <= d/dt v_max
    d/dt v_max(v1) = 0.1 [mmol/h/gdw]
    d/dt v_max(v2) = 0.3 [mmol/h/gdw]
    d/dt v_max(v3) = 0.3 [mmol/h/gdw]
    d/dt v_max(v4) = 0.1 [mmol/h/gdw]

    # in addition the flux bounds must be set, so that not resulting in negative
    # concentrations

    # ? exchange, how does it work ?
    # no external concentrations, but upper bounds for entry in batch reactor
    ub(vO2) = 15 [mmol/h/gdw]
    ub(vGlcxt) = 10 Glcxt/(Km + Glcxt) [mmol/h/gdw]  # Michaelis-Menten kinetics involving glucose concentration

Km = 0.015 mM

-----------------------------------------------

Glcxt:  glucose [mM=mmol/l],    Glcxt(0) = 10.8 [mM]
Ac:     acetate [mM=mmol/l],    Ac(0) = 0.4 [mM]
O2:     oxygen [mM=mmol/l],     O2(0) = 0.21 [mM]
X:      biomass [gdw/l],        X(0) = 0.001 [g/l]

# A*v is row of stoichiometric matrix, i.e. all reactions which change the concentration
d/dt Glcxt = A_Glcxt*v * X                      # [mmol/l/h]
d/dt Ac = A_Ac*v * X                            # [mmol/l/h]
d/dt O2 = A_O2 * v * X + kLa * (O2_gas - O2)    # [mmol/l/h]
d/dt X = (w1*v1 + w2*v2 + w3*v3 + w4*v4)*X      # [g/l/h], due to coefficients conversions to g

O2_gas = 0.21 [mM]  # oxygen in gas phase, constant
kLa = 7.5 [per_h]  # mass transfer coefficient for oxygen

z: vector of metabolite concentrations
v: fluxes per gdw (gram dry weight)
mu: growth rate

-----------------------------------------------
tend = 10 [h]
steps = 10000

-----------------------------------------------
"""
import logging
import warnings
from os.path import join as pjoin

from libsbml import *
# FIXME: remove the * import
import libsbml
from dgsettings import *

XMLOutputStream.setWriteTimestamp(False)

import sbmlutils.sbmlio as sbml_io
from sbmlutils import comp
from sbmlutils import factory as mc
import sbmlutils.annotation as sbml_annotation
from sbmlutils.report import sbmlreport
from sbmlutils.dfba.builder import LOWER_BOUND_DEFAULT, UPPER_BOUND_DEFAULT

########################################################################
# General model information
########################################################################
version = 6
DT_SIM = 0.1
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Diauxic Growth Model</h1>
    <p><strong>Model version: {}</strong></p>

    <h2>Description</h2>
    <p>Dynamic Flux Balance Analysis of Diauxic Growth in Escherichia coli</p>

    <p>The key variables in the mathematical model of the metabolic
network are the glucose concentration (Glcxt), the acetate concentration (Ac),
the biomass concentration (X), and the oxygen concentration (O2) in the gas phase.</p>

    <div class="dc:publisher">This file has been produced by
      <a href="https://livermetabolism.com/contact.html" title="Matthias Koenig" target="_blank">Matthias Koenig</a>.
      </div>

    <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2017 Matthias Koenig</div>
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
""".format(version))
creators = [
    mc.Creator(familyName='Koenig', givenName='Matthias', email='konigmatt@googlemail.com',
               organization='Humboldt University Berlin', site='http://livermetabolism.com')
]
main_units = {
    'time': 'h',
    'extent': 'mmol',
    'substance': 'mmol',
    'length': 'm',
    'area': 'm2',
    'volume': 'l',
}
units = [
    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)]),
    mc.Unit('g', [(UNIT_KIND_GRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('l', [(UNIT_KIND_LITRE, 1.0)]),
    mc.Unit('mmol', [(UNIT_KIND_MOLE, 1.0, -3, 1.0)]),
    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_h', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_l', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('l_per_mmol', [(UNIT_KIND_LITRE, 1.0),
                           (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
    mc.Unit('g_per_l', [(UNIT_KIND_GRAM, 1.0),
                        (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('g_per_mmol', [(UNIT_KIND_GRAM, 1.0),
                           (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
]

UNIT_AMOUNT = 'mmol'
UNIT_AREA = 'm2'
UNIT_VOLUME = 'l'
UNIT_TIME = 'h'
UNIT_CONCENTRATION = 'mmol_per_l'
UNIT_FLUX = 'mmol_per_h'


def add_generic_info(model):
    """ Adds the shared information to the models.

    :param model: SBMLModel instance
    :return:
    """
    sbml_annotation.set_model_history(model, creators)
    mc.create_objects(model, units)
    mc.set_main_units(model, main_units)
    # TODO: model specific notes, to clarify which models are which
    model.setNotes(notes)

########################################################################################################################


def fba_model(sbml_file, directory):
    """ Create FBA submodel.

    FBA submodel in sbml:fbc-version 2.
    """
    sbmlns = SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 2)
    sbmlns.addPackageNamespace("comp", 1)

    doc_fba = SBMLDocument(sbmlns)
    doc_fba.setPackageRequired("comp", True)
    doc_fba.getPlugin("comp")
    doc_fba.setPackageRequired("fbc", False)
    model = doc_fba.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(True)

    # model
    model.setId('diauxic_fba')
    model.setName('FBA submodel (diauxic_fba)')
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)
    add_generic_info(model)

    # Compartments
    compartments = [
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor', spatialDimension=3),
    ]
    mc.create_objects(model, compartments)

    # Species
    species = [
        # internal
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='O2', name="oxygen", value=0.21, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
    ]
    mc.create_objects(model, species)

    parameters = [
        # default bounds
        mc.Parameter(sid="zero", name="zero bound", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_default", name="default lower bound", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_default", name="default upper bound", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),

        # values of all exchange flux bounds can be overwritten from the outside
        mc.Parameter(sid="lb_EX_Ac", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_Ac", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_EX_Glcxt", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_Glcxt", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_EX_O2", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_O2", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_EX_X", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_X", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
    ]
    mc.create_objects(model, parameters)

    # reactions: exchange reactions (this species can be changed by the FBA)
    r_EX_O2 = mc.create_reaction(model, rid="EX_O2", name="O2 exchange", reversible=False,
                            reactants={"O2": 1}, products={}, compartment='bioreactor', sboTerm="SBO:0000627")
    r_EX_Glcxt = mc.create_reaction(model, rid="EX_Glcxt", name="Glcxt exchange", reversible=False,
                            reactants={"Glcxt": 1}, products={}, compartment='bioreactor', sboTerm="SBO:0000627")
    r_EX_Ac = mc.create_reaction(model, rid="EX_Ac", name="Ac exchange", reversible=True,
                            reactants={"Ac": 1}, products={}, compartment='bioreactor', sboTerm="SBO:0000627")
    r_EX_X = mc.create_reaction(model, rid="EX_X", name="biomass exchange", reversible=False,
                            reactants={"X": 1}, products={}, compartment='bioreactor', sboTerm="SBO:0000627")

    # flux bounds: exchange fluxes
    mc.set_flux_bounds(r_EX_Ac, lb="lb_EX_Ac", ub="ub_EX_Ac")
    mc.set_flux_bounds(r_EX_Glcxt, lb="lb_EX_Glcxt", ub="ub_EX_Glcxt")
    mc.set_flux_bounds(r_EX_O2, lb="lb_EX_O2", ub="ub_EX_O2")
    mc.set_flux_bounds(r_EX_X, lb="lb_EX_X", ub="ub_EX_X")

    # reactions: internal reactions
    r_v1 = mc.create_reaction(model, rid="v1", name="v1 (39.43 Ac + 35 O2 -> X)", reversible=False,
                               reactants={"Ac": 39.43, "O2": 35}, products={"X": 1}, compartment='bioreactor')
    r_v2 = mc.create_reaction(model, rid="v2", name="v2 (9.46 Glcxt + 12.92 O2 -> X)", reversible=False,
                              reactants={"Glcxt": 9.46, "O2": 12.92}, products={"X": 1}, compartment='bioreactor')
    r_v3 = mc.create_reaction(model, rid="v3", name="v3 (9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X)", reversible=False,
                              reactants={"Glcxt": 9.84, "O2": 12.73}, products={"Ac": 1.24, "X": 1}, compartment='bioreactor')
    r_v4 = mc.create_reaction(model, rid="v4", name="v4 (19.23 Glcxt -> 12.12 Ac + X)", reversible=False,
                              reactants={"Glcxt": 19.23}, products={"Ac": 12.12, "X": 1}, compartment='bioreactor')

    # flux bounds: internal fluxes
    mc.set_flux_bounds(r_v1, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r_v2, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r_v3, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r_v4, lb="zero", ub="ub_default")

    # objective function
    mc.create_objective(mplugin, oid="biomass_max", otype="maximize",
                        fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0})

    # ports: compartments
    # comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)

    # ports: species in exchange reactions
    # comp._create_port(model, pid="Ac_port", idRef="Ac", portType=comp.PORT_TYPE_PORT)
    # comp._create_port(model, pid="Glcxt_port", idRef="Glcxt", portType=comp.PORT_TYPE_PORT)
    # comp._create_port(model, pid="O2_port", idRef="O2", portType=comp.PORT_TYPE_PORT)
    # comp._create_port(model, pid="X_port", idRef="X", portType=comp.PORT_TYPE_PORT)

    # exchange reactions
    comp._create_port(model, pid="EX_Ac_port", idRef="EX_Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="EX_Glcxt_port", idRef="EX_Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="EX_O2_port", idRef="EX_O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="EX_X_port", idRef="EX_X", portType=comp.PORT_TYPE_PORT)

    # ports: bounds for exchange reactions (set by species concentrations)
    comp._create_port(model, pid="lb_EX_Ac_port", idRef="lb_EX_Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_Glcxt_port", idRef="lb_EX_Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_O2_port", idRef="lb_EX_O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_X_port", idRef="lb_EX_X", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_Ac_port", idRef="ub_EX_Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_Glcxt_port", idRef="ub_EX_Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_O2_port", idRef="ub_EX_O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_X_port", idRef="ub_EX_X", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_sbml(doc_fba, filepath=os.path.join(directory, sbml_file), validate=True)


def bounds_model(sbml_file, directory):
    """"
    Submodel for dynamically calculating the flux bounds.

    The dynamically changing flux bounds are the input to the
    FBA model.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("diauxic_bounds")
    model.setName("ODE bounds submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    objects = [

        # definition of min and max
        mc.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='minimum of arguments'),
        mc.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='maximum of arguments'),

        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                       spatialDimension=3),
        # species
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='O2', name="oxygen", value=0.21, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        # hardcoded time step for the update of the bounds
        mc.Parameter(sid='dt', value=DT_SIM, unit=UNIT_TIME, name='fba timestep', constant=True, sboTerm="SBO:0000346"),


        # default bounds
        mc.Parameter(sid="zero", name="zero bound", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_default", name="default lower bound", value=-1000.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_default", name="default upper bound", value=1000.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),

        # values of all exchange flux bounds can be overwritten from the outside
        mc.Parameter(sid="lb_EX_Ac", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_Ac", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_EX_Glcxt", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False,
                     sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_Glcxt", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False,
                     sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_EX_O2", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_O2", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_EX_X", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_EX_X", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),

        # kinetic lower bounds
        mc.Parameter(sid="lb_kin_EX_Glcxt", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_kin_EX_O2", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000612"),

        # parameters for kinetic bounds
        mc.Parameter(sid='Vmax_EX_O2', value=15, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid='Vmax_EX_Glcxt', value=10, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid='Km_EX_Glcxt', value=0.015, unit=UNIT_CONCENTRATION, name="Km_vGlcxt", constant=True),

        # kinetic bounds (unintuitive direction due to the identical concentrations in bioreactor and model)
        mc.AssignmentRule(sid="lb_kin_EX_Glcxt", value="-Vmax_EX_Glcxt* Glcxt/(Km_EX_Glcxt + Glcxt)"),
        mc.AssignmentRule(sid="lb_kin_EX_O2", value="-Vmax_EX_O2"),

        # exchange reaction bounds
        # amount limitation in export (lower bound)
        mc.AssignmentRule(sid="lb_EX_Ac", value="max(lb_default, -Ac*bioreactor/dt)"),
        mc.AssignmentRule(sid="lb_EX_Glcxt", value="max(lb_kin_EX_Glcxt, -Glcxt*bioreactor/dt)"),
        mc.AssignmentRule(sid="lb_EX_O2", value="max(lb_kin_EX_O2, -O2*bioreactor/dt)"),
        mc.AssignmentRule(sid="lb_EX_X", value="max(lb_default, -X*bioreactor/dt)"),

    ]
    mc.create_objects(model, objects)

    # ports
    comp._create_port(model, pid="dt_port", idRef="dt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)
    # species
    comp._create_port(model, pid="Glcxt_port", idRef="Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="Ac_port", idRef="Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="O2_port", idRef="O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="X_port", idRef="X", portType=comp.PORT_TYPE_PORT)

    # exchange bounds
    comp._create_port(model, pid="lb_EX_Ac_port", idRef="lb_EX_Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_Ac_port", idRef="ub_EX_Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_Glcxt_port", idRef="lb_EX_Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_Glcxt_port", idRef="ub_EX_Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_O2_port", idRef="lb_EX_O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_O2_port", idRef="ub_EX_O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_X_port", idRef="lb_EX_X", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_X_port", idRef="ub_EX_X", portType=comp.PORT_TYPE_PORT)

    sbml_io.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)


####################################################
# ODE species update
####################################################
def update_model(sbml_file, directory):
    """
        Submodel for dynamically updating the metabolite count/concentration.
        This updates the ode model based on the FBA fluxes.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()
    model.setId("diauxic_update")
    model.setName("ODE metabolite update")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    objects = [
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                       spatialDimension=3),
        # species
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='O2', name="oxygen", value=0.21, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        # exchange reaction fluxes
        mc.Parameter(sid="EX_Ac", name="Ac exchange (FBA flux)", value=1.0, constant=True, unit=UNIT_FLUX),
        mc.Parameter(sid="EX_Glcxt", name="Glcxt exchange (FBA flux)", value=1.0, constant=True, unit=UNIT_FLUX),
        mc.Parameter(sid="EX_O2", name="O2 exchange (FBA flux)", value=1.0, constant=True, unit=UNIT_FLUX),
        mc.Parameter(sid="EX_X", name="X exchange (FBA flux)", value=1.0, constant=True, unit=UNIT_FLUX),

    ]
    mc.create_objects(model, objects)

    # FIXME: multiply by X (fluxes per g weight, actual fluxes consequence of biomass)
    mc.create_reaction(model, rid="update_Glcxt", compartment="bioreactor", sboTerm="SBO:0000631",
                       reactants={"Glcxt": 1}, products={}, modifiers=["X"],
                       formula="-EX_Glcxt * X * 1 l_per_mmol")
    mc.create_reaction(model, rid="update_Ac", compartment="bioreactor", sboTerm="SBO:0000631",
                       reactants={"Ac": 1}, products={}, modifiers=["X"],
                       formula="-EX_Ac * X * 1 l_per_mmol")
    mc.create_reaction(model, rid="update_O2", compartment="bioreactor", sboTerm="SBO:0000631",
                       reactants={"O2": 1}, products={}, modifiers=["X"],
                       formula="-EX_O2 * X * 1 l_per_mmol")
    mc.create_reaction(model, rid="update_X", compartment="bioreactor", sboTerm="SBO:0000631",
                       reactants={"X": 1}, products={}, modifiers=["X"],
                       formula="-EX_X * X * 1 l_per_mmol")

    # ports
    comp._create_port(model, pid="EX_Glcxt_port", idRef="EX_Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="EX_Ac_port", idRef="EX_Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="EX_O2_port", idRef="EX_O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="EX_X_port", idRef="EX_X", portType=comp.PORT_TYPE_PORT)

    comp._create_port(model, pid="Glcxt_port", idRef="Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="Ac_port", idRef="Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="O2_port", idRef="O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="X_port", idRef="X", portType=comp.PORT_TYPE_PORT)

    comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)



def top_model(sbml_file, directory, emds):
    """
    Create diauxic comp model.
    Test script for working with the comp extension in SBML.

    One model composition combines all the kinetic models,
    in addition the higher level comp model is created which combines everything (i.e. the FBA & ODE models).
    For the simulation of the full combined model the tools have to figure out the subparts which are
    simulated with which simulation environment.
    Creates the full comp model as combination of FBA and comp models.

    The submodels must already exist in the given directory

    connections
    ------------
    [1] flux bounds
    kinetic reaction bounds => replace the FBA bounds
    comp_ode.submodel_bounds__ub_R1 => fba_R1.upper_bound

    [2] reaction rates (fluxes)
    FBA flux (all reactions) => replaces Reaction flux in kinetic model

    ** FBA **
    <listOfParameters>
        <parameter id="ub_R1" name="ub R1" value="1" units="item_per_s" constant="false"/>
        <parameter id="lb" name="lower bound" value="0" units="item_per_s" constant="true"/>
        <parameter id="ub" name="upper bound" value="1000" units="item_per_s" constant="true"/>
        <parameter id="v_R1" name="R1 flux" value="0" units="item_per_s" constant="false"/>
        <parameter id="v_R2" name="R2 flux" value="0" units="item_per_s" constant="false"/>
        <parameter id="v_R3" name="R3 flux" value="0" units="item_per_s" constant="false"/>
    </listOfParameters>
    """
    # Necessary to change into directory with submodel files
    working_dir = os.getcwd()
    os.chdir(directory)

    sbmlns = SBMLNamespaces(3, 1, "comp", 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    doc.setPackageRequired("fbc", False)

    mdoc = doc.getPlugin("comp")

    # create listOfExternalModelDefinitions
    emd_fba = comp.create_ExternalModelDefinition(mdoc, "diauxic_fba", source=emds["diauxic_fba"])
    emd_bounds = comp.create_ExternalModelDefinition(mdoc, "diauxic_bounds", source=emds["diauxic_bounds"])
    emd_update = comp.create_ExternalModelDefinition(mdoc, "diauxic_update", source=emds["diauxic_update"])

    # create models and submodels
    model = doc.createModel()
    model.setId("diauxic_top")
    model.setName("Top level model")
    add_generic_info(model)
    mplugin = model.getPlugin("comp")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    # add submodel which references the external model definition
    comp.add_submodel_from_emd(mplugin, submodel_id="fba", emd=emd_fba)
    comp.add_submodel_from_emd(mplugin, submodel_id="bounds", emd=emd_bounds)
    comp.add_submodel_from_emd(mplugin, submodel_id="update", emd=emd_update)

    # Compartments
    mc.create_objects(model, [
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                       spatialDimension=3),
    ])

    # Species
    # replaced species
    # (fba species are not replaced, because they need their boundaryConditions for the FBA,
    #    and do not depend on the actual concentrations)
    mc.create_objects(model, [
        # internal
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='O2', name="oxygen", value=0.21, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        # dummy species for dummy reactions (empty set)
        mc.Species(sid='dummy_S', name="dummy_S", value=0, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor", sboTerm="SBO:0000291"),
    ])

    # Parameters
    parameters = [
        # hardcoded time step for the update of the bounds
        mc.Parameter(sid='dt', value=DT_SIM, unit='h', name='fba timestep', constant=True, sboTerm="SBO:0000346"),

        # biomass conversion factor
        mc.Parameter(sid="Y", name="biomass [g_per_l]", value=1.0, unit="g_per_l"),

        mc.Parameter(sid="O2_ref", name="O2 reference", value=0.21, unit=UNIT_CONCENTRATION),
        mc.Parameter(sid="kLa", name="O2 mass transfer", value=7.5, unit='per_h'),
        # fluxes from fba (rate of reaction)
        mc.Parameter(sid="EX_Glcxt", value=1.0, constant=True, unit=UNIT_FLUX, sboTerm="SBO:0000612"),
        mc.Parameter(sid="EX_Ac", value=1.0, constant=True, unit=UNIT_FLUX, sboTerm="SBO:0000612"),
        mc.Parameter(sid="EX_O2", value=1.0, constant=True, unit=UNIT_FLUX, sboTerm="SBO:0000612"),
        mc.Parameter(sid="EX_X", value=1.0, constant=True, unit=UNIT_FLUX, sboTerm="SBO:0000612"),
    ]
    # exchange flux bounds
    for ex_rid in ['EX_Ac', 'EX_Glcxt', 'EX_O2', 'EX_X']:
        for bound_type in ['lb', 'ub']:
            if bound_type == 'lb':
                value = LOWER_BOUND_DEFAULT
            elif bound_type == 'ub':
                value = UPPER_BOUND_DEFAULT
            parameters.append(
                # lb_vGlcxt
                mc.Parameter(sid="{}_{}".format(bound_type, ex_rid), value=value, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625")
            )
    mc.create_objects(model, parameters)

    # Reactions
    # dummy reaction (pseudoreaction)
    mc.create_reaction(model, rid="dummy_EX_Glcxt", name="EX_Glcxt dummy", reversible=False,
                       reactants={}, products={"dummy_S": 1}, compartment="bioreactor", sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="dummy_EX_O2", name="EX_O2 dummy", reversible=False,
                       reactants={}, products={"dummy_S": 1}, compartment="bioreactor", sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="dummy_EX_Ac", name="EX_Ac dummy", reversible=False,
                       reactants={}, products={"dummy_S": 1}, compartment="bioreactor", sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="dummy_EX_X", name="EX_X dummy", reversible=False,
                       reactants={}, products={"dummy_S": 1}, compartment="bioreactor", sboTerm="SBO:0000631")

    # oxygen transfer reaction
    mc.create_reaction(model, rid="vO2_transfer", name="oxygen transfer", reversible=True,
                       reactants={}, products={"O2": 1}, formula="kLa * (O2_ref-O2) * bioreactor", compartment="bioreactor")


    # AssignmentRules
    # This are the important assignment rules which update the fluxes
    # must be of the form: pid = rid
    mc.create_objects(model, [
        mc.AssignmentRule("EX_Glcxt", value="dummy_EX_Glcxt"),
        mc.AssignmentRule("EX_Ac", value="dummy_EX_Ac"),
        mc.AssignmentRule("EX_O2", value="dummy_EX_O2"),
        mc.AssignmentRule("EX_X", value="dummy_EX_X"),

        # biomass conversion factor
        mc.AssignmentRule('Y', value='1 g_per_mmol * X'),
    ])

    # --- replacements ---
    # dt
    comp._create_port(model, pid="dt_port", idRef="dt", portType=comp.PORT_TYPE_PORT)

    # compartments
    comp.replace_elements(model, 'bioreactor', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={
                                             'update': ['bioreactor_port'],
                                             'bounds': ['bioreactor_port']})

    # species
    comp.replace_elements(model, 'Glcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={
                                             'update': ['Glcxt_port'],
                                             'bounds': ['Glcxt_port']})
    comp.replace_elements(model, 'O2', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={
                                             'update': ['O2_port'],
                                             'bounds': ['O2_port']})
    comp.replace_elements(model, 'Ac', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={
                                             'update': ['Ac_port'],
                                             'bounds': ['Ac_port']})
    comp.replace_elements(model, 'X', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={
                                             'update': ['X_port'],
                                             'bounds': ['X_port']})
    # exchange bounds
    for bound_id in [
        'lb_EX_Ac', 'ub_EX_Ac',
        'lb_EX_Glcxt', 'ub_EX_Glcxt',
        'lb_EX_O2', 'ub_EX_O2',
        'lb_EX_X', 'ub_EX_X']:
        comp.replace_elements(model, bound_id, ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['{}_port'.format(bound_id)], 'fba': ['{}_port'.format(bound_id)]})

    # dt
    comp.replace_elements(model, 'dt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['dt_port']})

    # fluxes
    comp.replace_elements(model, 'EX_Glcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['EX_Glcxt_port']})
    comp.replace_elements(model, 'EX_Ac', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['EX_Ac_port']})
    comp.replace_elements(model, 'EX_O2', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['EX_O2_port']})
    comp.replace_elements(model, 'EX_X', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['EX_X_port']})

    # FBA: replace reaction by fba reaction
    comp.replaced_by(model, 'dummy_EX_Glcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="EX_Glcxt_port")
    comp.replaced_by(model, 'dummy_EX_Ac', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="EX_Ac_port")
    comp.replaced_by(model, 'dummy_EX_O2', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="EX_O2_port")
    comp.replaced_by(model, 'dummy_EX_X', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="EX_X_port")

    # replace units
    for uid in ['h', 'g', 'm', 'm2', 'l', 'mmol', 'mmol_per_h', 'mmol_per_l', 'g_per_l', 'g_per_mmol']:
        comp.replace_element_in_submodels(model, uid, ref_type=comp.SBASE_REF_TYPE_UNIT,
                                          submodels=['bounds', 'fba', 'update'])

    # write SBML file
    sbml_io.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)
    # change back into working dir
    os.chdir(working_dir)


def create_models():
    """ Create all models.

    :return:
    """
    directory = pjoin(out_dir, 'v{}'.format(version))
    if not os.path.exists(directory):
        print('Create directory: {}'.format(directory))
        os.mkdir(directory)

    # create sbml
    fba_model(fba_file, directory)
    bounds_model(bounds_file, directory)
    update_model(update_file, directory)


    emds = {
        "diauxic_fba": fba_file,
        "diauxic_bounds": bounds_file,
        "diauxic_update": update_file,
    }

    # flatten top model
    top_model(top_file, directory, emds)
    comp.flattenSBMLFile(sbml_path=pjoin(directory, top_file),
                         output_path=pjoin(directory, flattened_file))

    # reported bug in writing comp model
    # TODO: test this as soon as bug is fixed
    if False:
        # remove external model definitions
        doc_top = libsbml.readSBMLFromFile(pjoin(directory, top_file))
        if doc_top is None:
            logging.error('SBML file could not be read:', top_file)

        # valid during creation
        doc_top_noemd = comp.flattenExternalModelDefinitions(doc_top, validate=True)
        from sbmlutils import validation
        validation.check_doc(doc_top_noemd)

        # not valid during writing
        sbml_io.write_and_check(doc_top_noemd, pjoin(directory, top_noemd_file))


        # comp.flattenSBMLFile(sbml_path=pjoin(directory, top_noemd_file),
        #                     output_path=pjoin(directory, flattened_noemd_file))

    # create reports
    sbml_paths = [pjoin(directory, fname) for fname in
                  # [fba_file, bounds_file, update_file, top_file, flattened_file]]
                  [fba_file, bounds_file, update_file, top_file, flattened_file]]
    sbmlreport.create_sbml_reports(sbml_paths, directory, validate=False)


if __name__ == "__main__":
    create_models()
