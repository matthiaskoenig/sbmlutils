from sbmlutils.modelcreator import creator
from sbmlutils.factory import *

from sbmlutils.units import *
from sbmlutils.annotation.sbo import *


mid = "paracetamol_model_liver"
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
                 Parameter("Import_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAP_Vmax* (apap_ext-apap)/(apap_ext-apap+Import_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGLU",
             equation="apap -> apap_glu",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPGLU_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGLU_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGLU_Vmax * (apap)/(apap+APAPGLU_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPSUL",
             equation="apap -> apap_sul",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPSUL_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPSUL_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPSUL_Vmax * (apap)/(apap+APAPSUL_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPCYS",
             equation="apap -> apap_cys",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPCYS_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPCYS_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPCYS_Vmax * (apap)/(apap+APAPCYS_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGSH",
             equation="apap -> apap_gsh",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPGSH_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGSH_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGSH_Vmax * (apap)/(apap+APAPGSH_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPMER",
             equation="apap -> apap_mer",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPMER_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPMER_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPMER_Vmax * (apap)/(apap+APAPMER_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGLUEXP",
             equation="apap_glu <-> apap_glu_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGLUEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGLUEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGLUEXP_Vmax* (apap_glu-apap_glu_ext)/(apap_glu-apap_glu_ext+APAPGLUEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPSULEXP",
             equation="apap_sul <-> apap_sul_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPSULEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPSULEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPSULEXP_Vmax * (apap_sul-apap_sul_ext)/(apap_sul-apap_sul_ext+APAPSULEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPCYSEXP",
             equation="apap_cys <-> apap_cys_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPCYSEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPCYSEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPCYSEXP_Vmax * (apap_cys-apap_cys_ext)/(apap_cys-apap_cys_ext+APAPCYSEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGSHEXP",
             equation="apap_gsh <-> apap_gsh_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGSHEXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPGSHEXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPGSHEXP_Vmax * (apap_gsh-apap_gsh_ext)/(apap_gsh-apap_gsh_ext+APAPGSHEXP_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPMEREXP",
             equation="apap_mer <-> apap_mer_ext",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPMEREXP_Vmax", 1.0, unit=UNIT_mmole_per_min),
                 Parameter("APAPMEREXP_Km", 1.0, unit=UNIT_mM),
             ],
             formula=("APAPMEREXP_Vmax* (apap_mer-apap_mer_ext)/(apap_mer-apap_mer_ext+APAPMEREXP_Km) ", UNIT_mmole_per_min)),
]

def create_model(target_dir):
    return creator.create_model(
        modules=['paracetamol_model_liver'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    create_model(target_dir=".")
