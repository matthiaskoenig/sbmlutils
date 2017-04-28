# -*- coding=utf-8 -*-
"""
Model: iAB_RBC_283

iAB-RBC-283: A proteomically derived knowledge-base of erythrocyte metabolism that can be used to simulate 
its physiological and patho-physiological states.

https://www.ncbi.nlm.nih.gov/pubmed/21749716
"""
from __future__ import print_function, absolute_import
from six import iteritems
    
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
from sbmlutils.dfba.rbc.settings import fba_file, model_id, bounds_file, update_file, top_file, flattened_file

libsbml.XMLOutputStream.setWriteTimestamp(False)

# TODO: add biomass
# TODO: biomass weighting of fluxes

########################################################################
# General model information
########################################################################
version = 1
DT_SIM = 0.1
notes = """
<notes>
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>E.coli core DFBA model</h1>
    <p><strong>Model version: {}</strong></p>
    <p>{}</p>
      <h2>Description</h2>
      <div class="dc:description">
        <p>This is a metabolism model of Homo sapiens in 
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
      <a href="http://identifiers.org/bigg.model/iAB_RBC_283" title="Access to this model via BiGG Models knowledge-base." target="_blank">iAB_RBC_283</a>.</div>
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
        <a href="http://identifiers.org/bigg.model/iAB_RBC_283" title="Access to this model via BiGG Models knowledge-base." target="_blank">this model in BiGG Models knowledge-base</a>.</p>
      </div>
      <h2>References</h2>When using content from BiGG Models knowledge-base in your research works, please cite 
      <dl>
        <dt>King ZA, Lu JS, Dräger A, Miller PC, Federowicz S, Lerman JA, Ebrahim A, Palsson BO, and&#160;Lewis NE. (2015). 
        <dd>BiGG Models: A platform for integrating, standardizing, and sharing genome-scale models. 
        <i>Nucl Acids Res</i>. 
        <a href="https://dx.doi.org/10.1093/nar/gkv1049" target="_blank" title="Access the publication about BiGG Models knowledge-base">doi:10.1093/nar/gkv1049</a></dd></dt>
      </dl></body>
    </notes>
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
    """
    # Read the model
    fba_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/iAB_RBC_283.xml')
    doc_fba = sbmlio.read_sbml(fba_path)

    # add comp
    doc_fba.enablePackage("http://www.sbml.org/sbml/level3/version1/comp/version1", "comp", True)
    doc_fba.setPackageRequired("comp", True)

    # add notes
    model = doc_fba.getModel()
    fba_notes = notes.format("""DFBA FBA submodel.""")
    utils.set_model_info(model, notes=fba_notes,
                         creators=None, units=units, main_units=main_units)

    # clip R_ reaction and M_ metabolite prefixes
    utils.clip_prefixes_in_model(model)

    # set id & framework
    model.setId('{}_fba'.format(model_id))
    model.setName('{} (FBA)'.format(model_id))
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)

    # add units and information
    for species in model.getListOfSpecies():
        species.setInitialConcentration(0.0)
        species.setHasOnlySubstanceUnits(False)
        species.setUnits(UNIT_AMOUNT)
    for compartment in model.getListOfCompartments():
        compartment.setUnits(UNIT_VOLUME)

    # update the existing exchange reactions
    builder.update_exchange_reactions(model, flux_unit=UNIT_FLUX)

    # write SBML file
    sbmlio.write_sbml(doc_fba, filepath=pjoin(directory, sbml_file), validate=True)

    return doc_fba


def bounds_model(sbml_file, directory, doc_fba=None):
    """"
    Submodel for dynamically calculating the flux bounds.

    The dynamically changing flux bounds are the input to the
    FBA model.
    """
    doc = builder.template_doc_bounds(model_id)
    model = doc.getModel()

    bounds_notes = notes.format("""
    <h2>BOUNDS submodel</h2>
    <p>Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.</p>
    """)
    utils.set_model_info(model, notes=bounds_notes, creators=creators, units=units, main_units=main_units)

    # dt
    compartment_id = "blood"
    builder.create_dfba_dt(model, time_unit=UNIT_TIME, create_port=True)

    # compartment
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=True)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_CONCENTRATION,
                                create_port=True)

    # bounds
    builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=True)

    # bounds
    fba_prefix = "fba"
    model_fba = doc_fba.getModel()
    objects = []
    ex_rids = utils.find_exchange_reactions(model_fba)
    for ex_rid, sid in iteritems(ex_rids):
        r = model_fba.getReaction(ex_rid)

        # lower & upper bound parameters
        r_fbc = r.getPlugin(builder.SBML_FBC_NAME)
        lb_id = r_fbc.getLowerFluxBound()
        fba_lb_id = fba_prefix + lb_id
        lb_value = model_fba.getParameter(lb_id).getValue()

        objects.extend([
            # default bounds from fba
            mc.Parameter(sid=fba_lb_id, value=lb_value, unit=UNIT_FLUX, constant=False),
            # uptake bounds (lower bound)
            mc.AssignmentRule(sid=lb_id, value="max({}, -{}*{}/dt)".format(fba_lb_id, compartment_id, sid)),
        ])
    mc.create_objects(model, objects)

    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)


