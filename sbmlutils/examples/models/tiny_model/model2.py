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
mid = 'atp_balance'
version = 1
notes = libsbml.XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h2>Description</h2>
    <p>A minimal example for atp balance.</p>
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
functions = list()
compartments = list()
species = list()
parameters = list()
assignments = list()
rules = list()
reactions = list()
events = list()
constraints = list()

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
    mc.Compartment(sid='c', value=1e-5, unit=UNIT_KIND_LITRE, constant=True, name='cell compartment', port=True),
])

##############################################################
# Species
##############################################################
species.extend([
    mc.Species(sid='atp', compartment='c', initialConcentration=3.0, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='ATP', sboTerm="SBO:0000247", port=True),
    mc.Species(sid='adp', compartment='c', initialConcentration=0.8, substanceUnit='mmole', constant=False,
               boundaryCondition=False, hasOnlySubstanceUnits=False, name='ADP', sboTerm="SBO:0000247", port=True),
])

##############################################################
# Parameters
##############################################################
parameters.extend([

    mc.Parameter('Vmax', 1.0E-6, unit='mmole_per_s', constant=True, sboTerm="SBO:0000186", name="Vmax ATPase"),
    mc.Parameter('Km_atp', 0.1, unit='mM', constant=True, sboTerm="SBO:0000371", name="Km ATP"),
])

##############################################################
# FunctionDefinitions
##############################################################

##############################################################
# Assignments
##############################################################

##############################################################
# Rules
##############################################################
rules.extend([
    mc.AssignmentRule("a_sum", "atp + adp", unit="mM", name="ATP + ADP balance")
])

##############################################################
# Reactions
##############################################################
reactions.extend([
    ReactionTemplate(
        rid='ATPASE',
        name='ATP consumption',
        equation='atp -> adp []',
        compartment='c',
        pars=[],
        rules=[],
        formula=('Vmax* (atp/(Km_atp+atp))', 'mmole_per_s')
    )
])
