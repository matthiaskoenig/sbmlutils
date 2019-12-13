from copy import deepcopy
from sbmlutils.examples.models.midazolam import templates

from sbmlutils.modelcreator import creator
from sbmlutils.factory import *
from sbmlutils.units import *
from sbmlutils.annotation.sbo import *

mid = "midazolam_intestine"
model_units = deepcopy(templates.MODEL_UNITS)
units = deepcopy(templates.UNITS)

compartments = [
    Compartment("Vext", 1.0, name="extern", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("Vint", 1.5, name="intestine", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
]

species = [
    Species("mid_ext", initialConcentration=0.0, name="midazolam (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("mid1oh_ext", initialConcentration=0.0, name="1-hydroxy-midazolam (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("mid", initialConcentration=0.0, name="midazolam (intestine)",
            compartment="Vint", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True),
    Species("mid1oh", initialConcentration=0.0, name="1-hydroxy-midazolam (intestine)",
            compartment="Vint", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True),
]

reactions = [
    Reaction("MIDIM",
             equation="mid_ext <-> mid",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("MIDIM_Vmax", 0.5E-5, unit=UNIT_mmole_per_min),
                 Parameter("MIDIM_Km", 4.0E-3, unit=UNIT_mM),
             ],
             formula=("MIDIM_Vmax * (mid_ext/Vext/(mid_ext/Vext + MIDIM_Km))", UNIT_mmole_per_min)),

    Reaction("MID1OHEX",
             equation="mid1oh <-> mid1oh_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
               Parameter("MID1OHBL_Vmax", 0.5E-5, unit=UNIT_mmole_per_min),
               Parameter("MID1OHBL_Km", 4E-3, unit=UNIT_mM),
             ],
             formula=("MID1OHBL_Vmax * (mid1oh/Vint/(mid1oh/Vint + MID1OHBL_Km))", UNIT_mmole_per_min),
             ),

    Reaction("MIDOH",
             equation="mid -> mid1oh",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                       Parameter("MIDOH_Vmax", 0.5E-5, unit=UNIT_mmole_per_min),   #Thummel1996; 500 - 800 pmol/min/mg
                       Parameter("MIDOH_Km", 4.0E-3, unit=UNIT_mM),             #Thummel1996; 3.3 - 4.3 umol/l
                   ],
             formula=("MIDOH_Vmax * (mid/Vint/(mid/Vint + MIDOH_Km))", UNIT_mmole_per_min),
             ),
]

def create_model(target_dir):
    return creator.create_model(
        modules=['model_intestine'],
        target_dir=target_dir,
        create_report=True
    )
