"""Example creating core model."""
from pathlib import Path

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


mid = "core_example1"
notes = Notes(
    [
        """
    <h1>Koenig Test Model</h1>
    <h2>Description</h2>
    <p>Test model.
    </p>
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

compartments = [
    Compartment(sid="ext", value="Vol_e", unit="m3", constant=True, name="external"),
    Compartment(sid="cyto", value="Vol_c", unit="m3", constant=False, name="cytosol"),
    Compartment(
        sid="pm",
        value="A_m",
        unit="m2",
        constant=True,
        spatialDimensions=2,
        name="membrane",
    ),
]

species = [
    Species(
        sid="e__gal",
        compartment="ext",
        initialConcentration=3.0,
        substanceUnit=UNIT_KIND_MOLE,
        boundaryCondition=True,
        name="D-galactose",
        sboTerm=SBO_SIMPLE_CHEMICAL,
    ),
    Species(
        sid="c__gal",
        compartment="cyto",
        initialConcentration=0.00012,
        substanceUnit=UNIT_KIND_MOLE,
        boundaryCondition=False,
        name="D-galactose",
        sboTerm=SBO_SIMPLE_CHEMICAL,
    ),
]
parameters = [
    Parameter(sid="x_cell", value=25e-6, unit="m", constant=True, name="cell diameter"),
    Parameter(
        sid="Vol_e", value=100e-14, unit="m3", constant=True, name="external volume"
    ),
    Parameter(sid="A_m", value=1.0, unit="m2", constant=True, name="membrane area"),
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