def update_model(sbml_file, directory, doc_fba=None):
    """
        Submodel for dynamically updating the metabolite count/concentration.
        This updates the ode model based on the FBA fluxes.
    """
    doc = builder.template_doc_update(model_id)
    model = doc.getModel()
    update_notes = notes.format("""
        <h2>UPDATE submodel</h2>
        <p>Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.</p>
        """)
    utils.set_model_info(model, notes=update_notes, creators=creators, units=units, main_units=main_units)

    # compartment
    compartment_id = "blood"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=True)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_CONCENTRATION,
                                create_port=True)

    # update reactions
    # FIXME: weight with X (biomass)
    builder.create_update_reactions(model, model_fba=model_fba, formula="-{}", unit_flux=UNIT_FLUX,
                                    modifiers=[])

    # write SBML file
    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)


def top_model(sbml_file, directory, emds, doc_fba=None, validate=True):
    """ Create the top model. """
    top_notes = notes.format("""
    <h2>TOP model</h2>
    <p>Main comp DFBA model by combining fba, update and bounds
        model with additional kinetics in the top model.</p>
    """)
    # Necessary to change into directory with submodel files
    working_dir = os.getcwd()
    os.chdir(directory)

    doc = builder.template_doc_top(model_id, emds)
    model = doc.getModel()
    utils.set_model_info(model, notes=top_notes,
                         creators=creators, units=units, main_units=main_units)

    # dt
    builder.create_dfba_dt(model, time_unit=UNIT_TIME, create_port=False)

    # compartment
    compartment_id = "blood"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=False)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_CONCENTRATION,
                                create_port=False)
    # dummy species
    builder.create_dummy_species(model, compartment_id=compartment_id, unit=UNIT_CONCENTRATION)

    # exchange flux bounds
    builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=False)

    # dummy reactions & flux assignments
    builder.create_dummy_reactions(model, model_fba=model_fba, unit_flux=UNIT_FLUX)

    # replacedBy (fba reactions)
    builder.create_top_replacedBy(model, model_fba=model_fba)

    # replaced
    builder.create_top_replacements(model, model_fba, compartment_id=compartment_id)

    # write SBML file
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=validate)

    # change back into working dir
    os.chdir(working_dir)


def create_model(output_dir):
    """ Create all models.

    :return: directory where SBML files are located
    """
    directory = utils.versioned_directory(output_dir, version=version)

    print("FBA")
    doc_fba = fba_model(fba_file, directory)
    print("BOUNDS")
    bounds_model(bounds_file, directory, doc_fba=doc_fba)
    print("UPDATE")
    update_model(update_file, directory, doc_fba=doc_fba)

    emds = {
        "{}_fba".format(model_id): fba_file,
        "{}_bounds".format(model_id): bounds_file,
        "{}_update".format(model_id): update_file,
    }

    print("TOP")
    top_model(top_file, directory, emds, doc_fba=doc_fba, validate=False)

    # flatten top model
    print("FLATTENING")
    comp.flattenSBMLFile(sbml_path=pjoin(directory, top_file),
                         output_path=pjoin(directory, flattened_file))

    print("REPORTS")
    # create reports
    sbml_paths = [pjoin(directory, fname) for fname in
                  # [fba_file, bounds_file, update_file, top_file, flattened_file]]
                  [fba_file, bounds_file, update_file, top_file, flattened_file]]
    sbmlreport.create_sbml_reports(sbml_paths, directory, validate=False)
    return directory


if __name__ == "__main__":

    from sbmlutils.dfba.rbc.settings import out_dir
    create_model(output_dir=out_dir)


