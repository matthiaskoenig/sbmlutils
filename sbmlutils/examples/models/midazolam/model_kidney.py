from copy import deepcopy
from sbmlutils.examples.models.midazolam import templates

from sbmlutils.modelcreator import creator
from sbmlutils.factory import *
from sbmlutils.units import *
from sbmlutils.annotation.sbo import *


mid = "midazolam_kidney"
model_units = deepcopy(templates.MODEL_UNITS)
units = deepcopy(templates.UNITS)
ports = []


compartments = [
    Compartment("Vext", 1.0, name="extern", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("Vki", 1.0, name="kidney", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("Vurine", 1.0, name="urine", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True)
]

species = [
    #external species
    Species("mid1oh_ext", initialConcentration=0.0, name="1-hydroxy-midazolam (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),

    #Species in kidney
    Species("mid1oh", initialConcentration=0.0, name="1-hydroxy-midazolam (kidney)",
            compartment="Vki", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True),

    #Species in urine
    Species("mid1oh_urine", initialConcentration=0.0, name="1-hydroxy-midazolam (urine)",
            compartment="Vurine", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
]
# create concentration variables

reactions = [
    #import reactions
    Reaction("MID1OHIM",
             equation="mid1oh_ext <-> mid1oh",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("MID1OHIM_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("MID1OHIM_Km", 1.0, unit=UNIT_mM)
                 ],
             formula=("MID1OHIM_Vmax * (mid1oh_ext/Vext / (mid1oh_ext/Vext + MID1OHIM_Km))", UNIT_mmole_per_min)
             ),

    #export reactions
    Reaction("MID1OHEX",
             equation="mid1oh -> mid1oh_urine",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
               Parameter("MID1OHEX_Vmax", 1.0, unit=UNIT_mmole_per_min),
               Parameter("MID1OHEX_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("MID1OHEX_Vmax * (mid1oh/Vki / (mid1oh/Vki + MID1OHEX_Km))", UNIT_mmole_per_min),
             ),
]

def create_model(target_dir):
    return creator.create_model(
        modules=['model_kidney'],
        target_dir=target_dir,
        create_report=True
    )

