from sbmlutils.modelcreator import creator
from sbmlutils.factory import *

from sbmlutils.units import *
from sbmlutils.annotation.sbo import *


mid = "midazolam_model"
model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE)

units = [
    UNIT_mmole,
    UNIT_min,
    UNIT_m,
    UNIT_m2,
    UNIT_mmole_per_min,
]

compartments = [
    # FIXME: units liter
    Compartment("Vli", 1.5, name="liver", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE),
    Compartment("Vext", 1.0, name="extern", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE),
]

species = [
    Species("mid_ext", initialConcentration=0.0, name="midazolam (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
    Species("mid1oh_ext", initialConcentration=0.0, name="1-hydroxy-midazolam (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
    Species("mid", initialConcentration=0.0, name="midazolam",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
    Species("mid1oh", initialConcentration=0.0, name="1-hydroxy-midazolam",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
]

reactions = [
    Reaction("MIDIM",
             equation="mid_ext <-> mid",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("MIDIM_Vmax", 1.0, unit=UNIT_mmole_per_min),
             ],
             formula=("MIDIM_Vmax * (", UNIT_mmole_per_min)),

    Reaction("MID1OHEX",
             equation="mid1oh <-> mid1oh_ext",
             sboTerm=SBO_TRANSPORT_REACTION),
    Reaction("MIDOH",
             equation="mid -> mid1oh",
             sboTerm=SBO_BIOCHEMICAL_REACTION),

]

def create_model(target_dir):
    return creator.create_model(
        modules=['midazolam_model'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    create_model(target_dir=".")
