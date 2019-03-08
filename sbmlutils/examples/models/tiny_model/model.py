# -*- coding=utf-8 -*-
"""
Demo kinetic network.
"""

import libsbml
from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_LITRE
import sbmlutils.factory as mc
import sbmlutils.layout as layout
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator.processes.reactiontemplate import ReactionTemplate

# -----------------------------------------------------------------------------
mid = 'tiny_example'
version = 8
notes = libsbml.XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h2>Description</h2>
    <p>A minimal example in <a href="http://sbml.org" target="_blank">SBML</a> format.
    </p>
    <div class="dc:provenance">The content of this model has been carefully created in a manual research effort.</div>
    <div class="dc:publisher">This file has been created by
    <a href="http://sbml.org" title="SBML team" target="_blank">SBML team</a>.</div>

    <h2>Terms of use</h2>
    <div class="dc:rightsHolder">Copyright © 2019 SBML team.</div>
    <div class="dc:license">
        <p>Redistribution and use of any part of this model, with or without modification, are permitted provided
        that the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions and
          the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of conditions
          and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>
        This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
        </p>
    </div>
    </body>
    """)
creators = templates.creators

units = list()
functions = list()
compartments = list()
species = list()
parameters = list()
assignments = list()
rules = list()
reactions = list()
events = list()
constraints = list()
layouts = list()

# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------
main_units = {
    'time': UNIT_KIND_SECOND,
    'extent': 'mmole',
    'substance': 'mmole',
    'length': UNIT_KIND_METRE,
    'area': 'm2',
    'volume': UNIT_KIND_LITRE,
}
units.extend([
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('mmole', [(UNIT_KIND_MOLE, 1, -3, 1.0)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('mmole_per_s', [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_SECOND, -1.0)]),
])
# -----------------------------------------------------------------------------
# Compartments
# -----------------------------------------------------------------------------
compartments.extend([
    mc.Compartment(sid='c', value=1e-5, unit=UNIT_KIND_LITRE, constant=True, name='cell compartment', port=True),
])

# -----------------------------------------------------------------------------
# Species
# -----------------------------------------------------------------------------
species.extend([

    mc.Species(sid='glc', compartment='c', initialConcentration=5.0, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='glucose', sboTerm="SBO:0000247", port=True),
    mc.Species(sid='g6p', compartment='c', initialConcentration=0.1, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='glucose-6-phosphate', sboTerm="SBO:0000247"),
    mc.Species(sid='atp', compartment='c', initialConcentration=3.0, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='ATP', sboTerm="SBO:0000247", port=True),
    mc.Species(sid='adp', compartment='c', initialConcentration=0.8, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='ADP', sboTerm="SBO:0000247", port=True),
    mc.Species(sid='phos', compartment='c', initialConcentration=0, substanceUnit='mmole', constant=True,
               boundaryCondition=True, hasOnlySubstanceUnits=False, name='P', sboTerm="SBO:0000247", port=True),
    mc.Species(sid='hydron', compartment='c', initialConcentration=0, substanceUnit='mmole', constant=True,
               boundaryCondition=True, hasOnlySubstanceUnits=False, name='H+', sboTerm="SBO:0000247"),
    mc.Species(sid='h2o', compartment='c', initialConcentration=0, substanceUnit='mmole', constant=True,
               boundaryCondition=True, hasOnlySubstanceUnits=False, name='H2O', sboTerm="SBO:0000247")
])

# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
parameters.extend([

    mc.Parameter('Vmax_GK', 1.0E-6, unit='mmole_per_s', constant=True,
                 sboTerm="SBO:0000186", name="Vmax Glucokinase"),
    mc.Parameter('Km_glc', 0.5, unit='mM', constant=True,
                 sboTerm="SBO:0000371", name="Km glucose"),
    mc.Parameter('Km_atp', 0.1, unit='mM', constant=True,
                 sboTerm="SBO:0000371", name="Km ATP"),
    mc.Parameter('Vmax_ATPASE', 1.0E-6, unit='mmole_per_s', constant=True,
                 sboTerm="SBO:0000186", name="Vmax ATPase"),
])

# -----------------------------------------------------------------------------
# FunctionDefinitions
# -----------------------------------------------------------------------------
functions.extend([
    mc.Function(sid="f_oscillation", value="lambda(x, cos(x/10 dimensionless))")
])

# -----------------------------------------------------------------------------
# Assignments
# -----------------------------------------------------------------------------
assignments.extend([
    mc.InitialAssignment('glc', "4.5 mM")
])

# -----------------------------------------------------------------------------
# Rules
# -----------------------------------------------------------------------------
rules.extend([
    mc.AssignmentRule("a_sum", "atp + adp", unit="mM", name="ATP + ADP balance")
])

# -----------------------------------------------------------------------------
# Reactions
# -----------------------------------------------------------------------------
reactions.extend([
    ReactionTemplate(
        rid='GK',
        name='Glucokinase',
        equation='glc + atp -> g6p + adp + hydron []',
        compartment='c',
        pars=[],
        rules=[],
        formula=('Vmax_GK * (glc/(Km_glc+glc)) * (atp/(Km_atp+atp))', 'mmole_per_s'),
        sboTerm="SBO:0000176"
    ),
    ReactionTemplate(
        rid='ATPASE',
        name='ATP consumption',
        equation='atp + h2o -> adp + phos + hydron []',
        compartment='c',
        pars=[],
        rules=[],
        formula=('Vmax_ATPASE * (atp/(Km_atp+atp)) * f_oscillation(time/ 1 second)', 'mmole_per_s'),
        sboTerm="SBO:0000176"
    )
])

# -----------------------------------------------------------------------------
# Events
# -----------------------------------------------------------------------------
events.extend([
    mc.Event("event_1", trigger="time%200 second == 0 second", assignments={"glc": "4.5 mM", "atp": "3.0 mM", "adp": "0.8 mM", "g6p": "0.1 mM"},
             name="reset concentrations")
])

# -----------------------------------------------------------------------------
# Constraints
# -----------------------------------------------------------------------------
events.extend([
    mc.Constraint("constraint_1", math="atp >= 0 mM", message='<body xmlns="http://www.w3.org/1999/xhtml">ATP must be non-negative</body>')
])


# -----------------------------------------------------------------------------
# Layout
# -----------------------------------------------------------------------------
layouts.extend([
    layout.Layout(sid="layout_1", name="Layout 1", width=700.0, height=700.0,
              compartment_glyphs=[
                layout.CompartmentGlyph("glyph_c", compartment="c", x=5, y=5, w=690, h=690)
              ],
              species_glyphs=[
                    layout.SpeciesGlyph('glyph_atp', species="atp", x=450, y=50, w=50, h=20, text="ATP"),
                    layout.SpeciesGlyph('glyph_adp', species="adp", x=450, y=450,  w=50, h=20, text="ADP"),
                    layout.SpeciesGlyph('glyph_glc', species="glc", x=50, y=50,  w=50, h=20, text="glucose"),
                    layout.SpeciesGlyph('glyph_g6p', species="g6p", x=50, y=450,  w=50, h=20, text="glucose-6-phosphate"),
                    layout.SpeciesGlyph('glyph_hydron', species="hydron", x=250, y=450,  w=50, h=20, text="hydron"),
              ],
              reaction_glyphs=[
                    layout.ReactionGlyph('glyph_GK', reaction="GK", x=250+25, y=250+10, h=0, w=0, text="GK",
                                     species_glyphs={
                                         "glyph_atp": layout.LAYOUT_ROLE_SIDESUBSTRATE,
                                         "glyph_adp": layout.LAYOUT_ROLE_SIDEPRODUCT,
                                         "glyph_glc": layout.LAYOUT_ROLE_SUBSTRATE,
                                         "glyph_g6p": layout.LAYOUT_ROLE_PRODUCT,
                                         "glyph_hydron": layout.LAYOUT_ROLE_SIDEPRODUCT
                                     }),
                    layout.ReactionGlyph('glyph_ATPASE', reaction="ATPASE", x=650+25, y=250+10, h=0, w=0, text="ATPase",
                                     species_glyphs={
                                         "glyph_atp": layout.LAYOUT_ROLE_SUBSTRATE,
                                         "glyph_adp": layout.LAYOUT_ROLE_PRODUCT,
                                     }),
              ])
])
