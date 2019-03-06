
from __future__ import print_function, absolute_import

import os
from os.path import join as pjoin

try:
    import libsbml
    from libsbml import (UNIT_KIND_SECOND, UNIT_KIND_METRE, UNIT_KIND_GRAM, UNIT_KIND_LITRE,
                         UNIT_KIND_ITEM, UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE)
except ImportError:
    import tesbml as libsbml
    from tesbml import (UNIT_KIND_SECOND, UNIT_KIND_METRE, UNIT_KIND_GRAM, UNIT_KIND_LITRE,
                         UNIT_KIND_ITEM, UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE)

from sbmlutils import sbmlio
from sbmlutils import comp
from sbmlutils import factory as mc
from sbmlutils.report import sbmlreport
from sbmlutils import annotation

from sbmlutils.dfba import builder
from sbmlutils.dfba import utils
from sbmlutils.dfba.diauxic_growth import settings

libsbml.XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################

DT_SIM = 0.1
notes = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Diauxic Growth Model</h1>
    <p><strong>Model version: {}</strong></p>

    {}

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
""".format(settings.VERSION, '{}')

creators = [
    mc.Creator(familyName='Koenig', givenName='Matthias', email='koenigmx@hu-berlin.de',
               organization='Humboldt University Berlin', site='https://livermetabolism.com')
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
    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)], name='hour'),
    mc.Unit('g', [(UNIT_KIND_GRAM, 1.0)], name="gram"),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)], name="meter"),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)], name="cubic meter"),
    mc.Unit('l', [(UNIT_KIND_LITRE, 1.0)], name="liter"),
    mc.Unit('mmol', [(UNIT_KIND_MOLE, 1.0, -3, 1.0)]),
    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_h', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                           (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_hg', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_GRAM, -1.0)]),

    mc.Unit('mmol_per_l', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                           (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('mmol_per_lg', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                           (UNIT_KIND_LITRE, -1.0), (UNIT_KIND_GRAM, -1.0)]),

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

# UNIT_CONCENTRATION_PER_G = 'mmol_per_lg'
UNIT_FLUX_PER_G = 'mmol_per_h'  # !!! FIXME (unit scaling between models)


def fba_model(sbml_file, directory, annotations=None):
    """ Create FBA submodel.

    FBA submodel in sbml:fbc-version 2.
    """
    fba_notes = notes.format("""
    <h2>FBA submodel</h2>
    <p>DFBA fba submodel. Unbalanced metabolites are encoded via exchange fluxes.</p>
    """)
    doc = builder.template_doc_fba(settings.MODEL_ID)
    model = doc.getModel()
    utils.set_model_info(model, notes=fba_notes, creators=creators, units=units, main_units=main_units)

    objects = [
        # compartments
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                       spatialDimensions=3),

        # species
        mc.Species(sid='Glcxt', name="glucose", initialConcentration=0.0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", initialConcentration=0.0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='O2', name="oxygen", initialConcentration=0.0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", initialConcentration=0.0, substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        # bounds
        mc.Parameter(sid="zero", name="zero bound", value=0.0, unit=UNIT_FLUX_PER_G, constant=True, sboTerm="SBO:0000612"),
        mc.Parameter(sid="ub_default", name="default upper bound", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX_PER_G,
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
    for sid in ['Ac', 'Glcxt', 'O2', 'X']:
        builder.create_exchange_reaction(model, species_id=sid, flux_unit=UNIT_FLUX_PER_G,
                                         exchange_type=builder.EXCHANGE)
    # set bounds for the exchange reactions
    p_lb_O2 = model.getParameter("lb_EX_O2")
    p_lb_O2.setValue(-15.0)  # FIXME: this is in mmol/gdw/h (biomass weighting of FBA)
    p_lb_Glcxt = model.getParameter("lb_EX_Glcxt")
    p_lb_Glcxt.setValue(-10.0)  # FIXME: this is in mmol/gdw/h

    # objective function
    model_fba = model.getPlugin(builder.SBML_FBC_NAME)
    mc.create_objective(model_fba, oid="biomass_max", otype="maximize",
                        fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0})

    # write SBML file
    if annotations:
        annotation.annotate_sbml_doc(doc, annotations)
    sbmlio.write_sbml(doc, filepath=pjoin(directory, sbml_file), validate=True)

    return doc