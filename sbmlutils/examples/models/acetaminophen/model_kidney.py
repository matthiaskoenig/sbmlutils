from sbmlutils.modelcreator import creator
from sbmlutils.factory import *

from sbmlutils.units import *
from sbmlutils.annotation.sbo import *

mid = "paracetamol_kidney"
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
    Compartment("Vki", 1.0, name="kidney", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("Vext", 1.0, name="extern", sboTerm=SBO_PHYSICAL_COMPARTMENT,
                unit=UNIT_KIND_LITRE, port=True),
    Compartment("Vur", 1.0, name="urine", sboTerm=SBO_PHYSICAL_COMPARTMENT,
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
            compartment="Vki", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapglu", initialConcentration=0.0, name="paracetamol glucuronide",
            compartment="Vki", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapsul", initialConcentration=0.0, name="paracetamol sulfate",
            compartment="Vki", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapcys", initialConcentration=0.0, name="paracetamol cysteine",
            compartment="Vki", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapgsh", initialConcentration=0.0, name="paracetamol glutathione",
            compartment="Vki", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapmer", initialConcentration=0.0, name="paracetamol mercapturate",
            compartment="Vki", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apap_urine", initialConcentration=0.0, name="paracetamol (urine)",
            compartment="Vur", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapglu_urine", initialConcentration=0.0, name="paracetamol glucuronide (urine)",
            compartment="Vur", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapsul_urine", initialConcentration=0.0, name="paracetamol sulfate (urine)",
            compartment="Vur", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapcys_urine", initialConcentration=0.0, name="paracetamol cysteine (urine)",
            compartment="Vur", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapgsh_urine", initialConcentration=0.0, name="paracetamol glutathione (urine)",
            compartment="Vur", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
    Species("apapmer_urine", initialConcentration=0.0, name="paracetamol mercapturate (urine)",
            compartment="Vur", substanceUnit=UNIT_mmole, hasOnlySubstanceUnits=True, port=True),
]

reactions = [

    # import reactions

    Reaction("APAPIM",
             equation="apap_ext <-> apap",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAP_Import_Vmax", 0.005, unit=UNIT_mmole_per_min),
                 Parameter("APAP_Import_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAP_Import_Vmax* (apap_ext/Vext)/(apap_ext/Vext+APAP_Import_Km) ", UNIT_mmole_per_min)),

    Reaction("APAPGLUIM",
             equation="apapglu_ext <-> apapglu",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGLU_Import_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPGLU_Import_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPGLU_Import_Vmax* (apapglu_ext/Vext)/(apapglu_ext/Vext+APAPGLU_Import_Km) ", UNIT_mmole_per_min)),

    Reaction("APAPSULIM",
             equation="apapsul_ext <-> apapsul",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPSUL_Import_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPSUL_Import_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPSUL_Import_Vmax* (apapsul_ext/Vext)/(apapsul_ext/Vext+APAPSUL_Import_Km) ", UNIT_mmole_per_min)),

    Reaction("APAPCYSIM",
             equation="apapcys_ext <-> apapcys",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPCYS_Import_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPCYS_Import_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPCYS_Import_Vmax* (apapcys_ext/Vext)/(apapcys_ext/Vext+APAPCYS_Import_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGSHIM",
             equation="apapgsh_ext <-> apapgsh",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGSH_Import_Vmax",0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPGSH_Import_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPGSH_Import_Vmax* (apapgsh_ext/Vext)/(apapgsh_ext/Vext+APAPGSH_Import_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPMERIM",
             equation="apapmer_ext <-> apapmer",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPMER_Import_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPMER_Import_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPMER_Import_Vmax* (apapmer_ext/Vext)/(apapmer_ext/Vext+APAPMER_Import_Km) ", UNIT_mmole_per_min)),

    # biochemical reactions

    Reaction("APAPGLU",
             equation="apap <-> apapglu",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPGLU_Vmax", 1e-7, unit=UNIT_mmole_per_min),
                 Parameter("APAPGLU_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPGLU_Vmax * (apap/Vki)/(apap/Vki+APAPGLU_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPSUL",
             equation="apap -> apapsul",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPSUL_Vmax", 1e-7, unit=UNIT_mmole_per_min),
                 Parameter("APAPSUL_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPSUL_Vmax * (apap/Vki)/(apap/Vki+APAPSUL_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPCYS",
             equation="apap -> apapcys",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPCYS_Vmax", 1e-7, unit=UNIT_mmole_per_min),
                 Parameter("APAPCYS_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPCYS_Vmax * (apap/Vki)/(apap/Vki+APAPCYS_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGSH",
             equation="apap -> apapgsh",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPGSH_Vmax", 1e-7, unit=UNIT_mmole_per_min),
                 Parameter("APAPGSH_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPGSH_Vmax * (apap/Vki)/(apap/Vki+APAPGSH_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPMER",
             equation="apap -> apapmer",
             sboTerm=SBO_BIOCHEMICAL_REACTION,
             pars=[
                 Parameter("APAPMER_Vmax", 1e-7, unit=UNIT_mmole_per_min),
                 Parameter("APAPMER_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPMER_Vmax * (apap/Vki)/(apap/Vki+APAPMER_Km) ", UNIT_mmole_per_min)),

    # export reactions

     Reaction("APAPEXP",
             equation="apap <-> apap_urine",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAP_Export_Vmax", 0.0005, unit=UNIT_mmole_per_min),
                 Parameter("APAP_Export_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAP_Export_Vmax* (apap/Vki)/(apap/Vki+APAP_Export_Km) ", UNIT_mmole_per_min)),

    Reaction("APAPGLUEXP",
             equation="apapglu <-> apapglu_urine",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGLU_Export_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPGLU_Export_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPGLU_Export_Vmax* (apapglu/Vki)/(apapglu/Vki+APAPGLU_Export_Km) ", UNIT_mmole_per_min)),

    Reaction("APAPSULEXP",
             equation="apapsul <-> apapsul_urine",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPSUL_Export_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPSUL_Export_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPSUL_Export_Vmax* (apapsul/Vki)/(apapsul/Vki+APAPSUL_Export_Km) ", UNIT_mmole_per_min)),

    Reaction("APAPCYSEXP",
             equation="apapcys <-> apapcys_urine",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPCYS_Export_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPCYS_Export_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPCYS_Export_Vmax* (apapcys/Vki)/(apapcys/Vki+APAPCYS_Export_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPGSHEXP",
             equation="apapgsh <-> apapgsh_urine",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPGSH_Export_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPGSH_Export_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPGSH_Export_Vmax* (apapgsh/Vki)/(apapgsh/Vki+APAPGSH_Export_Km) ", UNIT_mmole_per_min)),
    Reaction("APAPMEREXP",
             equation="apapmer <-> apapmer_urine",
             sboTerm=SBO_TRANSPORT_REACTION,
             pars=[
                 Parameter("APAPMER_Export_Vmax", 0.05, unit=UNIT_mmole_per_min),
                 Parameter("APAPMER_Export_Km", 0.05, unit=UNIT_mM),
             ],
             formula=("APAPMER_Export_Vmax* (apapmer/Vki)/(apapmer/Vki+APAPMER_Export_Km) ", UNIT_mmole_per_min)),
]


def create_model(target_dir):
    return creator.create_model(
        modules=['model_kidney'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    create_model(target_dir="./models")
