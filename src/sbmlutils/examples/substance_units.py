"""Example for substance units."""
from pathlib import Path
from typing import List

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


mid = "substance_units"
notes = Notes(
    [
        """
    <h1>Example model for substance units</h1>
    <p>Applying species conversion factors to have distinct subsets of species in a
    model. A common example are mixing metabolic species and proteins in a single model.
    </p>.
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators

model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
units = [
    UNIT_kg,
    UNIT_min,
    UNIT_m,
    UNIT_m2,
    UNIT_m3,
    UNIT_mM,
    UNIT_mmole,
    UNIT_per_mmole,
    UNIT_mmole_per_min,
    UNIT_per_min,
]

compartments: List[Compartment] = [
    Compartment(sid="cyto", value=1.0, unit=UNIT_KIND_LITRE, name="cytosol"),
]

parameters: List[Parameter] = [
    Parameter(sid="cf_units_per_mmole", value=1.0, unit=UNIT_per_mmole)
]

species: List[Species] = [
    Species(
        sid="glc",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_mmole,
        name="D-glucose",
        sboTerm=SBO.SIMPLE_CHEMICAL,
    ),
    Species(
        sid="glc6p",
        compartment="cyto",
        initialConcentration=0.5,
        substanceUnit=UNIT_mmole,
        name="D-glucose 6-phosphate",
        sboTerm=SBO.SIMPLE_CHEMICAL,
    ),
    # extent * conversionfactor = substanceUnit
    # mmole * 1/mmole = dimenionsless
    Species(
        sid="hex1",
        compartment="cyto",
        initialConcentration=1.0,
        substanceUnit=UNIT_KIND_DIMENSIONLESS,
        name="hexokinase protein",
        sboTerm=SBO.MACROMOLECULE,
        conversionFactor="cf_units_per_mmole",
        hasOnlySubstanceUnits=True,
    ),
]

reactions = [
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
                unit=UNIT_mmole_per_min,
                sboTerm=SBO.MAXIMAL_VELOCITY,
            ),
        ],
        formula=(
            "HEX1SYNTHESIS_k",
            UNIT_mmole_per_min,
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
                unit=UNIT_mmole_per_min,
                sboTerm=SBO.MAXIMAL_VELOCITY,
            ),
            Parameter(
                sid="HEX1_Km_glc",
                value=0.1,
                unit=UNIT_mM,
                sboTerm=SBO.MICHAELIS_CONSTANT,
            ),
        ],
        formula=(
            "HEX1_Vmax * hex1 * glc/(HEX1_Km_glc + glc)",
            UNIT_mmole_per_min,
        ),
    ),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.substance_units"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
