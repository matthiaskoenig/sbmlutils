# -*- coding=utf-8 -*-
"""
Creating E.coli core model.
"""
from __future__ import print_function, absolute_import
import os
from os.path import join as pjoin

import libsbml
from libsbml import UNIT_KIND_SECOND, UNIT_KIND_GRAM, UNIT_KIND_LITRE, UNIT_KIND_METRE, UNIT_KIND_MOLE

from sbmlutils import sbmlio
from sbmlutils import comp
from sbmlutils import factory as mc
from sbmlutils.report import sbmlreport

from sbmlutils.dfba import builder
from sbmlutils.dfba import utils
from sbmlutils.dfba.diauxic_growth.dgsettings import fba_file, bounds_file, update_file, top_file, flattened_file

libsbml.XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################
version = 9
DT_SIM = 0.1
notes = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>E.coli core DFBA model</h1>
    <p><strong>Model version: {}</strong></p>
    <p>{}<p>

      <body xmlns="http://www.w3.org/1999/xhtml" style="margin:0 auto; width: 970px; font-size: 14px; height: 100%; color: #444444; font-family:Helvetica, sans-serif;">
      <h2>Description</h2>
      <div class="dc:description">
        <p>This is a metabolism model of Escherichia coli str. K-12 substr. MG1655 in
        <a href="http://sbml.org" target="_blank" title="Access the definition of the SBML file format.">SBML</a>&#160;format.</p>
      </div>
      <div class="dc:provenance">The content of this model has been carefully created in a manual research effort. This file has been exported from the software
      <a href="http://dx.doi.org/10.1186/1752-0509-7-74" title="Access publication about COBRApy." target="_blank">COBRApy</a>&#160;and further processed with the
      <a href="http://dx.doi.org/10.1093/bioinformatics/btv341" title="Access publication about JSBML." target="_blank">JSBML</a>-based
      <a href="http://github.com/SBRG/ModelPolisher/" target="_blank" title="Access ModelPolisher on Github">ModelPolisher</a>&#160;application.</div>
      <div class="dc:publisher">This file has been produced by the
      <a href="http://systemsbiology.ucsd.edu" title="Website of the Systems Biology Research Group" target="_blank">Systems Biology Research Group</a>&#160;using
      <a href="http://bigg.ucsd.edu" title="Access BiGG Models knowledge-base." target="_blank">BiGG Models knowledge-base</a>&#160;version of Nov 21, 2016, where it is currently hosted and
      identified by:
      <a href="http://identifiers.org/bigg.model/e_coli_core" title="Access to this model via BiGG Models knowledge-base." target="_blank">e_coli_core</a>.</div>
      <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2016 The Regents of the University of California.</div>
      <div class="dc:license">
        <p>Redistribution and use of any part of this model from BiGG Models knowledge-base, with or without modification, are permitted provided that the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions and the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.</p>
        <p>For specific licensing terms about this particular model and regulations of commercial use, see
        <a href="http://identifiers.org/bigg.model/e_coli_core" title="Access to this model via BiGG Models knowledge-base." target="_blank">this model in BiGG Models knowledge-base</a>.</p>
      </div>
      <h2>References</h2>When using content from BiGG Models knowledge-base in your research works, please cite
      <dl>
        <dt>King ZA, Lu JS, Dräger A, Miller PC, Federowicz S, Lerman JA, Ebrahim A, Palsson BO, and&#160;Lewis NE. (2015).
        <dd>BiGG Models: A platform for integrating, standardizing, and sharing genome-scale models.
        <i>Nucl Acids Res</i>.
        <a href="https://dx.doi.org/10.1093/nar/gkv1049" target="_blank" title="Access the publication about BiGG Models knowledge-base">doi:10.1093/nar/gkv1049</a></dd></dt>
      </dl>
      </body>
