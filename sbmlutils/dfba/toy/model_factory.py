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
from __future__ import print_function, absolute_import

from os.path import join as pjoin
from libsbml import *

from sbmlutils import comp
from sbmlutils import sbmlio
from sbmlutils import factory as mc
from sbmlutils.report import sbmlreport

from sbmlutils.dfba import builder
from sbmlutils.dfba.builder import LOWER_BOUND_DEFAULT, UPPER_BOUND_DEFAULT, exchange_flux_bound_parameters
from sbmlutils.dfba.utils import versioned_directory, add_generic_info
from sbmlutils.dfba.toy import toysettings

XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################
version = 3
DT_SIM = 0.1
notes = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Wholecell Toy Model</h1>
    {}
    <h2>Description</h2>
    <p>This is a toy model for coupling models with different modeling frameworks via comp.</p>

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
"""
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

UNIT_TIME = 's'
UNIT_AMOUNT = UNIT_KIND_ITEM
UNIT_AREA = 'm2'
UNIT_VOLUME = 'm3'
UNIT_CONCENTRATION = 'item_per_m3'
UNIT_FLUX = 'item_per_s'


####################################################
# FBA submodel
####################################################
def fba_model(sbml_file, directory):
    """FBA model."""
    fba_notes = notes.format("""
    <h2>FBA submodel</h2>
    <p>DFBA fba submodel. Unbalanced metabolites are encoded via exchange fluxes.</p>
    """)

    sbmlns = SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 2)
    sbmlns.addPackageNamespace("comp", 1)

    doc_fba = SBMLDocument(sbmlns)
    doc_fba.setPackageRequired("comp", True)
    doc_fba.setPackageRequired("fbc", False)
    model = doc_fba.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(True)

    # model
    model.setId('toy_fba')
    model.setName('toy (FBA submodel)')
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)
    add_generic_info(model,
                     notes=fba_notes,
                     creators=creators,
                     units=units, main_units=main_units)

    objects = [
        # compartments
        mc.Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment',
                       spatialDimension=3),
        mc.Compartment(sid='cell', value=1.0, unit=UNIT_VOLUME, constant=True, name='cell', spatialDimension=3),
        mc.Compartment(sid='membrane', value=1.0, unit=UNIT_AREA, constant=True, name='membrane', spatialDimension=2),

        # exchange species
        mc.Species(sid='A', name="A", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),

        # internal species
        mc.Species(sid='B1', name="B1", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="cell"),
        mc.Species(sid='B2', name="B2", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="cell"),

        # bounds
        mc.Parameter(sid="ub_R1", value=1.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.SBO_FLUX_BOUND),
        mc.Parameter(sid="zero", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.SBO_FLUX_BOUND),
        mc.Parameter(sid="ub_default", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True,
                     sboTerm=builder.SBO_FLUX_BOUND),
    ]
    mc.create_objects(model, objects)

    # reactions
    r1 = mc.create_reaction(model, rid="R1", name="A import (R1)", fast=False, reversible=True,
                            reactants={"A": 1}, products={"B1": 1}, compartment='membrane')
    r2 = mc.create_reaction(model, rid="R2", name="B1 <-> B2 (R2)", fast=False, reversible=True,
                            reactants={"B1": 1}, products={"B2": 1}, compartment='cell')
    r3 = mc.create_reaction(model, rid="R3", name="B2 export (R3)", fast=False, reversible=True,
                            reactants={"B2": 1}, products={"C": 1}, compartment='membrane')

    # flux bounds
    mc.set_flux_bounds(r1, lb="zero", ub="ub_R1")
    mc.set_flux_bounds(r2, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r3, lb="zero", ub="ub_default")

    # exchange reactions
    builder.create_exchange_reaction(model, species_id="A", flux_unit=UNIT_FLUX)
    builder.create_exchange_reaction(model, species_id="C", flux_unit=UNIT_FLUX)

    # objective function
    mc.create_objective(mplugin, oid="R3_maximize", otype="maximize",
                        fluxObjectives={"R3": 1.0}, active=True)

    # create ports for kinetic bounds
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["ub_R1"])

    # write SBML
    sbmlio.write_sbml(doc_fba, filepath=os.path.join(directory, sbml_file), validate=True)


####################################################
# BOUNDS submodel
####################################################
def bounds_model(sbml_file, directory):
    """"
    Bounds model.
    """
    bounds_notes = notes.format("""
    <h2>BOUNDS submodel</h2>
    <p>Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.</p>
    """)
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("toy_bounds")
    model.setName("toy (BOUNDS submodel)")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model,
                     notes=bounds_notes,
                     creators=creators,
                     units=units, main_units=main_units)

    objects = [
        # min and max
        mc.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='minimum of arguments'),
        mc.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='maximum of arguments'),

        # compartments
        mc.Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment',
                       spatialDimension=3),

        # species
        mc.Species(sid='A', name="A", value=10, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),

        # dt parameter
        builder.create_dt(step_size=DT_SIM, unit=UNIT_TIME),

        # exchange bounds
        mc.Parameter(sid="lb_default", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub_EX_A", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb_EX_A", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub_EX_C", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb_EX_C", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),

        # kinetic bound parameter & calculation
        mc.Parameter(sid='ub_R1', value=1.0, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000346"),
        mc.Parameter(sid='k1', value=-0.2, unit="per_s", name="k1", constant=False),
        mc.RateRule(sid="ub_R1", value="k1*ub_R1"),

        # bound assignment rules
        mc.AssignmentRule(sid="lb_EX_A", value='max(lb_default, -A/dt)'),
        mc.AssignmentRule(sid="lb_EX_C", value='max(lb_default, -C/dt)'),
    ]
    mc.create_objects(model, objects)

    # ports
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["dt",
                              "extern",
                              "A", "C",
                              "lb_EX_A", "lb_EX_C",
                              "ub_EX_A", "ub_EX_C",
                              "ub_R1"])

    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)


####################################################
# UPDATE submodel
####################################################
def update_model(sbml_file, directory):
    """ Update model.
    """
    update_notes = notes.format("""
        <h2>UPDATE submodel</h2>
        <p>Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.</p>
        """)
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("toy_update")
    model.setName("toy (UPDATE submodel)")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model,
                     notes=update_notes,
                     creators=creators,
                     units=units, main_units=main_units)

    objects = [
        mc.Compartment(sid='extern', value=1.0, unit="m3", constant=True, name='external compartment'),
        mc.Species(sid='A', name="A", value=10.0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True, compartment="extern"),
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True, compartment="extern"),
        mc.Parameter(sid="EX_A", value=1.0, constant=False, unit=UNIT_FLUX, sboTerm="SBO:0000613"),
        mc.Parameter(sid="EX_C", value=1.0, constant=False, unit=UNIT_FLUX, sboTerm="SBO:0000613"),
    ]
    mc.create_objects(model, objects)

    # update reactions
    mc.create_reaction(model, rid="update_A", reversible=True,
                                reactants={"A": 1}, products={},
                                formula="-EX_A", sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="update_C", reversible=True,
                                reactants={"C": 1}, products={},
                                formula="-EX_C", sboTerm="SBO:0000631")
    # ports
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["extern",
                              "A", "C",
                              "EX_A", "EX_C"])

    # write SBML file
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)


####################################################
# TOP submodel
####################################################
def top_model(sbml_file, directory, emds):
    """ Create top comp model.

    Creates full comp model by combining fba, update and bounds
    model with additional kinetics in the top model.
    """
    top_notes = notes.format("""
        <h2>TOP model</h2>
        <p>Main comp DFBA model by combining fba, update and bounds
            model with additional kinetics in the top model.</p>
        """)
    working_dir = os.getcwd()
    os.chdir(directory)
    sbmlns = SBMLNamespaces(3, 1, "comp", 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    doc.setPackageRequired("fbc", False)
    mdoc = doc.getPlugin("comp")

    # create listOfExternalModelDefinitions
    emd_bounds = comp.create_ExternalModelDefinition(mdoc, "toy_bounds", source=emds["toy_bounds"])
    emd_fba = comp.create_ExternalModelDefinition(mdoc, "toy_fba", source=emds["toy_fba"])
    emd_update = comp.create_ExternalModelDefinition(mdoc, "toy_update", source=emds["toy_update"])

    # create models and submodels
    model = doc.createModel()
    model.setId("toy_top")
    model.setName("toy (TOP model)")
    add_generic_info(model,
                     notes=top_notes,
                     creators=creators, units=units, main_units=main_units)
    mplugin = model.getPlugin("comp")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    # add submodel which references the external model definition
    comp.add_submodel_from_emd(mplugin, submodel_id="bounds", emd=emd_bounds)
    comp.add_submodel_from_emd(mplugin, submodel_id="fba", emd=emd_fba)
    comp.add_submodel_from_emd(mplugin, submodel_id="update", emd=emd_update)

    # Compartments
    mc.create_objects(model, [
        mc.Compartment(sid="extern", name="external compartment", value=1.0, constant=True,
                       spatialDimension=3, unit=UNIT_VOLUME),

        mc.Species(sid='dummy_S', value=0, unit=UNIT_AMOUNT,
                   hasOnlySubstanceUnits=True, compartment="extern", sboTerm="SBO:0000291"),
        mc.Species(sid='A', value=10.0, unit=UNIT_AMOUNT,
                   hasOnlySubstanceUnits=True, compartment="extern"),
        mc.Species(sid='C', value=0, unit=UNIT_AMOUNT,
                   hasOnlySubstanceUnits=True, compartment="extern"),
        mc.Species(sid='D', value=0, unit=UNIT_AMOUNT,
                   hasOnlySubstanceUnits=True, compartment="extern"),

        # dt
        builder.create_dt(step_size=DT_SIM, unit=UNIT_TIME),

        # flux parameters
        mc.Parameter(sid='EX_A', value=1.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid='EX_C', value=1.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),

        # kinetic
        mc.Parameter(sid="k_R4", name="k R4", value=0.1, constant=True, unit="per_s"),

        # flux assignment rules
        mc.AssignmentRule("EX_A", value="dummy_EX_A"),
        mc.AssignmentRule("EX_C", value="dummy_EX_C"),

        # bounds parameter
        mc.Parameter(sid='ub_R1', value=1.0, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000346"),

    ])

    # creates the exchange bound parameters
    mc.create_objects(model,
                      exchange_flux_bound_parameters(exchange_rids=['EX_A', 'EX_C'],
                                                     unit=UNIT_FLUX))
    # kinetic flux bounds
    comp.replace_elements(model, 'ub_R1', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['ub_R1_port'],
                                             'fba': ['ub_R1_port']})
    # Reactions
    # exchange reaction in top model
    mc.create_reaction(model, rid="dummy_EX_A", reversible=True,
                       reactants={}, products={"dummy_S": 1}, sboTerm="SBO:0000631")
    mc.create_reaction(model, rid="dummy_EX_C", reversible=True,
                       reactants={}, products={"dummy_S": 1}, sboTerm="SBO:0000631")

    # kinetic reaction (MMK)
    mc.create_reaction(model, rid="R4", name="C -> D", fast=False, reversible=False,
                       reactants={"C": 1}, products={"D": 1}, formula="k_R4*C", compartment="extern")


    # fluxes
    comp.replace_elements(model, 'EX_A', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['EX_A_port']})
    comp.replace_elements(model, 'EX_C', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['EX_C_port']})

    # ReplacedBy: replace dummy reaction by fba exchage reactions
    comp.replaced_by(model, 'dummy_EX_A', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="EX_A_port")
    comp.replaced_by(model, 'dummy_EX_C', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="EX_C_port")

    # dt
    comp.replace_elements(model, 'dt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['dt_port']})

    # replace compartments
    comp.replace_elements(model, 'extern', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['extern_port'],
                                             'bounds': ['extern_port']})

    # replace species
    comp.replace_elements(model, 'A', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['A_port'],
                                             'bounds': ['A_port']})
    comp.replace_elements(model, 'C', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['C_port'],
                                             'bounds': ['C_port']})

    # exchange bounds
    for bound_id in [
        'lb_EX_A', 'ub_EX_A',
        'lb_EX_C', 'ub_EX_C'
    ]:
        comp.replace_elements(model, bound_id, ref_type=comp.SBASE_REF_TYPE_PORT,
                              replaced_elements={'bounds': ['{}_port'.format(bound_id)],
                                                 'fba': ['{}_port'.format(bound_id)]})

    # replace units
    for uid in ['s', 'kg', 'm3', 'm2', 'mM', 'item_per_m3', 'm', 'per_s', 'item_per_s']:
        comp.replace_element_in_submodels(model, uid, ref_type=comp.SBASE_REF_TYPE_UNIT,
                                          submodels=['bounds', 'fba', 'update'])

    # write SBML file
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)

    # change back the working dir
    os.chdir(working_dir)


def create_model(output_dir):
    """ Create all submodels and comp model.

    :param output_dir: results directory
    :rtype:
    :return directory in which model files exist.
    """
    directory = versioned_directory(output_dir, version=version)

    # create sbml
    fba_model(toysettings.fba_file, directory)
    bounds_model(toysettings.bounds_file, directory)
    update_model(toysettings.update_file, directory)

    emds = {
        "toy_fba": toysettings.fba_file,
        "toy_bounds": toysettings.bounds_file,
        "toy_update": toysettings.update_file,
    }

    # flatten top model
    top_model(toysettings.top_file, directory, emds)
    comp.flattenSBMLFile(sbml_path=pjoin(directory, toysettings.top_file),
                         output_path=pjoin(directory, toysettings.flattened_file))
    # create reports
    sbml_paths = [pjoin(directory, fname) for fname in
                  # [fba_file, bounds_file, update_file, top_file, flattened_file]]
                  [toysettings.fba_file,
                   toysettings.bounds_file,
                   toysettings.update_file,
                   toysettings.top_file,
                   toysettings.flattened_file]]
    sbmlreport.create_sbml_reports(sbml_paths, directory, validate=False)
    return directory


########################################################################################################################
if __name__ == "__main__":
    directory = create_model(output_dir=toysettings.out_dir)
    print(directory)
