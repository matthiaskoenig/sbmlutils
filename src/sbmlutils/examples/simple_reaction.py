"""Example simple_reaction.

Model with single irreversible reaction v1: A -> B.
"""
from pathlib import Path

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


mid = "simple_reaction"
notes = Notes(
    [
        """
    <h1>Koenig example model: simple reaction</h1>
    <h2>Description</h2>
    <p>Test model to show creation of compartment, species and reaction.
    </p>
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators

model_units = ModelUnits(
    time=UNIT_s,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
units = [UNIT_s, UNIT_m, UNIT_m2, UNIT_mM, UNIT_mmole, UNIT_mmole_per_s]

compartments = [
    Compartment(
        sid="cell", value="1.0", unit=UNIT_KIND_LITRE, constant=True, name="cell"
    ),
]

species = [
    Species(
        sid="A",
        compartment="cell",
        initialConcentration=10.0,  # [mM]
        substanceUnit=UNIT_mmole,
        boundaryCondition=False,
        name="A",
        sboTerm=SBO_SIMPLE_CHEMICAL,
    ),
    Species(
        sid="B",
        compartment="cell",
        initialConcentration=10.0,  # [mM]
        substanceUnit=UNIT_mmole,
        boundaryCondition=False,
        name="B",
        sboTerm=SBO_SIMPLE_CHEMICAL,
    ),
]

reactions = [
    Reaction(
        sid="v1",
        name="v1: A -> B",
        equation="A -> B []",
        compartment="cell",
        pars=[
            Parameter(sid="v1_Vmax", value=1.0, unit="mmole_per_s"),
            Parameter("v1_Km_A", 0.1, "mM"),
        ],
        formula=(
            "v1_Vmax * v1_Km_A/(v1_Km_A + A)",
            "mmole_per_s",
        ),
    )
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.simple_reaction"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
