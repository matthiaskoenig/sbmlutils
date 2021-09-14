"""Dextormethorphan kidney model. """

from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.units import *


annotations_species = {
    "dex": [
        (BQB.IS, "chebi/CHEBI:4470"),
        (BQB.IS, "ncit/C62022"),
        (BQB.IS, "inchikey/MKXZASYAUGDDCJ-NJAFHUGGSA-N"),
    ],
    "dor": [
        (BQB.IS, "chebi/CHEBI:29133"),
        (BQB.IS, "ncit/C171857"),
        (BQB.IS, "inchikey/JAQUASYNZVUNQP-PVAVHDDUSA-N"),
    ],
    "qui": [
        (BQB.IS, "chebi/CHEBI:28593"),
        (BQB.IS, "ncit/C793"),
        (BQB.IS, "inchikey/LOUPRKONTZGTKE-LHHVKLHASA-N"),
    ],
}
annotations_compartments = {}


class U(Units):
    min = "min"
    liter = UnitDefinition("liter", "liter", port=True)
    m = UnitDefinition("m", "meter")
    m2 = UnitDefinition("m2", "meter^2")
    mmole = UnitDefinition("mmole", "mmole")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")
    per_min = "1/min"
    mg = "mg"
    g_per_mole = "g/mole"


class MyModel(Model):
    pass


_m = MyModel(
    "dex_kidney",
    notes="""
    # dex_kidney
    ## Description
    Dextormethorphan (DEX) kidney model.

    DEX and DOR can be excreted in the urine via the kidneys. The renal filtration
    and excretion processes are not modeled in detail, but first order irreversible
    mass-action kinetics are used.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.m,
        area=U.m2,
        volume=U.liter,
    ),
    objects=[
        Compartment(
            "Vext",
            4,
            name="plasma",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            unit=U.liter,
            annotations=annotations_compartments["plasma"],
            port=True,
        ),
        Compartment(
            "Vki",
            1.5,
            name="kidney",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            unit=U.liter,
            annotations=annotations_compartments["ki"],
            port=True,
        ),
        Compartment(
            "Vurine",
            1.0,
            name="urine",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            unit=u.liter,
            annotations=annotations_compartments["urine"],
            port=True,
        ),
        Species(
            "dex_ext",
            initialConcentration=0.0,
            name="dextormethorphan (plasma)",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            compartment="Vext",
            substanceUnit=U.mmole,
            hasOnlySubstanceUnits=False,
            annotations=annotations_species["dex"],
            port=True,
        ),
        Species(
            "dor_ext",
            initialConcentration=0.0,
            name="dextrorphan (plasma)",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            compartment="Vext",
            substanceUnit=U.mmole,
            hasOnlySubstanceUnits=False,
            annotations=annotations_species["dor"],
            port=True,
        ),
        Species(
            "dex_urine",
            initialConcentration=0.0,
            name="dextormethorphan (urine)",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            compartment="Vurine",
            substanceUnit=U.mmole,
            hasOnlySubstanceUnits=True,
            annotations=annotations_species["dex"],
            port=True,
            notes="""
            Urinary species are in amounts (mmole)!
            """,
        ),
        Species(
            "dor_urine",
            initialConcentration=0.0,
            name="dextrorphan (urine)",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            compartment="Vurine",
            substanceUnit=U.mmole,
            hasOnlySubstanceUnits=True,
            annotations=annotations_species["dor"],
            port=True,
            notes="""
            Urinary species are in amounts (mmole)!
            """,
        ),
        # reactions
        Reaction(
            "DEXEX",
            name="DEX urinary excretion",
            equation="dex_ext -> dex_urine",
            sboTerm=SBO.TRANSPORT_REACTION,
            compartment="Vki",
            pars=[
                Parameter(
                    "DEXEX_k",
                    0.017,
                    unit=U.per_min,  # [0.0001 - 1000.0]
                    name="DEX urinary excretion rate",
                    sboTerm=SBO.KINETIC_CONSTANT,
                ),
            ],
            formula=("DEXEX_k * Vki * dex_ext", U.mmole_per_min),
        ),
        Reaction(
            "DOREX",
            name="DOR excretion",
            equation="dor_ext -> dor_urine",
            sboTerm=SBO.TRANSPORT_REACTION,
            compartment="Vki",
            pars=[
                Parameter(
                    "DOREX_k",
                    0.14,
                    unit=U.per_min,  # [0.0001 - 1000.0]
                    name="DOR urinary excretion rate",
                    sboTerm=SBO.KINETIC_CONSTANT,
                ),
            ],
            formula=("DOREX_k * Vki * dor_ext", U.mmole_per_min),
        ),
    ],
)


if __name__ == "__main__":
    from pkdb_models.models.dextromethorphan import MODEL_BASE_PATH

    create_model(output_dir=MODEL_BASE_PATH, modules="model_kidney")
