# -*- coding=utf-8 -*-
"""
Create SBML models for the ATP submodel.
* No flux weighting performed with model
* species and fluxes are handled via concentrations
"""

from __future__ import print_function, absolute_import

import os
from os.path import join as pjoin

try:
    import libsbml
    from libsbml import (UNIT_KIND_SECOND, UNIT_KIND_METRE,
                         UNIT_KIND_ITEM, UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE)
except ImportError:
    import tesbml as libsbml
    from tesbml import (UNIT_KIND_SECOND, UNIT_KIND_METRE,
                         UNIT_KIND_ITEM, UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE)


from sbmlutils import comp
from sbmlutils import sbmlio
from sbmlutils import factory as mc
from sbmlutils import annotation
from sbmlutils.report import sbmlreport


from sbmlutils.dfba import builder
from sbmlutils.dfba import utils
from sbmlutils.dfba.toy_atp import settings

libsbml.XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################
DT_SIM = 0.1
notes = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>ATP Toy Model</h1>
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
""".format(settings.VERSION, '{}')
creators = [
    mc.Creator(familyName='Koenig', givenName='Matthias', email='konigmatt@googlemail.com',
               organization='Humboldt University Berlin', site='http://livermetabolism.com')
]
main_units = {
    'time': 'h',
    'extent': UNIT_KIND_MOLE,
    'substance': UNIT_KIND_MOLE,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}
units = [
    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)], name="hour"),
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)], name="kilogram"),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)], name="meter"),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)], name="square meter"),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)], name="cubic meter"),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0),
                   (UNIT_KIND_METRE, -3.0)], name="millimolar"),
    mc.Unit('mole_per_h', [(UNIT_KIND_MOLE, 1.0),
                           (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
]

UNIT_TIME = 'h'
UNIT_AMOUNT = UNIT_KIND_ITEM
UNIT_AREA = 'm2'
UNIT_VOLUME = 'm3'
UNIT_CONCENTRATION = 'mM'
UNIT_FLUX = 'mole_per_h'


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
    doc = builder.template_doc_fba(settings.MODEL_ID)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=fba_notes,
                         creators=creators,
                         units=units, main_units=main_units)

    objects = [
        # compartments
        mc.Compartment(sid='cell', value=1.0, unit=UNIT_VOLUME, constant=True, name='cell', spatialDimensions=3),

        # exchange species
        mc.Species(sid='atp', name="ATP", value=0, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False, compartment="cell"),
        mc.Species(sid='adp', name="ADP", value=0, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False, compartment="cell"),
        mc.Species(sid='glc', name="Glucose", value=0, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False, compartment="cell"),
        mc.Species(sid='pyr', name='Pyruvate', value=0, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False, compartment="cell"),

        # internal species
        mc.Species(sid='fru16bp', name='Fructose 1,6-bisphospate', value=0, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False, compartment="cell"),
        mc.Species(sid='pg2', name='2-Phosphoglycerate', value=0, unit=UNIT_CONCENTRATION, hasOnlySubstanceUnits=False, compartment="cell"),

        # bounds
        mc.Parameter(sid="ub_R3", value=1.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
        mc.Parameter(sid="zero", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
        mc.Parameter(sid="ub_default", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True,
                     sboTerm=builder.FLUX_BOUND_SBO),
    ]
    mc.create_objects(model, objects)

    # reactions
    r1 = mc.create_reaction(model, rid="R1", name="glu + 2 atp -> fru16bp + 2 adp", fast=False, reversible=False,
                            reactants={"glc": 1, "atp": 2}, products={"fru16bp": 1, 'adp': 2}, compartment='cell')
    r2 = mc.create_reaction(model, rid="R2", name="fru16bp -> 2 pg2", fast=False, reversible=False,
                            reactants={"fru16bp": 1}, products={"pg2": 2}, compartment='cell')
    r3 = mc.create_reaction(model, rid="R3", name="pg2 + adp -> pyr + atp", fast=False, reversible=False,
                            reactants={"pg2": 1, "adp": 2}, products={"pyr": 1, "atp": 2}, compartment='cell')

    # flux bounds
    mc.set_flux_bounds(r1, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r2, lb="zero", ub="ub_default")
    mc.set_flux_bounds(r3, lb="zero", ub="ub_R3")
    # mc.set_flux_bounds(ratp, lb="zero", ub="ub_RATP")

    # exchange reactions
    for sid in ['atp', 'adp', 'glc', 'pyr']:
        builder.create_exchange_reaction(model, species_id=sid, flux_unit=UNIT_FLUX)

    # objective function
    model_fbc = model.getPlugin("fbc")
    mc.create_objective(model_fbc, oid="RATP_maximize", otype="maximize", fluxObjectives={"R3": 1.0}, active=True)

    if annotations:
        annotation.annotate_sbml_doc(doc, annotations)

    # write SBML
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
    doc = builder.template_doc_bounds(settings.MODEL_ID)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=bounds_notes,
                         creators=creators,
                         units=units, main_units=main_units)
    builder.create_dfba_dt(model, step_size=DT_SIM, time_unit=UNIT_TIME, create_port=True)

    # compartment
    compartment_id = 'cell'
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=True)

    # species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_CONCENTRATION,
                                hasOnlySubstanceUnits=False, create_port=True)

    # exchange bounds
    builder.create_exchange_bounds(model_bounds=model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=True)
    builder.create_dynamic_bounds(model_bounds=model, model_fba=model_fba, unit_flux=UNIT_FLUX)

    # annotations
    if annotations:
        annotation.annotate_sbml_doc(doc, annotations)

    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)


####################################################
# UPDATE submodel
####################################################
def update_model(sbml_file, directory, doc_fba=None, annotations=None):
    """ Update model."""
    update_notes = notes.format("""
        <h2>UPDATE submodel</h2>
        <p>Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.</p>
        """)
    doc = builder.template_doc_update(settings.MODEL_ID)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=update_notes,
                         creators=creators,
                         units=units, main_units=main_units)

    # compartment
    compartment_id = "cell"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=True)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_CONCENTRATION,
                                hasOnlySubstanceUnits=False, create_port=True)

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

    doc = builder.template_doc_top(settings.MODEL_ID, emds)
    model = doc.getModel()
    utils.set_model_info(model,
                         notes=top_notes,
                         creators=creators, units=units, main_units=main_units)

    # dt
    builder.create_dfba_dt(model, step_size=DT_SIM, time_unit=UNIT_TIME, create_port=False)

    # compartment
    compartment_id = "cell"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=False)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, hasOnlySubstanceUnits=False,
                                unit=UNIT_CONCENTRATION, create_port=False)
    # dummy species
    builder.create_dummy_species(model, compartment_id=compartment_id, hasOnlySubstanceUnits=False,
                                 unit=UNIT_CONCENTRATION)

    # exchange flux bounds
    builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=False)

    # dummy reactions & flux assignments
    builder.create_dummy_reactions(model, model_fba=model_fba, unit_flux=UNIT_FLUX)

    # replacedBy (fba reactions)
    builder.create_top_replacedBy(model, model_fba=model_fba)

    # replaced
    builder.create_top_replacements(model, model_fba, compartment_id=compartment_id)

    objects = [
        # kinetic parameters
        mc.Parameter(sid="Vmax_RATP", value=1, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid='k_RATP', value=0.1, unit=UNIT_CONCENTRATION, constant=True),

        # balancing rules
        mc.AssignmentRule(sid="atp_tot", value="atp + adp", unit="mM"),
        mc.AssignmentRule(sid="c3_tot", value="2 dimensionless * glc + pyr", unit="mM")
    ]
    mc.create_objects(model, objects)

    ratp = mc.create_reaction(model, rid="RATP", name="atp -> adp", fast=False, reversible=False,
                              reactants={"atp": 1}, products={"adp": 1}, compartment=compartment_id,
                              formula='Vmax_RATP * atp/(k_RATP + atp)')

    # initial concentrations for fba exchange species
    initial_c = {
        'atp': 2.0,
        'adp': 1.0,
        'glc': 5.0,
        'pyr': 0.0
    }
    for sid, value in initial_c.items():
        species = model.getSpecies(sid)
        species.setInitialConcentration(value)

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
    f_annotations = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'annotations.xlsx')
    annotations = annotation.ModelAnnotator.annotations_from_file(f_annotations)

    directory = utils.versioned_directory(output_dir, version=settings.VERSION)

    # create sbml
    doc_fba = fba_model(settings.FBA_LOCATION, directory, annotations=annotations)
    bounds_model(settings.BOUNDS_LOCATION, directory, doc_fba=doc_fba, annotations=annotations)
    update_model(settings.UPDATE_LOCATION, directory, doc_fba=doc_fba, annotations=annotations)

    emds = {
        "{}_fba".format(settings.MODEL_ID): settings.FBA_LOCATION,
        "{}_bounds".format(settings.MODEL_ID): settings.BOUNDS_LOCATION,
        "{}_update".format(settings.MODEL_ID): settings.UPDATE_LOCATION,
    }

    # flatten top model
    top_model(settings.TOP_LOCATION, directory, emds, doc_fba, annotations=annotations)
    comp.flattenSBMLFile(sbml_path=pjoin(directory, settings.TOP_LOCATION),
                         output_path=pjoin(directory, settings.FLATTENED_LOCATION))

    # create reports
    locations = [
        settings.FBA_LOCATION,
        settings.BOUNDS_LOCATION,
        settings.UPDATE_LOCATION,
        settings.TOP_LOCATION,
        settings.FLATTENED_LOCATION
    ]

    sbml_paths = [pjoin(directory, fname) for fname in locations]
    sbmlreport.create_sbml_reports(sbml_paths, directory, validate=False)

    # create sedml
    from sbmlutils.dfba.sedml import create_sedml
    species_ids = ", ".join(['atp', 'adp', 'glc', 'pyr'])
    reaction_ids = ", ".join(['EX_atp', 'EX_adp', 'EX_glc', 'EX_pyr', 'RATP'])
    create_sedml(settings.SEDML_LOCATION, settings.TOP_LOCATION, directory=directory,
                 dt=0.1, tend=15, species_ids=species_ids, reaction_ids=reaction_ids)

    return directory


########################################################################################################################
if __name__ == "__main__":
    create_model(output_dir=settings.OUT_DIR)
