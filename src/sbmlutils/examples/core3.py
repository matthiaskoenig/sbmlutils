"""Example for substance units."""
from pathlib import Path
from typing import List

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


mid = "core_example1"
notes = Notes(
    [
        """
    <h1>Example model for substance units</h1>
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators

model_units = ModelUnits(
    time=UNIT_s,
    extent=UNIT_KIND_MOLE,
    substance=UNIT_KIND_MOLE,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_m3,
)
units = [UNIT_kg, UNIT_s, UNIT_m, UNIT_m2, UNIT_m3, UNIT_mM, UNIT_mole_per_s]

compartments: List[Compartment] = [
    Compartment(sid="cyto", value=1.0, unit=UNIT_KIND_LITRE, name="cytosol"),
]

species: List[Specie] = [
    Species(
        sid="glc",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_mmole,
        name="D-glucose",
        sboTerm=SBO_SIMPLE_CHEMICAL,
    ),
    Species(
        sid="glc6p",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_mmole,
        name="D-glucose 6-phosphate",
        sboTerm=SBO_SIMPLE_CHEMICAL,
    ),
]

assignments = [
    InitialAssignment(sid="Vol_c", value="x_cell*x_cell*x_cell", unit="m3"),
]
reactions = [
    Reaction(
        sid="e__GLUT2_GAL",
        name="galactose transport [e__]",
        equation="e__gal <-> c__gal []",
        # C6H1206 (0) <-> C6H1206 (0)
        compartment="pm",
        pars=[
            Parameter(sid="GLUT2_Vmax", value=1e-13, unit="mole_per_s"),
            Parameter("GLUT2_k_gal", 1.0, "mM"),
            Parameter("GLUT2_keq", 1.0, "-"),
        ],
        formula=(
            "GLUT2_Vmax/GLUT2_k_gal * (e__gal - c__gal/GLUT2_keq)/"
            "(1 dimensionless + c__gal/GLUT2_k_gal + e__gal/GLUT2_k_gal)",
            "mole_per_s",
        ),
    )
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.core1"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
