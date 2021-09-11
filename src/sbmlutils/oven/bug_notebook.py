from sbmlutils.factory import *
from sbmlutils.units import *


md: ModelDict = {
    "sid": "distrib_assignment",
    "packages": ["distrib"],
    "model_units": ModelUnits(
        time=UNIT_hr,
        extent=UNIT_KIND_MOLE,
        substance=UNIT_KIND_MOLE,
        length=UNIT_m,
        area=UNIT_m2,
        volume=UNIT_KIND_LITRE,
    ),
    "units": [UNIT_hr, UNIT_m, UNIT_m2, UNIT_mM],
    "parameters": [Parameter(sid="p1", value=0.0, unit=UNIT_mM)],
    "assignments": [
        InitialAssignment("p1", "normal(0 mM, 1 mM)"),
    ],
}
print(md)

# create model and print SBML
model = Model(**md)
print(model.get_sbml())
