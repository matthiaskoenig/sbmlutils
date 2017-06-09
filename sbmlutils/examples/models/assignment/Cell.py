# -*- coding=utf-8 -*-
"""
PKPD example model
"""
from __future__ import absolute_import, print_function
from libsbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM

import sbmlutils.factory as fac
from sbmlutils.modelcreator import templates

##############################################################
creators = templates.creators
mid = 'assignment'
version = 3
notes = XMLNode.convertStringToXMLNode("""""")
main_units = {
    'time': 'h',
    'extent': 'mg',
    'substance': 'mg',
    'length': 'm',
    'area': 'm2',
    'volume': UNIT_KIND_LITRE,
}
units = list()
functions = list()
compartments = list()
species = list()
parameters = list()
names = list()
assignments = list()
rules = list()
rate_rules = list()
reactions = list()

#########################################################################
# Units
##########################################################################
# units (kind, exponent, scale=0, multiplier=1.0)
units.extend([

    fac.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)]),
    fac.Unit('kg', [(UNIT_KIND_GRAM, 1.0, 3, 1.0)]),
    fac.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    fac.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),

    fac.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),

    fac.Unit('mg', [(UNIT_KIND_GRAM, 1.0, -3, 1.0)]),
    fac.Unit('mg_per_litre', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                              (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
    fac.Unit('mg_per_g', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                          (UNIT_KIND_GRAM, -1.0, 0, 1.0)]),
    fac.Unit('mg_per_h', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                          (UNIT_KIND_SECOND, -1.0, 0, 3600)]),

    fac.Unit('litre_per_h', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                             (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    fac.Unit('litre_per_kg', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                              (UNIT_KIND_GRAM, -1.0, 3, 1.0)]),
    fac.Unit('mulitre_per_min_mg', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                                    (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_GRAM, -1.0, -3, 1.0)]),
    fac.Unit('ml_per_s', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                          (UNIT_KIND_SECOND, -1.0, 0, 1)]),

    # conversion factors
    fac.Unit('s_per_h', [(UNIT_KIND_SECOND, 1.0, 0, 1.0),
                         (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    fac.Unit('min_per_h', [(UNIT_KIND_SECOND, 1.0, 0, 60),
                           (UNIT_KIND_SECOND, -1.0, 0, 3600)]),

    fac.Unit('ml_per_litre', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                              (UNIT_KIND_LITRE, -1.0, 0, 1)]),
    fac.Unit('mulitre_per_g', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                               (UNIT_KIND_GRAM, -1.0, 0, 1)]),
])

##############################################################
# Functions
##############################################################


##############################################################
# Compartments
##############################################################


##############################################################
# Species
##############################################################


##############################################################
# Parameters
##############################################################
parameters.extend([
    # dosing
    fac.Parameter('Ave', 0, 'mg', False),
    fac.Parameter('D', 0, 'mg', False),
    fac.Parameter('IVDOSE', 0, 'mg', True),
    fac.Parameter('PODOSE', 100, 'mg', True),
    fac.Parameter('k1', 0.1, 'litre_per_h', True),

    # whole body data
    fac.Parameter('BW', 70, 'kg', True),
    fac.Parameter('FVve', 0.0514, 'litre_per_kg', True),
])

##############################################################
# Assignments
##############################################################
assignments.extend([
    # id, 'value', 'unit'
    fac.InitialAssignment('Ave', 'IVDOSE', 'mg'),
    fac.InitialAssignment('D', 'PODOSE', 'mg'),
])

##############################################################
# Rules
##############################################################
rules.extend([
    # id,  'value', 'unit'

    # concentrations
    fac.AssignmentRule('Cve', 'Ave/Vve', 'mg_per_litre'),
    # volumes
    fac.AssignmentRule('Vve', 'BW*FVve', UNIT_KIND_LITRE),
])

rate_rules.extend([
    fac.RateRule('Ave', '- k1*Cve', 'mg_per_h'),
])

##############################################################
# Reactions
##############################################################

reactions.extend([])
