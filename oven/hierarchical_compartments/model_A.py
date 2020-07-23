from copy import deepcopy
import templates

from sbmlutils.factory import *
from sbmlutils.units import *
from sbmlutils.annotation.sbo import *

mid = "model_A"
model_units = deepcopy(templates.MODEL_UNITS)
units = deepcopy(templates.UNITS)

compartments = [
    Compartment("ext", 1.0, name="compartment extern", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("ca", 1.0, name="compartment A", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE),

]
species = [
    Species("S_ext", initialConcentration=0.0,
            compartment="ext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False, port=True),

    Species("S", initialConcentration=0.0, name="midazolam",
            compartment="ca", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),

]
reactions = [
    # Transport reaction
    Reaction(
        "SIM",
         equation="S_ext <-> S",
         sboTerm=SBO_TRANSPORT_REACTION,
         pars=[
             Parameter("SIM_Vmax", 0.1, unit=UNIT_litre_per_min),
         ],
         formula=("SIM_Vmax * (S_ext - S)", UNIT_mmole_per_min)
    ),
]

