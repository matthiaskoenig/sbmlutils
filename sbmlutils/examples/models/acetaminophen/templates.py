from sbmlutils.factory import *
from sbmlutils.units import *

UNITS = [
    UNIT_mmole,
    UNIT_min,
    UNIT_m,
    UNIT_m2,
    UNIT_mM,
    UNIT_mmole_per_min,
]

MODEL_UNITS = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE)