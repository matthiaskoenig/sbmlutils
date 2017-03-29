"""
Hepatocyte template model.
"""
from __future__ import print_function, division

from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_PASCAL
from sbmlutils import factory as mc

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
units = list()
species = list()
parameters = list()
names = list()
assignments = list()
rules = list()
reactions = list()

#########################################################################
# Units
##########################################################################
# units (kind, exponent, scale=0, multiplier=1.0)
units.extend([
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0)]),
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    mc.Unit('per_s', [(UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('mole_per_s', [(UNIT_KIND_MOLE, 1.0),
                           (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('mole_per_s_per_mM', [(UNIT_KIND_METRE, 3.0),
                                  (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('mole_per_s_per_mM2', [(UNIT_KIND_MOLE, -1.0), (UNIT_KIND_METRE, 6.0),
                                   (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('m_per_s', [(UNIT_KIND_METRE, 1.0),
                        (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('m2_per_s', [(UNIT_KIND_METRE, 2.0),
                         (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('m3_per_s', [(UNIT_KIND_METRE, 3.0),
                         (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0),
                   (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('mM_s', [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, 1.0),
                     (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('per_mM', [(UNIT_KIND_METRE, 3.0),
                       (UNIT_KIND_MOLE, -1.0)]),
    mc.Unit('per_m2', [(UNIT_KIND_METRE, -2.0)]),
    mc.Unit('per_m3', [(UNIT_KIND_METRE, -3.0)]),
    mc.Unit('kg_per_m3', [(UNIT_KIND_KILOGRAM, 1.0),
                          (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('m3_per_skg', [(UNIT_KIND_METRE, 3.0),
                           (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('Pa', [(UNIT_KIND_PASCAL, 1.0)]),
    mc.Unit('Pa_s', [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0)]),
    mc.Unit('Pa_s_per_m4', [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                            (UNIT_KIND_METRE, -4.0)]),
    mc.Unit('Pa_s_per_m3', [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                            (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('Pa_s_per_m2', [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                            (UNIT_KIND_METRE, -2.0)]),
    mc.Unit('m6_per_Pa2_s2', [(UNIT_KIND_PASCAL, -2.0), (UNIT_KIND_SECOND, -2.0),
                              (UNIT_KIND_METRE, 6.0)]),
])
