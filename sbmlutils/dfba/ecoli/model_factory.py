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
from sbmlutils.validation import check

from sbmlutils.dfba import builder
from sbmlutils.dfba import utils
from sbmlutils.dfba.ecoli.settings import fba_file, model_id, bounds_file, update_file, top_file, flattened_file

libsbml.XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################
version = 2
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
    # Read the model
    fba_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'data/ecoli_fba.xml')
    doc_fba = sbmlio.read_sbml(fba_path)

    # add comp
    doc_fba.enablePackage("http://www.sbml.org/sbml/level3/version1/comp/version1", "comp", True)
    doc_fba.setPackageRequired("comp", True)

    # add notes
    model = doc_fba.getModel()
    fba_notes = notes.format("""
        DFBA FBA submodel. Unbalanced metabolites are encoded via exchange fluxes.
    """)
    utils.add_generic_info(model, notes=fba_notes,
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

    # find exchange reactions (these species can be changed by the FBA)
    ex_rids = utils.find_exchange_reactions(model)
    from pprint import pprint
    pprint(ex_rids)

    # make unique upper and lower bounds for exchange reaction
    builder.update_exchange_reactions(model, ex_rids, flux_unit=UNIT_FLUX)


    # write SBML file
    sbmlio.write_sbml(doc_fba, filepath=pjoin(directory, sbml_file), validate=True)

    return doc_fba


def bounds_model(sbml_file, directory, doc_fba=None):
    """"
    Submodel for dynamically calculating the flux bounds.

    The dynamically changing flux bounds are the input to the
    FBA model.
    """
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
    model.setId("ecoli_bounds")
    model.setName("ecoli (BOUNDS)")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    utils.add_generic_info(model, notes=bounds_notes, creators=creators, units=units, main_units=main_units)

    objects = [
        # definition of min and max
        mc.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='minimum of arguments'),
        mc.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='maximum of arguments'),

        # hardcoded time step for the update of the bounds
        mc.Parameter(sid='dt', value=DT_SIM, unit=UNIT_TIME, name='fba timestep', constant=True, sboTerm="SBO:0000346"),

        # default bounds
        mc.Parameter(sid="zero", name="zero bound", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="lb_default", name="default lower bound", value=-1000.0, unit=UNIT_FLUX, constant=True,
                     sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_default", name="default upper bound", value=1000.0, unit=UNIT_FLUX, constant=True,
                     sboTerm="SBO:0000612"),

        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                   spatialDimension=3),
    ]
    port_sids = ['dt', 'bioreactor']


    # dynamic species
    fba_prefix = "fba"
    model_fba = doc_fba.getModel()
    ex_rids = utils.find_exchange_reactions(model_fba)
    for ex_rid in ex_rids:
        r = model_fba.getReaction(ex_rid)
        sid = r.getReactant(0).getSpecies()
        s = model_fba.getSpecies(sid)

        # exchange species to create
        objects.append(
            mc.Species(sid=sid, name=s.getName(), value=1.0, unit=UNIT_CONCENTRATION,
                       hasOnlySubstanceUnits=False, compartment="bioreactor")
        )
        # port of exchange species
        port_sids.append(sid)

        # lower & upper bound parameters
        r_fbc = r.getPlugin("fbc")
        lb_id = r_fbc.getLowerFluxBound()
        fba_lb_id = fba_prefix + lb_id
        lb_value = model_fba.getParameter(lb_id).getValue()
        ub_id = r_fbc.getUpperFluxBound()
        fba_ub_id = fba_prefix + ub_id
        ub_value = model_fba.getParameter(ub_id).getValue()

        objects.extend([
            # for assignments
            mc.Parameter(sid=lb_id, value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
            mc.Parameter(sid=ub_id, value=builder.LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000625"),
            # default bounds from fba
            mc.Parameter(sid=fba_lb_id, value=lb_value, unit=UNIT_FLUX, constant=False,
                         sboTerm="SBO:0000625"),
            mc.Parameter(sid=fba_ub_id, value=ub_value, unit=UNIT_FLUX, constant=False,
                         sboTerm="SBO:0000625")
        ])
        port_sids.extend([lb_id, ub_id])

        objects.extend([
            # uptake bounds (lower bound)
            mc.AssignmentRule(sid=lb_id, value="max({}, -{}*bioreactor/dt)".format(fba_lb_id, sid)),
            mc.AssignmentRule(sid=ub_id, value="{}".format(fba_ub_id)),
        ])

    mc.create_objects(model, objects)
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT, idRefs=port_sids)

    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)

def create_model(output_dir):
    """ Create all models.

    :return:
    """
    directory = utils.versioned_directory(output_dir, version=version)

    # create sbml
    doc_fba = fba_model(fba_file, directory)


    bounds_model(bounds_file, directory, doc_fba=doc_fba)
    '''
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

    '''
    return directory


if __name__ == "__main__":
    from sbmlutils.dfba.ecoli.settings import out_dir
    directory = create_model(output_dir=out_dir)
