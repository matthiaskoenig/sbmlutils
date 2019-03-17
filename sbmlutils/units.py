from libsbml import UNIT_KIND_AMPERE, UNIT_KIND_AVOGADRO, \
    UNIT_KIND_BECQUEREL, UNIT_KIND_CANDELA, UNIT_KIND_CELSIUS, UNIT_KIND_COULOMB, UNIT_KIND_DIMENSIONLESS, \
    UNIT_KIND_FARAD, UNIT_KIND_GRAM, UNIT_KIND_GRAY, UNIT_KIND_HERTZ, UNIT_KIND_METER, UNIT_KIND_ITEM, \
    UNIT_KIND_KELVIN, UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE, UNIT_KIND_NEWTON, UNIT_KIND_OHM, UNIT_KIND_VOLT, \
    UNIT_KIND_SECOND, UNIT_KIND_METRE, UNIT_KIND_LITRE

from sbmlutils.factory import Unit

UNIT_kg = Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)])
UNIT_m = Unit('m', [(UNIT_KIND_METRE, 1.0)])
UNIT_m2 = Unit('m2', [(UNIT_KIND_METRE, 2.0)])
UNIT_m3 = Unit('m3', [(UNIT_KIND_METRE, 3.0)])

UNIT_mM = Unit('mM', [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_LITRE, -1.0)])
UNIT_mmole = Unit('mmole', [(UNIT_KIND_MOLE, 1, -3, 1.0)])
UNIT_mmole_per_min = Unit('mole_per_min', [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 60)])
UNIT_mmole_per_s = Unit('mmole_per_s', [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_SECOND, -1.0)])
UNIT_mole_per_s = Unit('mole_per_s', [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0)])

UNIT_s = Unit('s', [(UNIT_KIND_SECOND, 1.0)])
UNIT_min = Unit('min', [(UNIT_KIND_SECOND, 1.0, 0, 60)])
UNIT_h = Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)])

UNIT_per_h = Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)])
UNIT_mg = Unit('mg', [(UNIT_KIND_GRAM, 1.0, -3, 1.0)])
UNIT_mg_per_h = Unit('mg_per_h', [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)])


__all__ = [
    'UNIT_KIND_AMPERE', 'UNIT_KIND_AVOGADRO',
    'UNIT_KIND_BECQUEREL', 'UNIT_KIND_CANDELA', 'UNIT_KIND_CELSIUS', 'UNIT_KIND_COULOMB', 'UNIT_KIND_DIMENSIONLESS',
    'UNIT_KIND_FARAD', 'UNIT_KIND_GRAM', 'UNIT_KIND_GRAY', 'UNIT_KIND_HERTZ', 'UNIT_KIND_METER', 'UNIT_KIND_ITEM',
    'UNIT_KIND_KELVIN', 'UNIT_KIND_KILOGRAM', 'UNIT_KIND_MOLE', 'UNIT_KIND_NEWTON', 'UNIT_KIND_OHM', 'UNIT_KIND_VOLT',
    'UNIT_KIND_SECOND', 'UNIT_KIND_METRE', 'UNIT_KIND_LITRE',
    'UNIT_min',
    'UNIT_m',
    'UNIT_m2',
    'UNIT_m3',
    'UNIT_mM',
    'UNIT_mmole',
    'UNIT_mmole_per_min',
    'UNIT_mmole_per_s',
    'UNIT_mole_per_s',
    'UNIT_kg',
    'UNIT_s',
    'UNIT_h',
    'UNIT_per_h',
    'UNIT_mg',
    'UNIT_mg_per_h',
]
