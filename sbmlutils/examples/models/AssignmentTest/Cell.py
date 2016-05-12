# -*- coding=utf-8 -*-
"""
PKPD example model
"""
from libsbml import UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM
from libsbml import XMLNode
from sbmlutils.modelcreator import templates

##############################################################
creators = templates.creators
mid = 'AssignmentTest'
version = 1
notes = XMLNode.convertStringToXMLNode("""""")
main_units = {
    'time': 'h',
    'extent': 'mg',
    'substance': 'mg',
    'length': 'm',
    'area': 'm2',
    'volume': UNIT_KIND_LITRE,
}
units = dict()
functions = dict()
compartments = dict()
species = dict()
parameters = dict()
names = dict()
assignments = dict()
rules = dict()
rate_rules = dict()
reactions = []

#########################################################################
# Units
##########################################################################
# units (kind, exponent, scale=0, multiplier=1.0)
units.update({
    'h': [(UNIT_KIND_SECOND, 1.0, 0, 3600)],
    'kg': [(UNIT_KIND_GRAM, 1.0, 3, 1.0)],
    'm': [(UNIT_KIND_METRE, 1.0)],
    'm2': [(UNIT_KIND_METRE, 2.0)],

    'per_h': [(UNIT_KIND_SECOND, -1.0, 0, 3600)],

    'mg': [(UNIT_KIND_GRAM, 1.0, -3, 1.0)],
    'mg_per_litre': [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0, 0, 1.0)],
    'mg_per_g': [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                     (UNIT_KIND_GRAM, -1.0, 0, 1.0)],
    'mg_per_h': [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                 (UNIT_KIND_SECOND, -1.0, 0, 3600)],

    'litre_per_h': [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                     (UNIT_KIND_SECOND, -1.0, 0, 3600)],
    'litre_per_kg': [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                     (UNIT_KIND_GRAM, -1.0, 3, 1.0)],
    'mulitre_per_min_mg': [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                           (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_GRAM, -1.0, -3, 1.0)],
    'ml_per_s': [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                 (UNIT_KIND_SECOND, -1.0, 0, 1)],

    # conversion factors
    's_per_h': [(UNIT_KIND_SECOND, 1.0, 0, 1.0),
                (UNIT_KIND_SECOND, -1.0, 0, 3600)],
    'min_per_h': [(UNIT_KIND_SECOND, 1.0, 0, 60),
                  (UNIT_KIND_SECOND, -1.0, 0, 3600)],

    'ml_per_litre': [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                     (UNIT_KIND_LITRE, -1.0, 0, 1)],
    'mulitre_per_g': [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                      (UNIT_KIND_GRAM, -1.0, 0, 1)],

})

##############################################################
# Functions
##############################################################
functions.update({
    # id : ('assignment')
})
names.update({
})

##############################################################
# Compartments
##############################################################
compartments.update({
    # id : ('spatialDimension', 'unit', 'constant', 'assignment')
})

names.update({
})

##############################################################
# Species
##############################################################
species.update({
    # id : ('compartment', 'value', 'unit', 'boundaryCondition')

})

names.update({

})

##############################################################
# Parameters
##############################################################
parameters.update({
    # id: ('value', 'unit', 'constant')

    # dosing
    'Ave': (0, 'mg', False),
    'D': (0, 'mg', False),
    'IVDOSE': (0, 'mg', True),
    'PODOSE': (100, 'mg', True),
    'k1': (0.1, 'litre_per_h', True),

    # whole body data
    'BW': (70, 'kg', True),
    'FVve': (0.0514, 'litre_per_kg', True),

})
names.update({
})

##############################################################
# Assignments
##############################################################
assignments.update({
    # id: ('value', 'unit')
    'Ave': ('IVDOSE', 'mg'),
    'D': ('PODOSE', 'mg'),
})

##############################################################
# Rules
##############################################################

rules.update({
    # id: ('value', 'unit')
    # concentrations
    'Cve': ('Ave/Vve', 'mg_per_litre'),
    # volumes
    'Vve': ('BW*FVve', UNIT_KIND_LITRE),


})
names.update({
})

rate_rules.update({
    'Ave': ('- k1*Cve', 'mg_per_h'),

})


##############################################################
# Reactions
##############################################################

reactions.extend([])
