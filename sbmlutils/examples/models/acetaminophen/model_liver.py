from sbmlutils.modelcreator import creator
from sbmlutils.factory import *

from sbmlutils.units import *
from sbmlutils.annotation.sbo import *


mid = "paracetamol_liver"
model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE)

units = [
    UNIT_mmole,
    UNIT_mM,
    UNIT_min,
    UNIT_m,
    UNIT_m2,
    UNIT_mmole_per_min,
]

compartments = [
    # FIXME: units liter
    Compartment("Vli", 1.5, name="liver", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("Vext", 1.0, name="extern", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
]

species = [
    Species("apap_ext", initialConcentration=0.0, name="paracetamol (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapglu_ext", initialConcentration=0.0, name="paracetamol glucuronide (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapsul_ext", initialConcentration=0.0, name="paracetamol sulfate (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapcys_ext", initialConcentration=0.0, name="paracetamol cysteine (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapgsh_ext", initialConcentration=0.0, name="paracetamol glutathione (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapmer_ext", initialConcentration=0.0, name="paracetamol mercapturate (extern)",
            compartment="Vext", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apap", initialConcentration=0.0, name="paracetamol",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapglu", initialConcentration=0.0, name="paracetamol glucuronide",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapsul", initialConcentration=0.0, name="paracetamol sulfate",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapcys", initialConcentration=0.0, name="paracetamol cysteine",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapgsh", initialConcentration=0.0, name="paracetamol glutathione",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapmer", initialConcentration=0.0, name="paracetamol mercapturate",
            compartment="Vli", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
]

reactions = [
    Reaction("APAPIM",
             equation="apap_ext <-> apap",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("Import_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAP_Vmax* (apap/Vli)/(apap/Vli+Import_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGLU",
             equation="apap -> apapglu",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPGLU_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGLU_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGLU_Vmax * (apap/Vli)/(apap/Vli+APAPGLU_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPSUL",
             equation="apap -> apapsul",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPSUL_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPSUL_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPSUL_Vmax * (apap/Vli)/(apap/Vli+APAPSUL_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPCYS",
             equation="apap -> apapcys",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPCYS_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPCYS_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPCYS_Vmax * (apap/Vli)/(apap/Vli+APAPCYS_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGSH",
             equation="apap -> apapgsh",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPGSH_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGSH_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGSH_Vmax * (apap/Vli)/(apap/Vli+APAPGSH_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPMER",
             equation="apap -> apapmer",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPMER_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPMER_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPMER_Vmax * (apap/Vli)/(apap/Vli+APAPMER_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGLUEXP",
             equation="apapglu <-> apapglu_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGLUEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGLUEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGLUEXP_Vmax* (apapglu/Vli)/(apapglu/Vli+APAPGLUEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPSULEXP",
             equation="apapsul <-> apapsul_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPSULEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPSULEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPSULEXP_Vmax * (apapsul/Vli)/(apapsul/Vli+APAPSULEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPCYSEXP",
             equation="apapcys <-> apapcys_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPCYSEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPCYSEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPCYSEXP_Vmax * (apapcys/Vli)/(apapcys/Vli+APAPCYSEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGSHEXP",
             equation="apapgsh <-> apapgsh_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGSHEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGSHEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGSHEXP_Vmax * (apapgsh/Vli)/(apapgsh/Vli+APAPGSHEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPMEREXP",
             equation="apapmer <-> apapmer_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPMEREXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPMEREXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPMEREXP_Vmax* (apapmer/Vli)/(apapmer/Vli+APAPMEREXP_Km) ", UNIT_mmole_per_min)),
]

def create_model(target_dir):
    return creator.create_model(
        modules=['model_liver'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    create_model(target_dir="./models")
