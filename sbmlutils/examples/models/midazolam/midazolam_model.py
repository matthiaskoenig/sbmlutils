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
    UNIT_mM,
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
                 Parameter("MIDIM_Km", 3E-3, unit=UNIT_mM),
             ],
             formula=("MIDIM_Vmax * (mid_ext/(mid_ext + MIDIM_Km))", UNIT_mmole_per_min)),

    Reaction("MIDOH",
             equation="mid -> mid1oh",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                       Parameter("MIDOH_Vmax", 1.0, unit=UNIT_mmole_per_min),
                       Parameter("MIDOH_Km", 3E-3, unit=UNIT_mM),
                   ],
             formula=("MIDOH_Vmax * (mid/(mid + MIDOH_Km))", UNIT_mmole_per_min),
             ),

    Reaction("MID1OHEX",
             equation="mid1oh <-> mid1oh_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
               Parameter("MID1OHEX_Vmax", 1.0, unit=UNIT_mmole_per_min),  # 500 - 1500 pmol/min/mg
               Parameter("MID1OHEX_Km", 2.8E-3, unit=UNIT_mM),  # Thummel1996 (liver microsomes), 2-6µm
             ],
             formula=("MID1OHEX_Vmax * (mid1oh/(mid1oh + MID1OHEX_Km))", UNIT_mmole_per_min),
             ),
]

def create_model(target_dir):
    return creator.create_model(
        modules=['midazolam_model'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    create_model(target_dir=".")
