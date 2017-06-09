# -*- coding=utf-8 -*-
"""
Demo kinetic network.
"""
from __future__ import print_function, division, absolute_import

import libsbml
import sbmlutils.factory as mc
from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, UNIT_KIND_KILOGRAM, UNIT_KIND_METRE
from sbmlutils.modelcreator import templates

from . import Reactions as R

##############################################################
mid = 'Koenig_demo'
version = 12
notes = libsbml.XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Koenig Demo Metabolism</h1>
    <h2>Description</h2>
    <p>This is a demonstration model in
    <a href="http://sbmlutils.org" target="_blank" title="Access the definition of the SBML file format.">
    SBML</a>&#160;format.
    </p>
    """ + templates.terms_of_use + """
    </body>
    """)
creators = templates.creators
main_units = {
    'time': 's',
    'extent': UNIT_KIND_MOLE,
    'substance': UNIT_KIND_MOLE,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
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
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0)]),
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0), (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('mole_per_s', [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0)]),
])
##############################################################
# Compartments
##############################################################
compartments.extend([
    mc.Compartment(sid='e', value=1e-06, unit='m3', constant=False, name='external compartment'),
    mc.Compartment(sid='c', value=1e-06, unit='m3', constant=False, name='cell compartment'),
    mc.Compartment(sid='m', value=1, unit='m2', constant=False, spatialDimensions=2, name='plasma membrane'),
])

##############################################################
# Species
##############################################################
species.extend([
    mc.Species(sid='c__A', compartment='c', value=0, unit='mM', boundaryCondition=False, name='A'),
    mc.Species(sid='c__B', compartment='c', value=0.0, unit='mM', boundaryCondition=False, name='B'),
    mc.Species(sid='c__C', compartment='c', value=0.0, unit='mM', boundaryCondition=False, name='C'),
    mc.Species(sid='e__A', compartment='e', value=10.0, unit='mM', boundaryCondition=False, name='A'),
    mc.Species(sid='e__B', compartment='e', value=0.0, unit='mM', boundaryCondition=False, name='B'),
    mc.Species(sid='e__C', compartment='e', value=0.0, unit='mM', boundaryCondition=False, name='C'),
])

##############################################################
# Parameters
##############################################################
parameters.extend([
    mc.Parameter('scale_f', value=1E-6, unit='-', constant=True, name='metabolic scaling factor'),
    mc.Parameter('Vmax_bA', 5.0, 'mole_per_s', True),
    mc.Parameter('Km_A', 1.0, 'mM', True),
    mc.Parameter('Vmax_bB', 2.0, 'mole_per_s', True),
    mc.Parameter('Km_B', 0.5, 'mM', True),
    mc.Parameter('Vmax_bC', 2.0, 'mole_per_s', True),
    mc.Parameter('Km_C', 3.0, 'mM', True),
    mc.Parameter('Vmax_v1', 1.0, 'mole_per_s', True),
    mc.Parameter('Keq_v1', 10.0, '-', True),
    mc.Parameter('Vmax_v2', 0.5, 'mole_per_s', True),
    mc.Parameter('Vmax_v3', 0.5, 'mole_per_s', True),
    mc.Parameter('Vmax_v4', 0.5, 'mole_per_s', True),
    mc.Parameter('Keq_v4', 2.0, '-', True)
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
    R.bA, R.bB, R.bC, R.v1, R.v2, R.v3, R.v4
])
