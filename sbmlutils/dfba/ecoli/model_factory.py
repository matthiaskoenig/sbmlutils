# -*- coding=utf-8 -*-
"""
Creating E.coli core model.
The core E. coli metabolic model is a subset of the genome-scale metabolic reconstruction iAF1260. 

It is described in EcoSal Chapter 10.2.1 - Reconstruction and Use of Microbial Metabolic Networks: 
the Core Escherichia coli Metabolic Model as an Educational Guide by Orth, Fleming, and Palsson (2010) link

* Biomass weighting of fluxes *
One challenge is that the biomass species is expressed in [g] whereas all other species have units [mol] in the
model. Normally the biomass should be converted with the molecular mass of the species, but
for the biomass the conversion factor is most of the time implicitely put into the biomass function.


Necessary to define a conversion factor for the species biomass X
4.6.7 The conversionFactor attribute (on species)
The attribute conversionFactor defines a conversion factor that applies to a particular species. The value
of the attribute must have the data type SIdRef and must be the identifier of a Parameter object instance
defined in the model. That Parameter object must be a constant, meaning its constant attribute must be set
to true. If a given Species object defnition defnes a value for its conversionFactor attribute, it takes
precedence over any factor dened by the Model object's conversionFactor attribute.

In SBML, the unit of measurement associated with a species' quantity can be different from the unit of
extent of reactions in the model. SBML avoids implicit unit conversions by providing an explicit way to
indicate any unit conversion that might be required.
The use of a conversion factor in computing the effects of reactions on a species' quantity
is explained in Section 4.11.7. Because the value of the conversionFactor
attribute is the identifer of a Parameter object, and because parameters can have units attached to them, the
transformation from reaction extent units to species units can be completely specified using this approach.

Note that the unit conversion factor is only applied when calculating the effect of a reaction on a species. It
is not used in any rules or other SBML constructs that aect the species, and it is also not used when the
value of the species is referenced in a mathematical expression.


"""
from __future__ import print_function, absolute_import
import os
from os.path import join as pjoin

try:
    import libsbml
    from libsbml import UNIT_KIND_SECOND, UNIT_KIND_GRAM, UNIT_KIND_LITRE, UNIT_KIND_METRE, UNIT_KIND_MOLE
except ImportError:
    import tesbml as libsbml
    from tesbml import UNIT_KIND_SECOND, UNIT_KIND_GRAM, UNIT_KIND_LITRE, UNIT_KIND_METRE, UNIT_KIND_MOLE


from sbmlutils import sbmlio
from sbmlutils import comp
from sbmlutils import factory as mc
from sbmlutils.report import sbmlreport
from sbmlutils.validation import check

from sbmlutils.dfba import builder
from sbmlutils.dfba import utils
from sbmlutils.dfba.ecoli import settings

libsbml.XMLOutputStream.setWriteTimestamp(False)

# units are defined on the upper and lower bounds of the the exchange reactions.

# TODO: biomass weighting of fluxes
# Necessary to implement alternative solutions of either weighting or not weighting the
# fluxes from the FBA network.
# The problem is that all the units are identical.

# FBA fluxes: [mmol/h/g]
# Biomass exchange flux [g(biomass)/h/g]


########################################################################
# General model information
########################################################################
biomass_weighting = False
print('-'*80)
print('BIOMASS WEIGHTING:', biomass_weighting)
print('-'*80)


