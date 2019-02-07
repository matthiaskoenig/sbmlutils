# -*- coding=utf-8 -*-
"""
Demo kinetic network.
"""
from __future__ import absolute_import, print_function, division

try:
    import libsbml
    from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_LITRE
except ImportError:
    import tesbml as libsbml
    from tesbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_LITRE

import sbmlutils.factory as mc
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator.processes.reactiontemplate import ReactionTemplate

##############################################################
mid = 'tiny_example'
version = 1
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
main_units = {
    'time': UNIT_KIND_SECOND,
    'extent': 'mmole',
    'substance': 'mmole',
    'length': UNIT_KIND_METRE,
    'area': 'm2',
    'volume': UNIT_KIND_LITRE,
}
units = list()
compartments = list()
species = list()
parameters = list()
assignments = list()
rules = list()
reactions = list()
events = None

##############################################################
# Units
##############################################################
# units (kind, exponent, scale=0, multiplier=1.0)
units.extend([
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('mmole', [(UNIT_KIND_MOLE, 1, -3, 1.0)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('mmole_per_s', [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_SECOND, -1.0)]),
])
##############################################################
# Compartments
##############################################################
compartments.extend([
    mc.Compartment(sid='c', value=1e-15, unit=UNIT_KIND_LITRE, constant=True, name='cell compartment'),
])

##############################################################
# Species
##############################################################
species.extend([
    mc.Species(sid='glc', compartment='c', initialConcentration=5.0, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='glucose', sboTerm="SBO:0000247"),
    mc.Species(sid='atp', compartment='c', initialConcentration=3.0, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='ATP', sboTerm="SBO:0000247"),
    mc.Species(sid='g6p', compartment='c', initialConcentration=0.1, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='glucose-6-phosphate', sboTerm="SBO:0000247"),
    mc.Species(sid='adp', compartment='c', initialConcentration=0.8, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='ADP', sboTerm="SBO:0000247"),
    mc.Species(sid='hydron', compartment='c', initialConcentration=0, substanceUnit='mmole', constant=True,
               boundaryCondition=True, hasOnlySubstanceUnits=False, name='H+', sboTerm="SBO:0000247")
])

##############################################################
# Parameters
##############################################################
parameters.extend([

    mc.Parameter('Vmax', 1.0E-16, unit='mmole_per_s', constant=True, sboTerm="SBO:0000186", name="Vmax Hexokinase"),
    mc.Parameter('Km_glc', 0.5, unit='mM', constant=True, sboTerm="SBO:0000371", name="Km glucose"),
    mc.Parameter('Km_atp', 0.1, unit='mM', constant=True, sboTerm="SBO:0000371", name="Km ATP"),
])

##############################################################
# Assignments
##############################################################
assignments.extend([])

##############################################################
# Rules
##############################################################
rules.extend([])

##############################################################
# Reactions
##############################################################
reactions.extend([
    ReactionTemplate(
        rid='GK',
        name='Glucokinase',
        equation='glc + atp -> g6p + adp + hydron []',
        compartment='c',
        pars=[],
        rules=[],
        formula=('Vmax * (glc/(Km_glc+glc)) * (atp/(Km_atp+atp))', 'mmole_per_s')
    )
])