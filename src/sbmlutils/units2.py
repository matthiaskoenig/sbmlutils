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

from sbmlutils.factory import UnitDefinition


UNIT_kg = UnitDefinition("kg", [(UNIT_KIND_KILOGRAM, 1.0)], port=True)
UNIT_m = UnitDefinition("m", [(UNIT_KIND_METRE, 1.0)], port=True)
UNIT_m2 = UnitDefinition("m2", [(UNIT_KIND_METRE, 2.0)], port=True)
UNIT_m3 = UnitDefinition("m3", [(UNIT_KIND_METRE, 3.0)], port=True)

UNIT_mM = UnitDefinition("mM", [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_LITRE, -1.0)], port=True)
UNIT_mmole = UnitDefinition("mmole", [(UNIT_KIND_MOLE, 1, -3, 1.0)], port=True)
UNIT_g_per_mole = UnitDefinition(
    "g_per_mole",
    [(UNIT_KIND_GRAM, 1.0, 0, 1.0), (UNIT_KIND_MOLE, -1.0, 0, 1.0)],
    port=True,
)

UNIT_mole_per_min = UnitDefinition(
    "mole_per_min", [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 60)], port=True
)
UNIT_mmole_per_min = UnitDefinition(
    "mmole_per_min",
    [(UNIT_KIND_MOLE, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 60)],
    port=True,
)
UNIT_mmole_per_min_l = UnitDefinition(
    "mmole_per_min_l",
    [
        (UNIT_KIND_MOLE, 1.0, -3, 1.0),
        (UNIT_KIND_SECOND, -1.0, 0, 60),
        (UNIT_KIND_LITRE, -1.0, 0, 1),
    ],
    port=True,
)
UNIT_mmole_per_min_kg = UnitDefinition(
    "mmole_per_min_kg",
    [
        (UNIT_KIND_MOLE, 1.0, -3, 1.0),
        (UNIT_KIND_SECOND, -1.0, 0, 60),
        (UNIT_KIND_KILOGRAM, -1.0, 0, 1),
    ],
    port=True,
)

UNIT_mmole_per_s = UnitDefinition(
    "mmole_per_s", [(UNIT_KIND_MOLE, 1, -3, 1.0), (UNIT_KIND_SECOND, -1.0)], port=True
)
UNIT_mole_per_s = UnitDefinition(
    "mole_per_s", [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0)], port=True
)
UNIT_s = UnitDefinition("s", [(UNIT_KIND_SECOND, 1.0)], port=True)
UNIT_min = UnitDefinition("min", [(UNIT_KIND_SECOND, 1.0, 0, 60)], port=True)
UNIT_hr = UnitDefinition("hr", [(UNIT_KIND_SECOND, 1.0, 0, 3600)], port=True)

UNIT_per_s = UnitDefinition("per_s", [(UNIT_KIND_SECOND, -1.0)], port=True)
UNIT_per_min = UnitDefinition("per_min", [(UNIT_KIND_SECOND, -1.0, 0, 60)], port=True)
UNIT_per_hr = UnitDefinition("per_hr", [(UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True)
UNIT_per_kg = UnitDefinition("per_kg", [(UNIT_KIND_GRAM, -1.0, 0, 1000)], port=True)
UNIT_per_l = UnitDefinition("per_l", [(UNIT_KIND_LITRE, -1.0)], port=True)

UNIT_per_mmole = UnitDefinition(
    "per_mmole",
    [(UNIT_KIND_MOLE, -1, -3, 1)],
    port=True,
)

UNIT_mg = UnitDefinition("mg", [(UNIT_KIND_GRAM, 1.0, -3, 1.0)], port=True)
UNIT_mg_per_hr = UnitDefinition(
    "mg_per_hr",
    [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)],
    port=True,
)
UNIT_mg_per_day = UnitDefinition(
    "mg_per_day",
    [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600 * 24)],
    port=True,
)

UNIT_ml = UnitDefinition("ml", [(UNIT_KIND_LITRE, 1.0, -3, 1.0)], metaId="meta_ml", port=True)

UNIT_litre_per_min = UnitDefinition(
    "litre_per_min",
    [(UNIT_KIND_LITRE, 1.0, 0, 1), (UNIT_KIND_SECOND, -1.0, 0, 60)],
    port=True,
)
UNIT_litre_per_mmole = UnitDefinition(
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
    "UNIT_per_kg",
    "UNIT_per_l",
    "UNIT_per_mmole",
    "UNIT_mg",
    "UNIT_mg_per_hr",
    "UNIT_mg_per_day",
    "UNIT_ml",
    "UNIT_litre_per_min",
    "UNIT_litre_per_mmole",
]
