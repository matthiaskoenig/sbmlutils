"""
Hepatocyte template model.
"""
from __future__ import print_function, division
from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_PASCAL

##############################################################
mid = 'hepatocyte'
version = 1
main_units = {
    'time': 's',
    'extent': UNIT_KIND_MOLE,
    'substance': UNIT_KIND_MOLE,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}
units = dict()
species = dict()
parameters = dict()
names = dict()
assignments = dict()
rules = dict()
reactions = []

#########################################################################
# Units
##########################################################################
# units (kind, exponent, scale=0, multiplier=1.0)
units.update({
    's': [(UNIT_KIND_SECOND, 1.0)],
    'kg': [(UNIT_KIND_KILOGRAM, 1.0)],
    'm': [(UNIT_KIND_METRE, 1.0)],
    'm2': [(UNIT_KIND_METRE, 2.0)],
    'm3': [(UNIT_KIND_METRE, 3.0)],
    'per_s': [(UNIT_KIND_SECOND, -1.0)],
    'mole_per_s': [(UNIT_KIND_MOLE, 1.0),
                       (UNIT_KIND_SECOND, -1.0)],
    'mole_per_s_per_mM': [(UNIT_KIND_METRE, 3.0),
                       (UNIT_KIND_SECOND, -1.0) ],
    'mole_per_s_per_mM2': [(UNIT_KIND_MOLE, -1.0), (UNIT_KIND_METRE, 6.0),
                       (UNIT_KIND_SECOND, -1.0) ],
    'm_per_s': [(UNIT_KIND_METRE, 1.0),
                    (UNIT_KIND_SECOND, -1.0)],
    'm2_per_s': [(UNIT_KIND_METRE, 2.0),
                    (UNIT_KIND_SECOND, -1.0)],
    'm3_per_s': [(UNIT_KIND_METRE, 3.0),
                    (UNIT_KIND_SECOND, -1.0)],
    'mM': [(UNIT_KIND_MOLE, 1.0, 0),
                    (UNIT_KIND_METRE, -3.0)],
    'mM_s': [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, 1.0),
                    (UNIT_KIND_METRE, -3.0)],
    'per_mM': [(UNIT_KIND_METRE, 3.0),
                    (UNIT_KIND_MOLE, -1.0)],
    'per_m2': [(UNIT_KIND_METRE, -2.0)],
    'per_m3': [(UNIT_KIND_METRE, -3.0)],
    'kg_per_m3': [(UNIT_KIND_KILOGRAM, 1.0),
                    (UNIT_KIND_METRE, -3.0)],
    'm3_per_skg': [(UNIT_KIND_METRE, 3.0),
                    (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_SECOND, -1.0)],
    'Pa': [(UNIT_KIND_PASCAL, 1.0)],
    'Pa_s': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0)],
    'Pa_s_per_m4': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                     (UNIT_KIND_METRE, -4.0)],
    'Pa_s_per_m3': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                     (UNIT_KIND_METRE, -3.0)],
    'Pa_s_per_m2': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                     (UNIT_KIND_METRE, -2.0)],
    'm6_per_Pa2_s2': [(UNIT_KIND_PASCAL, -2.0), (UNIT_KIND_SECOND, -2.0),
                     (UNIT_KIND_METRE, 6.0)],
})
