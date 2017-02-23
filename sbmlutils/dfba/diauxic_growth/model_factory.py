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

from libsbml import *

import sbmlutils.sbmlio as sbml_io
import sbmlutils.annotation as sbml_annotation
from sbmlutils import comp
from sbmlutils import factory as mc
from sbmlutils.report import sbmlreport

XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################
version = 1
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Diauxic Growth Model</h1>
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
""")
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

    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_l', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('g_per_l', [(UNIT_KIND_GRAM, 1.0),
                        (UNIT_KIND_LITRE, -1.0)]),

    mc.Unit('mmol', [(UNIT_KIND_MOLE, 1.0, -3, 1.0)]),
    mc.Unit('per_g', [(UNIT_KIND_GRAM, -1.0)]),
    mc.Unit('g_per_mmol', [(UNIT_KIND_GRAM, 1.0),
                           (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
    mc.Unit('mmol_per_h', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_hg', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_GRAM, -1.0)]),
    mc.Unit('mmol_per_lh', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_LITRE, -1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('g_per_lh', [(UNIT_KIND_GRAM, 1.0),
                         (UNIT_KIND_LITRE, -1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
]

UNIT_AMOUNT = 'mmol'
UNIT_AREA = 'm2'
UNIT_VOLUME ='l'
UNIT_CONCENTRATION = 'mmol_per_l'
UNIT_FLUX = 'mmol_per_hg'


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

####################################################
# FBA submodel
####################################################
def create_fba(sbml_file, directory):
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
    # TODO: annotation of boundary fluxes
    species = [
        # internal
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='O2', name="oxygen", value=0.21, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
    ]
    mc.create_objects(model, species)

    parameters = [
        # bounds
        mc.Parameter(sid="lb_irrev", name="lower bound", value=0.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb", name="lower bound", value=-1000.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub", name="upper bound", value=1000.0, unit=UNIT_FLUX, constant=True),

        mc.Parameter(sid="ub_vO2", name="ub vO2", value=15.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub_vGlcxt", name="ub vGlcxt", value=10.0, unit=UNIT_FLUX, constant=False),
    ]
    mc.create_objects(model, parameters)

    # reactions with constant flux
    r_vO2 = mc.create_reaction(model, rid="vO2", name="O2 import (vO2)", reversible=False,
                            reactants={}, products={"O2": 1}, compartment='bioreactor')
    r_vGlcxt = mc.create_reaction(model, rid="vGlcxt", name="Glcxt import (vGlcxt)", reversible=False,
                            reactants={}, products={"Glcxt": 1}, compartment='bioreactor')
    r_vAc = mc.create_reaction(model, rid="vAc", name="Ac import (vAc)", reversible=True,
                            reactants={}, products={"Ac": 1}, compartment='bioreactor')
    r_vX = mc.create_reaction(model, rid="vX", name="biomass generation (vX)", reversible=False,
                            reactants={"X": 1}, products={}, compartment='bioreactor')

    r_v1 = mc.create_reaction(model, rid="v1", name="v1", reversible=False,
                               reactants={"Ac": 39.43, "O2": 35}, products={"X": 1}, compartment='bioreactor')
    r_v2 = mc.create_reaction(model, rid="v2", name="v2", reversible=False,
                              reactants={"Glcxt": 9.46, "O2": 12.92}, products={"X": 1}, compartment='bioreactor')
    r_v3 = mc.create_reaction(model, rid="v3", name="v3", reversible=False,
                              reactants={"Glcxt": 9.84, "O2": 12.73}, products={"Ac": 1.24, "X": 1}, compartment='bioreactor')
    r_v4 = mc.create_reaction(model, rid="v4", name="v4", reversible=False,
                              reactants={"Glcxt": 19.23}, products={"Ac": 12.12, "X": 1}, compartment='bioreactor')

    # flux bounds
    mc.set_flux_bounds(r_vO2, lb="lb_irrev", ub="ub_vO2")
    mc.set_flux_bounds(r_vGlcxt, lb="lb_irrev", ub="ub_vGlcxt")
    mc.set_flux_bounds(r_vAc, lb="lb", ub="ub")

    mc.set_flux_bounds(r_vX, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v1, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v2, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v3, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v4, lb="lb_irrev", ub="ub")


    # objective function
    mc.create_objective(mplugin, oid="biomass_max", otype="maximize",
                        fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0})

    # create ports
    comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="Glcxt_port", idRef="Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="O2_port", idRef="O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="Ac_port", idRef="Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="X_port", idRef="X", portType=comp.PORT_TYPE_PORT)

    # input bounds
    comp._create_port(model, pid="ub_vGlcxt_port", idRef="ub_vGlcxt", portType=comp.PORT_TYPE_PORT)
    # output fluxes
    comp._create_port(model, pid="vGlcxt_port", idRef="vGlcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="vAc_port", idRef="vAc", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="vO2_port", idRef="vO2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="vX_port", idRef="vX", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc_fba, os.path.join(directory, sbml_file))


####################################################
# ODE flux bounds
####################################################
def create_bounds(sbml_file, directory):
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
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                       spatialDimension=3),
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        mc.Parameter(sid='ub_vGlcxt', value=15, unit=UNIT_FLUX, name='ub_vGlcxt', constant=False),
        mc.Parameter(sid='Vmax_vGlcxt', value=15, unit=UNIT_FLUX, name="Vmax_vGlcxt", constant=True),
        mc.Parameter(sid='Km_vGlcxt', value=0.015, unit="mmol_per_l", name="Km_vGlcxt", constant=True),

        mc.AssignmentRule(sid="ub_vGlcxt", value="Vmax_vGlcxt* Glcxt/(Km_vGlcxt + Glcxt)"),
        # # driving function to test the bound update
        # mc.AssignmentRule(sid="Glcxt", value="5.0 mM + 5.0 mM * sin(time/1 h)")
    ]
    mc.create_objects(model, objects)

    # ports
    comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="Glcxt_port", idRef="Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_vGlcxt_port", idRef="ub_vGlcxt", portType=comp.PORT_TYPE_PORT)

    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))


####################################################
# ODE species update
####################################################
def create_update(sbml_file, directory):
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

    # Compartments
    objects = [
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                       spatialDimension=3),
        # internal
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        mc.Species(sid='O2', name="oxygen", value=0.21, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        # biomass conversion factor
        mc.Parameter(sid="Y", name="biomass [g_per_l]", value=1.0, unit="g_per_l"),
        mc.AssignmentRule('Y', '1 g_per_mmol * X'),

        # fluxes from fba
        mc.Parameter(sid="vGlcxt", name="vGlcxt (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vAc", name="vAc (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vO2", name="vO2 (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vX", name="vX (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        # Michaelis-Menten kinetics for flux updates
        mc.Parameter(sid="Km_vFBA", name="Km_vFBA", value=0.02, constant=True, unit="mmol_per_l"),

    ]
    mc.create_objects(model, objects)

    # kinetic reaction using FBA flux as upper bound
    # Michaelis-Menten-Terms for restriction
    mc.create_reaction(model, rid="update_Glcxt", reversible=False,
                       reactants={"Glcxt": 1}, products={}, formula="(vGlcxt*Y*bioreactor) * Glcxt/(Km_vFBA + Glcxt)", compartment="bioreactor")
    mc.create_reaction(model, rid="update_Ac", reversible=False,
                       reactants={"Ac": 1}, products={}, formula="(vAc*Y*bioreactor) * Ac/(Km_vFBA + Ac)", compartment="bioreactor")
    mc.create_reaction(model, rid="update_O2", reversible=False,
                       reactants={"O2": 1}, products={}, formula="(vO2*Y*bioreactor) * O2/(Km_vFBA + O2)", compartment="bioreactor")
    mc.create_reaction(model, rid="update_X", reversible=False,
                       reactants={}, products={"X": 1}, formula="(vX*Y*bioreactor)", compartment="bioreactor")

    # ports
    comp._create_port(model, pid="vGlcxt_port", idRef="vGlcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="vAc_port", idRef="vAc", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="vO2_port", idRef="vO2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="vX_port", idRef="vX", portType=comp.PORT_TYPE_PORT)

    comp._create_port(model, pid="Glcxt_port", idRef="Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="Ac_port", idRef="Ac", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="O2_port", idRef="O2", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="X_port", idRef="X", portType=comp.PORT_TYPE_PORT)

    comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))


####################################################
# comp model
####################################################


def create_top_level_model(sbml_file, directory):
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
    emd_fba = comp.create_ExternalModelDefinition(mdoc, "diauxic_fba", sbml_file=fba_file)
    emd_bounds = comp.create_ExternalModelDefinition(mdoc, "diauxic_bounds", sbml_file=bounds_file)
    emd_update = comp.create_ExternalModelDefinition(mdoc, "diauxic_update", sbml_file=update_file)

    # create models and submodels
    model = doc.createModel()
    model.setId("diauxic_comp")
    model.setName("Top level model")
    add_generic_info(model)
    mplugin = model.getPlugin("comp")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    # add submodel which references the external model definition
    comp.add_submodel_from_emd(mplugin, submodel_sid="bounds", emd=emd_bounds)
    comp.add_submodel_from_emd(mplugin, submodel_sid="fba", emd=emd_fba)
    comp.add_submodel_from_emd(mplugin, submodel_sid="update", emd=emd_update)

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

        # dummy species for dummy reactions
        mc.Species(sid='S_dummy', name="S_dummy", value=0, unit='mmol_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
    ])

    # Parameters
    mc.create_objects(model, [
        # bounds
        mc.Parameter(sid="ub_vGlcxt", name="ub vGlcxt", value=10.0, unit="mmol_per_hg", constant=False),

        # fluxes from fba
        mc.Parameter(sid="vGlcxt", name="vGlcxt (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vAc", name="vAc (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vO2", name="vO2 (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vX", name="vX (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),

    ])

    # Reactions
    # dummy reaction in top model
    mc.create_reaction(model, rid="dummy_vGlcxt", name="vGlcxt dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    mc.create_reaction(model, rid="dummy_vO2", name="vO2 dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    mc.create_reaction(model, rid="dummy_vAc", name="vAc dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    mc.create_reaction(model, rid="dummy_vX", name="vX dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    # AssignmentRules
    mc.create_objects(model, [
        mc.AssignmentRule(sid="vGlcxt", value="1 per_g * dummy_vGlcxt"),
        mc.AssignmentRule(sid="vAc", value="1 per_g * dummy_vAc"),
        mc.AssignmentRule(sid="vO2", value="1 per_g * dummy_vO2"),
        mc.AssignmentRule(sid="vX", value="1 per_g * dummy_vX"),
    ])

    # --- replacements ---

    # compartments
    comp.replace_elements(model, 'bioreactor', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['bioreactor_port'],
                                             'update': ['bioreactor_port'],
                                             'bounds': ['bioreactor_port']})

    # replace species
    comp.replace_elements(model, 'Glcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['Glcxt_port'],
                                             'update': ['Glcxt_port'],
                                             'bounds': ['Glcxt_port']})
    comp.replace_elements(model, 'O2', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['O2_port'],
                                             'update': ['O2_port']})
    comp.replace_elements(model, 'Ac', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['Ac_port'],
                                             'update': ['Ac_port']})
    comp.replace_elements(model, 'X', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['X_port'],
                                             'update': ['X_port']})
    # bounds
    comp.replace_elements(model, 'ub_vGlcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['ub_vGlcxt_port'], 'fba': ['ub_vGlcxt_port']})
    # fluxes
    comp.replace_elements(model, 'vGlcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vGlcxt_port']})
    comp.replace_elements(model, 'vAc', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vAc_port']})
    comp.replace_elements(model, 'vO2', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vO2_port']})
    comp.replace_elements(model, 'vX', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vX_port']})


    # FBA: replace reaction by fba reaction
    comp.replaced_by(model, 'dummy_vGlcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vGlcxt_port")
    comp.replaced_by(model, 'dummy_vAc', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vAc_port")
    comp.replaced_by(model, 'dummy_vO2', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vO2_port")
    comp.replaced_by(model, 'dummy_vX', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vX_port")

    # replace units
    # TODO
    # for uid in ['s', 'kg', 'm3', 'm2', 'mM', 'item_per_m3', 'm', 'per_s', 'item_per_s']:
    #    comp.replace_element_in_submodels(model, uid, ref_type=comp.SBASE_REF_TYPE_UNIT,
    #                                      submodels=['bounds', 'fba', 'update', 'ode'])

    # write SBML file
    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))
    # change back into working dir
    os.chdir(working_dir)


########################################################################################################################
if __name__ == "__main__":
    from dgsettings import fba_file, bounds_file, update_file, top_file, flattened_file, out_dir
    import os

    # create sbml
    create_fba(fba_file, out_dir)
    create_bounds(bounds_file, out_dir)
    create_update(update_file, out_dir)
    create_top_level_model(top_file, out_dir)

    # flatten top model
    comp.flattenSBMLFile(sbml_path=os.path.join(out_dir, top_file),
                         output_path=os.path.join(out_dir, flattened_file))

    # create reports
    for fname in [fba_file, bounds_file, update_file, top_file, flattened_file]:
        sbmlreport.create_sbml_report(os.path.join(out_dir, fname), out_dir, validate=False)
