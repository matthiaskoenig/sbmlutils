# -*- coding=utf-8 -*-
"""
Test model to check the update of global depending parameters in Roadrunner.
Mainly volumes which are calculated based on other parameters.
"""
from __future__ import print_function, division
from libsbml import XMLNode
from sbmlutils.modelcreator import templates
from Reactions import *

##############################################################
creators = templates.creators
mid = 'test'
version = 6
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Koenig Test Model</h1>
    <h2>Description</h2>
    <p>Test model.
    </p>
    """ + templates.terms_of_use + """
    </body>
    """)
units = dict()
compartments = dict()
species = dict()
parameters = dict()
names = dict()
assignments = dict()
rules = dict()
reactions = []

##############################################################
# Compartments
##############################################################
compartments.update({
    # id : ('spatialDimension', 'unit', 'constant', 'assignment')
    'ext': (3, 'm3', True, 'Vol_e'),
    'cyto': (3, 'm3', False, 'Vol_c'),
    'pm': (2, 'm2', True, 'A_m'),
})
names.update({
    'ext': 'external',
    'cyto': 'cytosol',
    'pm': 'membrane',
})

##############################################################
# Species
##############################################################
species.update({
    # id : ('compartment', 'value', 'unit', 'boundaryCondition')
    'e__gal':       ('ext', 3.0, 'mM', True),
    'c__gal':       ('cyto', 0.00012, 'mM', False),
})
names.update({
    'gal': 'D-galactose',
})

##############################################################
# Parameters
##############################################################
parameters.update({
    # id: ('value', 'unit', 'constant')
    'x_cell':       (25E-6, 'm', True),
    'Vol_e':        (100E-14, 'm3', True),
    'A_m':          (1.0, 'm2', True),
})
names.update({
    'x_cell': 'cell diameter',
    'Vol_e': 'external volume',
    'Vol_c': 'cell volume',
    'A_m': 'membrane area',
})

##############################################################
# Assignments
##############################################################
assignments.update({
    # id: ('value', 'unit')
    'Vol_c': ('x_cell*x_cell*x_cell', 'm3'),
})

##############################################################
# Rules
##############################################################
rules.update({
    # id: ('value', 'unit')
    # driving a boundaryCondition species
    # 'e__gal': ('1.0 mM * (1 dimensionless + sin(time/1 s))', 'mM'),
})
names.update({
})


##############################################################
# Reactions
##############################################################
reactions.extend([
    GLUT2_GAL
])
