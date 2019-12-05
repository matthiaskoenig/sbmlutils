from sbmlutils.modelcreator import creator
from sbmlutils.factory import *

from sbmlutils.units import *
from sbmlutils.annotation.sbo import *


mid = "paracetamol_model"
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
    Species("apap_ext", initialConcentration=0.0, name="paracetamol (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
    Species("apap_glu_ext", initialConcentration=0.0, name="paracetamol glucuronide (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_sul_ext", initialConcentration=0.0, name="paracetamol sulfate (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_cys_ext", initialConcentration=0.0, name="paracetamol cysteine (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_gsh_ext", initialConcentration=0.0, name="paracetamol glutathione (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_mer_ext", initialConcentration=0.0, name="paracetamol mercapturate (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
    Species("apap", initialConcentration=0.0, name="paracetamol",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
    Species("apap_glu", initialConcentration=0.0, name="paracetamol glucuronide",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_sul", initialConcentration=0.0, name="paracetamol sulfate",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_cys", initialConcentration=0.0, name="paracetamol cysteine",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_gsh", initialConcentration=0.0, name="paracetamol glutathione",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
     Species("apap_mer", initialConcentration=0.0, name="paracetamol mercapturate",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=False),
]

reactions = [
    Reaction("APAPIM",
             equation="apap_ext <-> apap",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAP_Vmax", 1.0, unit=UNIT_mmole_per_min),
             ],
             formula=("APAP_Vmax * (apap_ext-apap)/((apap_ext-apap+1)) ", UNIT_mmole_per_min)),
    Reaction("APAPGLU",
             equation="apap -> apap_glu",
             sboTerm=SBO_BIOCHEMICAL_REACTION),
    Reaction("APAPSUL",
             equation="apap -> apap_sul",
             sboTerm=SBO_BIOCHEMICAL_REACTION),
    Reaction("APAPCYS",
             equation="apap -> apap_cys",
             sboTerm=SBO_BIOCHEMICAL_REACTION),
    Reaction("APAPGSH",
             equation="apap -> apap_gsh",
             sboTerm=SBO_BIOCHEMICAL_REACTION),
    Reaction("APAPMER",
             equation="apap -> apap_mer",
             sboTerm=SBO_BIOCHEMICAL_REACTION),
    Reaction("APAPGLUEXP",
             equation="apap_glu <-> apap_glu_ext",
             sboTerm=SBO_TRANSPORT_REACTION),
    Reaction("APAPSULEXP",
             equation="apap_sul <-> apap_sul_ext",
             sboTerm=SBO_TRANSPORT_REACTION),
    Reaction("APAPCYSEXP",
             equation="apap_cys <-> apap_cys_ext",
             sboTerm=SBO_TRANSPORT_REACTION),
    Reaction("APAPGSHEXP",
             equation="apap_gsh <-> apap_gsh_ext",
             sboTerm=SBO_TRANSPORT_REACTION),
    Reaction("APAPMEREXP",
             equation="apap_mer <-> apap_mer_ext",
             sboTerm=SBO_TRANSPORT_REACTION),


]

def create_model(target_dir):
    return creator.create_model(
        modules=['paracetamol_model'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    create_model(target_dir=".")
