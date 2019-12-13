from copy import deepcopy
from sbmlutils.examples.models.midazolam import templates

from sbmlutils.modelcreator import creator
from sbmlutils.factory import *
from sbmlutils.units import *
from sbmlutils.annotation.sbo import *


mid = "midazolam_liver"

model_units = deepcopy(templates.MODEL_UNITS)
units = deepcopy(templates.UNITS)

compartments = [
    # FIXME: units liter
    Compartment("Vli", 1.5, name="liver", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("Vext", 1.0, name="extern", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
]

species = [
    Species("mid_ext", initialConcentration=0.0, name="midazolam (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("mid1oh_ext", initialConcentration=0.0, name="1-hydroxy-midazolam (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),

    Species("mid", initialConcentration=0.0, name="midazolam (liver)",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True),
    Species("mid1oh", initialConcentration=0.0, name="1-hydroxy-midazolam (liver)",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True),
]

reactions = [
    #Transport reactions
    Reaction("MIDIM",
             equation="mid_ext <-> mid",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("MIDIM_Vmax", 3E-3, unit=UNIT_mmole_per_min),
                 Parameter("MIDIM_Km", 6E-2, unit=UNIT_mM),
             ],
             formula=("MIDIM_Vmax * (mid_ext/Vext/(mid_ext/Vext + MIDIM_Km))", UNIT_mmole_per_min)
             ),

    Reaction("MID1OHEX",
             equation="mid1oh <-> mid1oh_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
               Parameter("MID1OHEX_Vmax", 3E-3, unit=UNIT_mmole_per_min),  # 500 - 1500 pmol/min/mg
               Parameter("MID1OHEX_Km", 6E-2, unit=UNIT_mM),  # Thummel1996 (liver microsomes), 2-6µm
             ],
             formula=("MID1OHEX_Vmax * (mid1oh/Vli/(mid1oh/Vli + MID1OHEX_Km))", UNIT_mmole_per_min),
             ),

    #Biochemical reactions
    Reaction("MIDOH",
             equation="mid -> mid1oh",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("MIDOH_Vmax", 2.5E-3, unit=UNIT_mmole_per_min),
                 Parameter("MIDOH_Km", 6E-2, unit=UNIT_mM),
             ],
             formula=("MIDOH_Vmax * (mid/Vli/(mid/Vli + MIDOH_Km))", UNIT_mmole_per_min),
             ),
]

def create_model(target_dir):
    return creator.create_model(
        modules=['model_liver'],
        target_dir=target_dir,
        create_report=True
    )

