"""Example for substance units."""
from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *


class U(Units):
    """UnitsDefinitions."""

    kg = UnitDefinition("kg", "kg")
    min = UnitDefinition("min", "min")
    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole = UnitDefinition("mmole", "mmole")
    per_mmole = UnitDefinition("per_mmole", "1/mmole")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")
    per_min = UnitDefinition("per_min", "1/min")


_m = Model(
    "multiple_substance_units",
    name="model with multiple substance units",
    notes="""
    # Example model for multiple substance units
    The substance units for species are restricted to a single substance unit so that
    reaction rates are in [substance_units/time_units] in an SBML model.

    Applying species conversion factors allows to have distinct subsets of species with
    different units in a single model.

    A typical example is the combination of metabolic compounds (simple chemicals) often
    in mmole with proteins in a single model.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    units=U,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.meter,
        area=U.m2,
        volume=U.liter,
    ),
    compartments=[
        Compartment(
            sid="cyto",
            value=1.0,
            unit=U.liter,
            name="cytosol",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
        ),
    ],
    parameters=[
        Parameter(
            sid="cf_units_per_mmole",
            value=1.0,
            unit=U.per_mmole,
            name="dimensionless species conversion",
            sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        )
    ],
    species=[
        Species(
            sid="glc",
            compartment="cyto",
            initialConcentration=3.0,
            substanceUnit=U.mmole,
            name="D-glucose",
            sboTerm=SBO.SIMPLE_CHEMICAL,
        ),
        Species(
            sid="glc6p",
            compartment="cyto",
            initialConcentration=0.5,
            substanceUnit=U.mmole,
            name="D-glucose 6-phosphate",
            sboTerm=SBO.SIMPLE_CHEMICAL,
        ),
        Species(
            sid="hex1",
            compartment="cyto",
            initialConcentration=1.0,
            substanceUnit=U.dimensionless,
            name="hexokinase protein",
            sboTerm=SBO.MACROMOLECULE,
            conversionFactor="cf_units_per_mmole",
            hasOnlySubstanceUnits=True,
            notes="""
            extent * conversionfactor = substanceUnit

            mmole * 1/mmole = dimensionless
            """,
        ),
    ],
)

_m.reactions = [
    Reaction(
        sid="HEX1SYNTHESIS",
        name="hexokinase synthesis",
        equation="-> hex1",
        compartment="cyto",
        sboTerm=SBO.BIOCHEMICAL_REACTION,
        pars=[
            Parameter(
                sid="HEX1SYNTHESIS_k",
                value=1.0,
                unit=U.mmole_per_min,
                sboTerm=SBO.MAXIMAL_VELOCITY,
            ),
        ],
        formula=(
            "HEX1SYNTHESIS_k",
            U.mmole_per_min,
        ),
    ),
    Reaction(
        sid="HEX1",
        name="hexokinase",
        equation="glc -> glc6p [hex1]",
        compartment="cyto",
        sboTerm=SBO.BIOCHEMICAL_REACTION,
        pars=[
            Parameter(
                sid="HEX1_Vmax",
                value=1.0,
                unit=U.mmole_per_min,
                sboTerm=SBO.MAXIMAL_VELOCITY,
            ),
            Parameter(
                sid="HEX1_Km_glc",
                value=0.1,
                unit=U.mM,
                sboTerm=SBO.MICHAELIS_CONSTANT,
            ),
        ],
        formula=(
            "HEX1_Vmax * hex1 * glc/(HEX1_Km_glc + glc)",
            U.mmole_per_min,
        ),
    ),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
