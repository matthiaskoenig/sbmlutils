# -*- coding=utf-8 -*-
"""
Test model to check the update of global depending parameters in Roadrunner.
Mainly volumes which are calculated based on other parameters.
"""
from __future__ import print_function, division, absolute_import

from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, UNIT_KIND_KILOGRAM, UNIT_KIND_METRE
from libsbml import XMLNode
from sbmlutils.modelcreator import templates
from sbmlutils import factory as fac
from . import Reactions

##############################################################
mid = 'basic'
version = 7
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Koenig Test Model</h1>
    <h2>Description</h2>
    <p>Test model.
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

units = []
compartments = []
species = []
parameters = []
names = []
assignments = []
rules = []
reactions = []

##############################################################
# Units
##############################################################
# units (kind, exponent, scale=0, multiplier=1.0)
units.extend([
    fac.Unit('s', [(UNIT_KIND_SECOND, 1.0)]),
    fac.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    fac.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    fac.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    fac.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    fac.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0), (UNIT_KIND_METRE, -3.0)]),
    fac.Unit('mole_per_s', [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0)]),
])

##############################################################
# Compartments
##############################################################
compartments.extend([
    fac.Compartment(sid='ext', value='Vol_e', unit='m3', constant=True, name="external"),
    fac.Compartment(sid='cyto', value='Vol_c', unit='m3', constant=False, name="cytosol"),
    fac.Compartment(sid='pm', value='A_m', unit="m2", constant=True, spatialDimensions=2, name="membrane"),
])

##############################################################
# Species
##############################################################
species.extend([
    fac.Species(sid='e__gal', compartment='ext', value=3.0, unit='mM', boundaryCondition=True, name='D-galactose'),
    fac.Species(sid='c__gal', compartment='cyto', value=0.00012, unit='mM', boundaryCondition=False,
                name='D-galactose'),
])

##############################################################
# Parameters
##############################################################
parameters.extend([
    fac.Parameter(sid='x_cell', value=25E-6, unit='m', constant=True, name="cell diameter"),
    fac.Parameter(sid='Vol_e', value=100E-14, unit='m3', constant=True, name="external volume"),
    fac.Parameter(sid='A_m', value=1.0, unit='m2', constant=True, name="membrane area"),
])

##############################################################
# Assignments
##############################################################
assignments.extend([
    fac.InitialAssignment(sid='Vol_c', value='x_cell*x_cell*x_cell', unit='m3'),
])

##############################################################
# Rules
##############################################################
rules.extend([])

##############################################################
# Reactions
##############################################################
reactions.extend([
    Reactions.GLUT2_GAL
])