""".format(version, '{}')

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


########################################################################################################
def fba_model(sbml_file, directory):
    """ Create FBA submodel.

    FBA submodel in sbml:fbc-version 2.
    """
    fba_notes = notes.format("""
    <h2>FBA submodel</h2>
    <p>DFBA fba submodel. Unbalanced metabolites are encoded via exchange fluxes.</p>
    """)
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 2)
    sbmlns.addPackageNamespace("comp", 1)

    doc_fba = libsbml.SBMLDocument(sbmlns)
    doc_fba.setPackageRequired("comp", True)
    doc_fba.getPlugin("comp")
    doc_fba.setPackageRequired("fbc", False)
    model = doc_fba.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(True)

    # model
    model.setId('diauxic_fba')
    model.setName('diauxic (FBA)')
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)
    utils.set_model_info(model, notes=fba_notes, creators=creators, units=units, main_units=main_units)

    objects = [
        # compartments
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

        # bounds
        mc.Parameter(sid="zero", name="zero bound", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_default", name="default upper bound", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX,
                     constant=True, sboTerm="SBO:0000612"),
    ]
    mc.create_objects(model, objects)

    # reactions
    r_v1 = mc.create_reaction(model, rid="v1", name="v1 (39.43 Ac + 35 O2 -> X)", reversible=False,
                              reactants={"Ac": 39.43, "O2": 35}, products={"X": 1}, compartment='bioreactor')
    r_v2 = mc.create_reaction(model, rid="v2", name="v2 (9.46 Glcxt + 12.92 O2 -> X)", reversible=False,
                              reactants={"Glcxt": 9.46, "O2": 12.92}, products={"X": 1}, compartment='bioreactor')
    r_v3 = mc.create_reaction(model, rid="v3", name="v3 (9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X)", reversible=False,
                              reactants={"Glcxt": 9.84, "O2": 12.73}, products={"Ac": 1.24, "X": 1},
                              compartment='bioreactor')
    r_v4 = mc.create_reaction(model, rid="v4", name="v4 (19.23 Glcxt -> 12.12 Ac + X)", reversible=False,
                              reactants={"Glcxt": 19.23}, products={"Ac": 12.12, "X": 1}, compartment='bioreactor')

    # flux bounds: internal fluxes
    mc.set_flux_bounds(r_v1, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r_v2, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r_v3, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r_v4, lb="zero", ub="ub_default")

    # reactions: exchange reactions (this species can be changed by the FBA)

    builder.create_exchange_reaction(model, species_id="Ac", flux_unit=UNIT_FLUX,
                                     exchange_type=builder.EXCHANGE)
    builder.create_exchange_reaction(model, species_id="Glcxt", flux_unit=UNIT_FLUX,
                                     exchange_type=builder.EXCHANGE_IMPORT)
    builder.create_exchange_reaction(model, species_id="O2", flux_unit=UNIT_FLUX,
                                     exchange_type=builder.EXCHANGE_IMPORT)
    builder.create_exchange_reaction(model, species_id="X", flux_unit=UNIT_FLUX,
                                     exchange_type=builder.EXCHANGE_EXPORT)


    # objective function
    mc.create_objective(mplugin, oid="biomass_max", otype="maximize",
                        fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0})

    # write SBML file
    sbmlio.write_sbml(doc_fba, filepath=pjoin(directory, sbml_file), validate=True)

    return doc_fba


def bounds_model(sbml_file, directory, doc_fba=None):
    """"
    Submodel for dynamically calculating the flux bounds.

    The dynamically changing flux bounds are the input to the
    FBA model.
    """
    # TODO: the bounds model should be created based on the FBA model (i.e. use the exchange reactions
    # to create the bounds info.

    bounds_notes = notes.format("""
    <h2>BOUNDS submodel</h2>
    <p>Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.</p>
    """)
    sbmlns = libsbml.SBMLNamespaces(3, 1, 'comp', 1)
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("diauxic_bounds")
    model.setName("diauxic (BOUNDS)")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    utils.set_model_info(model, notes=bounds_notes, creators=creators, units=units, main_units=main_units)

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
        mc.Parameter(sid="lb_default", name="default lower bound", value=-1000.0, unit=UNIT_FLUX, constant=True,
                     sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_default", name="default upper bound", value=1000.0, unit=UNIT_FLUX, constant=True,
                     sboTerm="SBO:0000612"),

        # values of all exchange flux bounds can be overwritten from the outside
        mc.Parameter(sid="lb_EX_Ac", value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
        mc.Parameter(sid="ub_EX_Ac", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
        mc.Parameter(sid="lb_EX_Glcxt", value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False,
                     sboTerm="SBO:0000625"),
        mc.Parameter(sid="ub_EX_Glcxt", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False,
                     sboTerm="SBO:0000625"),
        # FIXME: handle the reversibility of exchange reactions (i.e. ZERO_BOUNDS)
        mc.Parameter(sid="lb_EX_O2", value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
        mc.Parameter(sid="ub_EX_O2", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
        mc.Parameter(sid="lb_EX_X", value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
        mc.Parameter(sid="ub_EX_X", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),

        # kinetic lower bounds
        mc.Parameter(sid="lb_kin_EX_Glcxt", value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False,
                     sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_kin_EX_O2", value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False,
                     sboTerm="SBO:0000612"),

        # parameters for kinetic bounds
        mc.Parameter(sid='Vmax_EX_O2', value=15, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid='Vmax_EX_Glcxt', value=10, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid='Km_EX_Glcxt', value=0.015, unit=UNIT_CONCENTRATION, name="Km_vGlcxt", constant=True),

        # kinetic bounds (unintuitive direction due to the identical concentrations in bioreactor and model)
        mc.AssignmentRule(sid="lb_kin_EX_Glcxt", value="-Vmax_EX_Glcxt* Glcxt/(Km_EX_Glcxt + Glcxt)"),
        mc.AssignmentRule(sid="lb_kin_EX_O2", value="-Vmax_EX_O2"),

        # exchange reaction bounds
        # uptake bounds (lower bound)
        mc.AssignmentRule(sid="lb_EX_Ac", value="max(lb_default, -Ac/X*bioreactor/dt)"),
        mc.AssignmentRule(sid="lb_EX_Glcxt", value="max(lb_kin_EX_Glcxt, -Glcxt/X*bioreactor/dt)"),
        mc.AssignmentRule(sid="lb_EX_O2", value="max(lb_kin_EX_O2, -O2/X*bioreactor/dt)"),
        mc.AssignmentRule(sid="lb_EX_X", value="max(lb_default, -X/X*bioreactor/dt)"),

        # mc.AssignmentRule(sid="lb_EX_Ac", value="max(lb_default, -Ac*bioreactor/dt)"),
        # mc.AssignmentRule(sid="lb_EX_Glcxt", value="max(lb_kin_EX_Glcxt, -Glcxt*bioreactor/dt)"),
        # mc.AssignmentRule(sid="lb_EX_O2", value="max(lb_kin_EX_O2, -O2*bioreactor/dt)"),
        # mc.AssignmentRule(sid="lb_EX_X", value="max(lb_default, -X*bioreactor/dt)"),
    ]
    mc.create_objects(model, objects)

    # ports
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["dt",
                              "bioreactor",
                              "Ac", "Glcxt", "O2", "X",
                              "lb_EX_Ac", "lb_EX_Glcxt", "lb_EX_O2", "lb_EX_X",
                              "ub_EX_Ac", "ub_EX_Glcxt", "ub_EX_O2", "ub_EX_X",
                              ])

    # TODO: kinetic bounds missing

    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)


####################################################
# ODE species update
####################################################
def update_model(sbml_file, directory):
    """
        Submodel for dynamically updating the metabolite count/concentration.
        This updates the ode model based on the FBA fluxes.
    """
    update_notes = notes.format("""
        <h2>UPDATE submodel</h2>
        <p>Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.</p>
        """)
    sbmlns = libsbml.SBMLNamespaces(3, 1, 'comp', 1)
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()
    model.setId("diauxic_update")
    model.setName("diauxic (UPDATE)")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    utils.set_model_info(model, notes=update_notes, creators=creators, units=units, main_units=main_units)

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
        mc.Parameter(sid="EX_Ac", value=1.0, constant=True, unit=UNIT_FLUX),
        mc.Parameter(sid="EX_Glcxt", value=1.0, constant=True, unit=UNIT_FLUX),
        mc.Parameter(sid="EX_O2", value=1.0, constant=True, unit=UNIT_FLUX),
        mc.Parameter(sid="EX_X", value=1.0, constant=True, unit=UNIT_FLUX),
    ]
    mc.create_objects(model, objects)

    # FIXME: multiply by X (fluxes per g weight, actual fluxes consequence of biomass)
    builder.create_update_reaction(model, sid="Ac", modifiers=["X"], formula="-EX_Ac * X * 1 l_per_mmol")
    builder.create_update_reaction(model, sid="Glcxt", modifiers=["X"], formula="-EX_Glcxt * X * 1 l_per_mmol")
    builder.create_update_reaction(model, sid="O2", modifiers=["X"], formula="-EX_O2 * X * 1 l_per_mmol")
    builder.create_update_reaction(model, sid="X", modifiers=["X"], formula="-EX_X * X * 1 l_per_mmol")

    # ports
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["bioreactor",
                              "Ac", "Glcxt", "O2", "X",
                              "EX_Ac", "EX_Glcxt", "EX_O2", "EX_X"])

    # write SBML file
    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)


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
    top_notes = notes.format("""
    <h2>TOP model</h2>
    <p>Main comp DFBA model by combining fba, update and bounds
        model with additional kinetics in the top model.</p>
    """)
    # Necessary to change into directory with submodel files
    working_dir = os.getcwd()
    os.chdir(directory)

    sbmlns = libsbml.SBMLNamespaces(3, 1, "comp", 1)
    doc = libsbml.SBMLDocument(sbmlns)
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
    model.setName("diauxic (TOP)")
    utils.set_model_info(model, notes=top_notes,
                         creators=creators, units=units, main_units=main_units)
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
                value = builder.LOWER_BOUND_DEFAULT
            elif bound_type == 'ub':
                value = builder.UPPER_BOUND_DEFAULT
            parameters.append(
                # lb_vGlcxt
                mc.Parameter(sid="{}_{}".format(bound_type, ex_rid), value=value, unit=UNIT_FLUX, constant=False,
                             sboTerm="SBO:0000625")
            )
    mc.create_objects(model, parameters)

    # Reactions
    # dummy reaction (pseudoreaction)
    mc.create_reaction(model, rid="dummy_EX_Glcxt", reversible=False,
                       products={"dummy_S": 1}, sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="dummy_EX_O2", reversible=False,
                       products={"dummy_S": 1}, sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="dummy_EX_Ac", reversible=False,
                       products={"dummy_S": 1}, sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="dummy_EX_X", reversible=False,
                       products={"dummy_S": 1}, sboTerm="SBO:0000631")

    # oxygen transfer reaction
    mc.create_reaction(model, rid="vO2_transfer", name="oxygen transfer", reversible=True,
                       reactants={}, products={"O2": 1}, formula="kLa * (O2_ref-O2) * bioreactor",
                       compartment="bioreactor")

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
        'lb_EX_X', 'ub_EX_X'
    ]:
        comp.replace_elements(model, bound_id, ref_type=comp.SBASE_REF_TYPE_PORT,
                              replaced_elements={'bounds': ['{}_port'.format(bound_id)],
                                                 'fba': ['{}_port'.format(bound_id)]})

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
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)
    # change back into working dir
    os.chdir(working_dir)


def create_model(output_dir):
    """ Create all models.

    :return:
    """
    directory = utils.versioned_directory(output_dir, version=version)

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

    # create reports
    sbml_paths = [pjoin(directory, fname) for fname in
                  # [fba_file, bounds_file, update_file, top_file, flattened_file]]
                  [fba_file, bounds_file, update_file, top_file, flattened_file]]
    sbmlreport.create_sbml_reports(sbml_paths, directory, validate=False)

    return directory


if __name__ == "__main__":
    from sbmlutils.dfba.diauxic_growth.dgsettings import out_dir
    directory = create_model(output_dir=out_dir)
