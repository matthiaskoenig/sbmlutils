from copy import deepcopy
from pkdb_models.models.midazolam.models import templates

from sbmlutils.modelcreator import creator
from sbmlutils.factory import *
from sbmlutils.units import *
from sbmlutils.annotation.sbo import *

mid = "model_top"
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


def create_model(target_dir):
    return creator.create_model(
        modules=['model_A'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    from pkdb_models.models.midazolam import MODEL_BASE_PATH
    create_model(MODEL_BASE_PATH)
