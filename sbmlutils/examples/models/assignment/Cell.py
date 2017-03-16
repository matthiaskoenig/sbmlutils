# -*- coding=utf-8 -*-
"""
PKPD example model
"""
import sbmlutils.factory as mc
from libsbml import UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM
from libsbml import XMLNode
from sbmlutils.modelcreator import templates

##############################################################
creators = templates.creators
mid = 'assignment'
version = 2
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

    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)]),
    mc.Unit('kg', [(UNIT_KIND_GRAM, 1.0, 3, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),

    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),

    mc.Unit('mg', [(UNIT_KIND_GRAM, 1.0, -3, 1.0)]),
    mc.Unit('mg_per_litre', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                             (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
    mc.Unit('mg_per_g', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                         (UNIT_KIND_GRAM, -1.0, 0, 1.0)]),
    mc.Unit('mg_per_h', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                         (UNIT_KIND_SECOND, -1.0, 0, 3600)]),

    mc.Unit('litre_per_h', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('litre_per_kg', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                             (UNIT_KIND_GRAM, -1.0, 3, 1.0)]),
    mc.Unit('mulitre_per_min_mg', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                                   (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_GRAM, -1.0, -3, 1.0)]),
    mc.Unit('ml_per_s', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                         (UNIT_KIND_SECOND, -1.0, 0, 1)]),

    # conversion factors
    mc.Unit('s_per_h', [(UNIT_KIND_SECOND, 1.0, 0, 1.0),
                        (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('min_per_h', [(UNIT_KIND_SECOND, 1.0, 0, 60),
                          (UNIT_KIND_SECOND, -1.0, 0, 3600)]),

    mc.Unit('ml_per_litre', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                             (UNIT_KIND_LITRE, -1.0, 0, 1)]),
    mc.Unit('mulitre_per_g', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
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
    mc.Parameter('Ave', 0, 'mg', False),
    mc.Parameter('D', 0, 'mg', False),
    mc.Parameter('IVDOSE', 0, 'mg', True),
    mc.Parameter('PODOSE', 100, 'mg', True),
    mc.Parameter('k1', 0.1, 'litre_per_h', True),

    # whole body data
    mc.Parameter('BW', 70, 'kg', True),
    mc.Parameter('FVve', 0.0514, 'litre_per_kg', True),
])

##############################################################
# Assignments
##############################################################
assignments.extend([
    # id, 'value', 'unit'
    mc.InitialAssignment('Ave', 'IVDOSE', 'mg'),
    mc.InitialAssignment('D', 'PODOSE', 'mg'),
])

##############################################################
# Rules
##############################################################
rules.extend([
    # id,  'value', 'unit'

    # concentrations
    mc.AssignmentRule('Cve', 'Ave/Vve', 'mg_per_litre'),
    # volumes
    mc.AssignmentRule('Vve', 'BW*FVve', UNIT_KIND_LITRE),
])

rate_rules.extend([
    mc.RateRule('Ave', '- k1*Cve', 'mg_per_h'),
])

##############################################################
# Reactions
##############################################################

reactions.extend([])