DT_SIM = 0.1
notes = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>E.coli core DFBA model</h1>
    <p><strong>Model version: {}</strong></p>
    <p>{}</p>

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
""".format(settings.VERSION, '{}')

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
    mc.Unit('mmol_per_hg', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_GRAM, -1.0)]),
    mc.Unit('mmol_per_l', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                           (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('l_per_mmol', [(UNIT_KIND_LITRE, 1.0),
                           (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
    mc.Unit('g_per_l', [(UNIT_KIND_GRAM, 1.0),
                        (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('g_per_mmol', [(UNIT_KIND_GRAM, 1.0),
                           (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
    # mc.Unit('mmol_per_g', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
    #                       (UNIT_KIND_GRAM, 1.0)]),
]

UNIT_AMOUNT = 'mmol'
UNIT_AREA = 'm2'
UNIT_VOLUME = 'l'
UNIT_TIME = 'h'
UNIT_CONCENTRATION = 'mmol_per_l'
UNIT_FLUX = 'mmol_per_h'
UNIT_FLUX_PER_G = 'mmol_per_hg'


########################################################################################################
def fba_model(sbml_file, directory):
    """ Create FBA submodel.
    """
    # Read the model
    fba_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/ecoli_fba.xml')
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
    model.setId('ecoli_fba')
    model.setName('ecoli (FBA)')
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)

    # add units and information
    for species in model.getListOfSpecies():
        species.setInitialConcentration(0.0)
        species.setHasOnlySubstanceUnits(False)
        species.setUnits(UNIT_AMOUNT)
    for compartment in model.getListOfCompartments():
        compartment.setUnits(UNIT_VOLUME)


    # The ATPM (atp maintainance reactions creates many problems in the DFBA)
    # mainly resulting in infeasible solutions when some metabolites run out.
    # ATP -> ADP is part of the biomass, so we set the lower bound to zero
    r_ATPM = model.getReaction('ATPM')
    r_ATPM_fbc = r_ATPM.getPlugin(builder.SBML_FBC_NAME)
    lb_id = r_ATPM_fbc.getLowerFluxBound()
    model.getParameter(lb_id).setValue(0.0)  # 8.39 before

    # make unique upper and lower bounds for exchange reaction
    if not biomass_weighting:
        builder.update_exchange_reactions(model=model, flux_unit=UNIT_FLUX)
    else:
        builder.update_exchange_reactions(model=model, flux_unit=UNIT_FLUX_PER_G)

    # add exchange reaction for biomass (X)
    # we are adding the biomass component to the biomass function and create an
    # exchange reaction for it
    r_biomass = model.getReaction('BIOMASS_Ecoli_core_w_GAM')

    # FIXME: refactor in function
    # FIXME: annotate biomass species (SBO for biomass missing)
    mc.create_objects(model, [
        mc.Parameter(sid='cf_X', value=1.0, unit="g_per_mmol", name="biomass conversion factor", constant=True),
        mc.Species(sid='X', value=0.001, compartment='c', name='biomass', unit='g', hasOnlySubstanceUnits=True,
                   conversionFactor='cf_X')
    ])


    pr_biomass = r_biomass.createProduct()
    pr_biomass.setSpecies('X')
    pr_biomass.setStoichiometry(1.0)
    pr_biomass.setConstant(True)
    # FIXME: the flux units must fit to the species units.
    if not biomass_weighting:
        builder.create_exchange_reaction(model, species_id='X', flux_unit=UNIT_FLUX, exchange_type=builder.EXCHANGE_EXPORT)
    else:
        builder.create_exchange_reaction(model, species_id='X', flux_unit=UNIT_FLUX_PER_G, exchange_type=builder.EXCHANGE_EXPORT)
    # write SBML file
    sbmlio.write_sbml(doc_fba, filepath=pjoin(directory, sbml_file), validate=True)

    # Set kinetic laws to zero for kinetic simulation
    '''
    for reaction in model.getListOfReactions():
        ast_node = mc.ast_node_from_formula(model=model, formula='0 {}'.format(UNIT_FLUX))
        law = reaction.createKineticLaw()
        law.setMath(ast_node)
    '''

    return doc_fba


def bounds_model(sbml_file, directory, doc_fba=None):
    """"
    Submodel for dynamically calculating the flux bounds.

    The dynamically changing flux bounds are the input to the
    FBA model.

    The units of the exchange fluxes must fit to the transported species.
    """
    doc = builder.template_doc_bounds("ecoli")
    model = doc.getModel()

    bounds_notes = notes.format("""
    <h2>BOUNDS submodel</h2>
    <p>Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.</p>
    """)
    utils.set_model_info(model, notes=bounds_notes, creators=creators, units=units, main_units=main_units)

    # dt
    compartment_id = "bioreactor"
    builder.create_dfba_dt(model, time_unit=UNIT_TIME, create_port=True)

    # compartment
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=True)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_AMOUNT, create_port=True,
                                exclude_sids=['X'])
    # FIXME: define biomass separately, also port needed for biomass
    mc.create_objects(model, [
        mc.Parameter(sid='cf_X', value=1.0, unit="g_per_mmol", name="biomass conversion factor", constant=True),
        mc.Species(sid='X', value=0.001, compartment=compartment_id, name='biomass', unit='g', hasOnlySubstanceUnits=True,
                   conversionFactor='cf_X')
    ])


    # exchange & dynamic bounds
    if not biomass_weighting:
        builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=True)
        builder.create_dynamic_bounds(model, model_fba, unit_flux=UNIT_FLUX)
    else:
        builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX_PER_G, create_ports=True)
        builder.create_dynamic_bounds(model, model_fba, unit_flux=UNIT_FLUX_PER_G)

    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)


def update_model(sbml_file, directory, doc_fba=None):
    """
        Submodel for dynamically updating the metabolite count/concentration.
        This updates the ode model based on the FBA fluxes.
    """
    doc = builder.template_doc_update("ecoli")
    model = doc.getModel()
    update_notes = notes.format("""
        <h2>UPDATE submodel</h2>
        <p>Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.</p>
        """)
    utils.set_model_info(model, notes=update_notes, creators=creators, units=units, main_units=main_units)

    # compartment
    compartment_id = "bioreactor"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=True)

    # dynamic species
    model_fba = doc_fba.getModel()


    # creates all the exchange reactions, biomass must be handeled separately
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_AMOUNT, create_port=True)

    # FIXME: biomass via function
    mc.create_objects(model, [
        mc.Parameter(sid='cf_biomass', value=1.0, unit="g_per_mmol", name="biomass conversion factor", constant=True),
        mc.Species(sid='X', value=0.001, compartment='c', name='biomass', unit='g', hasOnlySubstanceUnits=True,
                   conversionFactor='cf_biomass')
    ])


    # update reactions
    # FIXME: weight with X (biomass)
    builder.create_update_reactions(model, model_fba=model_fba, formula="-{}", unit_flux=UNIT_FLUX,
                                    modifiers=[])

    # write SBML file
    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)


def top_model(sbml_file, directory, emds, doc_fba=None):
    """ Create the top model. """
    top_notes = notes.format("""
    <h2>TOP model</h2>
    <p>Main comp DFBA model by combining fba, update and bounds
        model with additional kinetics in the top model.</p>
    """)
    # Necessary to change into directory with submodel files
    working_dir = os.getcwd()
    os.chdir(directory)

    model_id = "ecoli"
    doc = builder.template_doc_top(model_id, emds)
    model = doc.getModel()
    utils.set_model_info(model, notes=top_notes,
                         creators=creators, units=units, main_units=main_units)

    # dt
    builder.create_dfba_dt(model, time_unit=UNIT_TIME, create_port=False)

    # compartment
    compartment_id = "bioreactor"
    builder.create_dfba_compartment(model, compartment_id=compartment_id, unit_volume=UNIT_VOLUME, create_port=False)

    # dynamic species
    model_fba = doc_fba.getModel()
    builder.create_dfba_species(model, model_fba, compartment_id=compartment_id, unit=UNIT_AMOUNT, create_port=False)

    # minimal medium with single carbon source
    initial_c = {
        'ac_e': 1.0,
        'acald_e': 1.0,
        'akg_e': 1.0,
        'co2_e': 1.0,
        'etoh_e': 1.0,
        'for_e': 1.0,
        'fru_e': 1.0,
        'fum_e': 1.0,
        'glc__D_e': 20.0,
        'gln__L_e': 10.0,
        'glu__L_e': 1.0,
        'h_e': 1.0,
        'h2o_e': 20.0,
        'lac__D_e': 1.0,
        'mal__L_e': 1.0,
        'nh4_e': 1.0,
        'o2_e': 1.0,
        'pi_e': 1.0,
        'pyr_e': 1.0,
        'succ_e': 1.0,
        'X': 0.001,
    }
    for sid, value in initial_c.items():
        species = model.getSpecies(sid)
        species.setInitialConcentration(value)

    # dummy species
    builder.create_dummy_species(model, compartment_id=compartment_id, unit=UNIT_AMOUNT)

    # exchange flux bounds
    builder.create_exchange_bounds(model, model_fba=model_fba, unit_flux=UNIT_FLUX, create_ports=False)

    # dummy reactions & flux assignments
    builder.create_dummy_reactions(model, model_fba=model_fba, unit_flux=UNIT_FLUX)

    # replacedBy (fba reactions)
    builder.create_top_replacedBy(model, model_fba=model_fba)

    # replaced
    builder.create_top_replacements(model, model_fba, compartment_id=compartment_id)

    # write SBML file
    sbmlio.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)

    # change back into working dir
    os.chdir(working_dir)


def create_model(output_dir):
    """ Create all models.

    :return: directory where SBML files are located
    """
    directory = utils.versioned_directory(output_dir, version=settings.VERSION)

    # create sbml
    import time
    t_start = time.time()

    doc_fba = fba_model(settings.FBA_LOCATION, directory)
    t_fba = time.time()
    print('{:<10}: {:3.2f}'.format('fba', t_fba-t_start))

    bounds_model(settings.BOUNDS_LOCATION, directory, doc_fba=doc_fba)
    t_bounds = time.time()
    print('{:<10}: {:3.2f}'.format('bounds', t_bounds-t_fba))

    update_model(settings.UPDATE_LOCATION, directory, doc_fba=doc_fba)
    t_update = time.time()
    print('{:<10}: {:3.2f}'.format('update', t_update-t_bounds))

    emds = {
        "ecoli_fba": settings.FBA_LOCATION,
        "ecoli_bounds": settings.BOUNDS_LOCATION,
        "ecoli_update": settings.UPDATE_LOCATION,
    }

    # flatten top model
    top_model(settings.TOP_LOCATION, directory, emds, doc_fba=doc_fba)
    t_top = time.time()
    print('{:<10}: {:3.2f}'.format('top', t_top-t_update))

    comp.flattenSBMLFile(sbml_path=pjoin(directory, settings.TOP_LOCATION),
                         output_path=pjoin(directory, settings.FLATTENED_LOCATION))
    t_flat = time.time()
    print('{:<10}: {:3.2f}'.format('flat', t_flat-t_top))

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
    sids = ['ac_e', 'acald_e', 'akg_e', 'co2_e', 'etoh_e', 'for_e', 'fru_e', 'fum_e', 'glc__D_e',
            'gln__L_e', 'glu__L_e', 'h_e', 'h2o_e', 'lac__D_e', 'mal__L_e', 'nh4_e', 'o2_e', 'pi_e',
            'pyr_e', 'succ_e', 'X']
    species_ids = ", ".join(sids)
    reaction_ids = ", ".join(['EX_{}'.format(sid) for sid in sids])
    create_sedml(settings.SEDML_LOCATION, settings.TOP_LOCATION, directory=directory,
                 dt=0.01, tend=3.5, species_ids=species_ids, reaction_ids=reaction_ids)

    return directory

########################################################################################################################
if __name__ == "__main__":
    create_model(output_dir=settings.OUT_DIR)
