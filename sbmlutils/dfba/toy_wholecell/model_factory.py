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
from six import iteritems

import os
from os.path import join as pjoin
import libsbml
from libsbml import (UNIT_KIND_SECOND, UNIT_KIND_METRE,
                     UNIT_KIND_ITEM, UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE)

from sbmlutils import comp
from sbmlutils import sbmlio
from sbmlutils import factory as mc
from sbmlutils.report import sbmlreport
from sbmlutils import annotation

from sbmlutils.dfba import builder
from sbmlutils.dfba import utils
from sbmlutils.dfba.toy_wholecell import settings

libsbml.XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################
version = 11
DT_SIM = 0.1
notes = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Wholecell Toy Model</h1>
    <p><strong>Model version: {}</strong></p>

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
""".format(version, '{}')
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
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0)], name="second"),
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)], name="kilogram"),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)], name="meter"),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)], name="square meter"),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)], name="cubic meter"),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0),
                   (UNIT_KIND_METRE, -3.0)], name="millimolar"),
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
def fba_model(sbml_file, directory, annotations=None):
    """ FBA model
    
    :param sbml_file: output file name 
    :param directory: output directory
    :return: SBMLDocument
    """
    fba_notes = notes.format("""
    <h2>FBA submodel</h2>
    <p>DFBA fba submodel. Unbalanced metabolites are encoded via exchange fluxes.</p>
    """)
    doc = builder.template_doc_fba(settings.model_id)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=fba_notes,
                         creators=creators,
                         units=units, main_units=main_units)

    objects = [
        # compartments
        mc.Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment',
                       spatialDimensions=3),
        mc.Compartment(sid='cell', value=1.0, unit=UNIT_VOLUME, constant=True, name='cell', spatialDimensions=3),
        mc.Compartment(sid='membrane', value=1.0, unit=UNIT_AREA, constant=True, name='membrane', spatialDimensions=2),

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
        mc.Parameter(sid="ub_R1", value=1.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
        mc.Parameter(sid="zero", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
        mc.Parameter(sid="ub_default", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True,
                     sboTerm=builder.FLUX_BOUND_SBO),
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
    model_fbc = model.getPlugin("fbc")
    mc.create_objective(model_fbc, oid="R3_maximize", otype="maximize",
                        fluxObjectives={"R3": 1.0}, active=True)

    # create ports for kinetic bounds
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["ub_R1"])

    # write SBML
    if annotations:
        annotation.annotate_sbml_doc(doc, annotations)
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)
    return doc


####################################################
# BOUNDS submodel
####################################################
def bounds_model(sbml_file, directory, doc_fba, annotations=None):
    """"
    Bounds model.
    """
    bounds_notes = notes.format("""
    <h2>BOUNDS submodel</h2>
    <p>Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.</p>
    """)
    doc = builder.template_doc_bounds(settings.model_id)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=bounds_notes,
                         creators=creators,
                         units=units, main_units=main_units)

    builder.create_dfba_dt(model, step_size=DT_SIM, time_unit=UNIT_TIME, create_port=True)

    # compartment
    compartment_id = 'extern'
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME,
                                    create_port=True)

    # species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_AMOUNT,
                                hasOnlySubstanceUnits=True, create_port=True)

    # exchange bounds
    builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=True)

    objects = [
        # exchange bounds
        # FIXME: readout the FBA network bounds
        mc.Parameter(sid="lb_default", value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),

        # kinetic bound parameter & calculation
        mc.Parameter(sid='ub_R1', value=1.0, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
        mc.Parameter(sid='k1', value=-0.2, unit="per_s", name="k1", constant=False),
        mc.RateRule(sid="ub_R1", value="k1*ub_R1"),

        # bound assignment rules
        mc.AssignmentRule(sid="lb_EX_A", value='max(lb_default, -A/dt)'),
        mc.AssignmentRule(sid="lb_EX_C", value='max(lb_default, -C/dt)'),
    ]
    mc.create_objects(model, objects)

    # ports
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=["ub_R1"])
    if annotations:
        annotation.annotate_sbml_doc(doc, annotations)
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)


####################################################
# UPDATE submodel
####################################################
def update_model(sbml_file, directory, doc_fba=None, annotations=None):
    """ Update model.
    """
    update_notes = notes.format("""
        <h2>UPDATE submodel</h2>
        <p>Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.</p>
        """)
    doc = builder.template_doc_update(settings.model_id)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=update_notes,
                         creators=creators,
                         units=units, main_units=main_units)

    # compartment
    compartment_id = "extern"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=True)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_AMOUNT,
                                hasOnlySubstanceUnits=True, create_port=True)

    # update reactions
    builder.create_update_reactions(model, model_fba=model_fba, formula="-{}", unit_flux=UNIT_FLUX,
                                    modifiers=[])


    # write SBML file
    if annotations:
        annotation.annotate_sbml_doc(doc, annotations)
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)


####################################################
# TOP submodel
####################################################
def top_model(sbml_file, directory, emds, doc_fba, annotations=None):
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

    doc = builder.template_doc_top(settings.model_id, emds)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=top_notes,
                         creators=creators, units=units, main_units=main_units)

    # dt
    builder.create_dfba_dt(model, step_size=DT_SIM, time_unit=UNIT_TIME, create_port=False)

    # compartment
    compartment_id = "extern"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=False)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, hasOnlySubstanceUnits=True,
                                unit=UNIT_AMOUNT, create_port=False)
    # dummy species
    builder.create_dummy_species(model, compartment_id=compartment_id, hasOnlySubstanceUnits=True,
                                 unit=UNIT_AMOUNT)

    # exchange flux bounds
    builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=False)

    # dummy reactions & flux assignments
    builder.create_dummy_reactions(model, model_fba=model_fba, unit_flux=UNIT_FLUX)

    # replacedBy (fba reactions)
    builder.create_top_replacedBy(model, model_fba=model_fba)

    # replaced
    builder.create_top_replacements(model, model_fba, compartment_id=compartment_id)

    # initial concentrations for fba exchange species
    initial_c = {
        'A': 10.0,
        'C': 0.0,
    }
    for sid, value in iteritems(initial_c):
        species = model.getSpecies(sid)
        species.setInitialConcentration(value)

    # kinetic model
    mc.create_objects(model, [
        # kinetic species
        mc.Species(sid='D', value=0, unit=UNIT_AMOUNT,
                   hasOnlySubstanceUnits=True, compartment="extern"),

        # kinetic
        mc.Parameter(sid="k_R4", name="k R4", value=0.1, constant=True, unit="per_s"),

        # bounds parameter
        mc.Parameter(sid='ub_R1', value=1.0, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000346"),
    ])
    # kinetic reaction (MMK)
    mc.create_reaction(model, rid="R4", name="C -> D", fast=False, reversible=False,
                       reactants={"C": 1}, products={"D": 1}, formula="k_R4*C", compartment="extern")

    # kinetic flux bounds
    comp.replace_elements(model, 'ub_R1', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['ub_R1_port'],
                                             'fba': ['ub_R1_port']})

    # write SBML file
    if annotations:
        annotation.annotate_sbml_doc(doc, annotations)
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)

    # change back the working dir
    os.chdir(working_dir)


def create_model(output_dir):
    """ Create all submodels and comp model.

    :param output_dir: results directory
    :rtype:
    :return directory in which model files exist.
    """
    directory = utils.versioned_directory(output_dir, version=version)

    f_annotations = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.annotations_file)
    annotations = annotation.ModelAnnotator.annotations_from_file(f_annotations)

    # create sbml
    doc_fba = fba_model(settings.fba_file, directory, annotations=annotations)
    bounds_model(settings.bounds_file, directory, doc_fba=doc_fba, annotations=annotations)
    update_model(settings.update_file, directory, doc_fba=doc_fba, annotations=annotations)

    emds = {
        "{}_fba".format(settings.model_id): settings.fba_file,
        "{}_bounds".format(settings.model_id): settings.bounds_file,
        "{}_update".format(settings.model_id): settings.update_file,
    }

    # flatten top model
    top_model(settings.top_file, directory, emds, doc_fba, annotations=annotations)
    comp.flattenSBMLFile(sbml_path=pjoin(directory, settings.top_file),
                         output_path=pjoin(directory, settings.flattened_file))
    # create reports
    sbml_paths = [pjoin(directory, fname) for fname in
                  # [fba_file, bounds_file, update_file, top_file, flattened_file]]
                  [settings.fba_file,
                   settings.bounds_file,
                   settings.update_file,
                   settings.top_file,
                   settings.flattened_file]]
    sbmlreport.create_sbml_reports(sbml_paths, directory, validate=False)
    return directory


########################################################################################################################
if __name__ == "__main__":
    directory = create_model(output_dir=settings.out_dir)
    print(directory)
