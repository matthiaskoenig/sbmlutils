"""Module for unit information."""

from libsbml import (
    UNIT_KIND_AMPERE,
    UNIT_KIND_AVOGADRO,
    UNIT_KIND_BECQUEREL,
    UNIT_KIND_CANDELA,
    UNIT_KIND_CELSIUS,
    UNIT_KIND_COULOMB,
    UNIT_KIND_DIMENSIONLESS,
    UNIT_KIND_FARAD,
    UNIT_KIND_GRAM,
    UNIT_KIND_GRAY,
    UNIT_KIND_HERTZ,
    UNIT_KIND_ITEM,
    UNIT_KIND_KELVIN,
    UNIT_KIND_KILOGRAM,
    UNIT_KIND_LITRE,
    UNIT_KIND_METER,
    UNIT_KIND_METRE,
    UNIT_KIND_MOLE,
    UNIT_KIND_NEWTON,
    UNIT_KIND_OHM,
    UNIT_KIND_SECOND,
    UNIT_KIND_VOLT,
)

from sbmlutils.factory import Unit


UNIT_kg = Unit("kg", [(UNIT_KIND_KILOGRAM, 1.0)], port=True)
UNIT_m = Unit("m", [(UNIT_KIND_METRE, 1.0)], port=True)
UNIT_m2 = Unit("m2", [(UNIT_KIND_METRE, 2.0)], port=True)
UNIT_m3 = Unit("m3", [(UNIT_KIND_METRE, 3.0)], port=True)

UNIT_mM = Unit("mM", [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_LITRE, -1.0)], port=True)
UNIT_mmole = Unit("mmole", [(UNIT_KIND_MOLE, 1, -3, 1.0)], port=True)
UNIT_g_per_mole = Unit(
    "g_per_mole",
    [(UNIT_KIND_GRAM, 1.0, 0, 1.0), (UNIT_KIND_MOLE, -1.0, 0, 1.0)],
    port=True,
)

UNIT_mole_per_min = Unit(
    "mole_per_min", [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 60)], port=True
)
UNIT_mmole_per_min = Unit(
    "mmole_per_min",
    [(UNIT_KIND_MOLE, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 60)],
    port=True,
)
UNIT_mmole_per_min_l = Unit(
    "mmole_per_min_l",
    [
        (UNIT_KIND_MOLE, 1.0, -3, 1.0),
        (UNIT_KIND_SECOND, -1.0, 0, 60),
        (UNIT_KIND_LITRE, -1.0, 0, 1),
    ],
    port=True,
)
UNIT_mmole_per_min_kg = Unit(
    "mmole_per_min_kg",
    [
        (UNIT_KIND_MOLE, 1.0, -3, 1.0),
        (UNIT_KIND_SECOND, -1.0, 0, 60),
        (UNIT_KIND_KILOGRAM, -1.0, 0, 1),
    ],
    port=True,
)

UNIT_mmole_per_s = Unit(
    "mmole_per_s", [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_SECOND, -1.0)], port=True
)
UNIT_mole_per_s = Unit(
    "mole_per_s", [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0)], port=True
)
UNIT_s = Unit("s", [(UNIT_KIND_SECOND, 1.0)], port=True)
UNIT_min = Unit("min", [(UNIT_KIND_SECOND, 1.0, 0, 60)], port=True)
UNIT_hr = Unit("hr", [(UNIT_KIND_SECOND, 1.0, 0, 3600)], port=True)

UNIT_per_s = Unit("per_s", [(UNIT_KIND_SECOND, -1.0)], port=True)
UNIT_per_min = Unit("per_min", [(UNIT_KIND_SECOND, -1.0, 0, 60)], port=True)
UNIT_per_hr = Unit("per_hr", [(UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True)

UNIT_mg = Unit("mg", [(UNIT_KIND_GRAM, 1.0, -3, 1.0)], port=True)
UNIT_mg_per_hr = Unit(
    "mg_per_hr",
    [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)],
    port=True,
)
UNIT_mg_per_day = Unit(
    "mg_per_day",
    [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600 * 24)],
    port=True,
)

UNIT_ml = Unit("ml", [(UNIT_KIND_LITRE, 1.0, -3, 1.0)], metaId="meta_ml", port=True)

UNIT_litre_per_min = Unit(
    "litre_per_min",
    [(UNIT_KIND_LITRE, 1.0, 0, 1), (UNIT_KIND_SECOND, -1.0, 0, 60)],
    port=True,
)
UNIT_litre_per_mmole = Unit(
    "litre_per_mmole",
    [(UNIT_KIND_LITRE, 1.0, 0, 1), (UNIT_KIND_MOLE, -1, -3, 1)],
    port=True,
)


__all__ = [
    "UNIT_KIND_AMPERE",
    "UNIT_KIND_AVOGADRO",
    "UNIT_KIND_BECQUEREL",
    "UNIT_KIND_CANDELA",
    "UNIT_KIND_CELSIUS",
    "UNIT_KIND_COULOMB",
    "UNIT_KIND_DIMENSIONLESS",
    "UNIT_KIND_FARAD",
    "UNIT_KIND_GRAM",
    "UNIT_KIND_GRAY",
    "UNIT_KIND_HERTZ",
    "UNIT_KIND_METER",
    "UNIT_KIND_ITEM",
    "UNIT_KIND_KELVIN",
    "UNIT_KIND_KILOGRAM",
    "UNIT_KIND_MOLE",
    "UNIT_KIND_NEWTON",
    "UNIT_KIND_OHM",
    "UNIT_KIND_VOLT",
    "UNIT_KIND_SECOND",
    "UNIT_KIND_METRE",
    "UNIT_KIND_LITRE",
    "UNIT_min",
    "UNIT_m",
    "UNIT_m2",
    "UNIT_m3",
    "UNIT_mM",
    "UNIT_mmole",
    "UNIT_g_per_mole",
    "UNIT_mmole_per_min",
    "UNIT_mmole_per_min_l",
    "UNIT_mmole_per_min_kg",
    "UNIT_mole_per_min",
    "UNIT_mmole_per_s",
    "UNIT_mole_per_s",
    "UNIT_kg",
    "UNIT_s",
    "UNIT_min",
    "UNIT_hr",
    "UNIT_per_s",
    "UNIT_per_min",
    "UNIT_per_hr",
    "UNIT_mg",
    "UNIT_mg_per_hr",
    "UNIT_mg_per_day",
    "UNIT_ml",
    "UNIT_litre_per_min",
    "UNIT_litre_per_mmole",
]
