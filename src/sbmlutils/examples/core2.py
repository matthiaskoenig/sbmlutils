"""Example model for creating an SBML ODE model."""
from typing import List

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


mid = "core_example2"
notes = Notes(
    [
        """
    <h1>sbmlutils {}</h1>
    <h2>Description</h2>
    <p>Example model showing how to create compartments, species and reactions.</p>
    """,
        templates.terms_of_use,
    ]
)
creators = [
    Creator(
        familyName="Koenig",
        givenName="Matthias",
        email="koenigmx@hu-berlin.de",
        organization="Humboldt-University Berlin, Institute for Theoretical Biology",
        site="https://livermetabolism.com",
    )
]

model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
units = [
    UNIT_m,
    UNIT_m2,
    UNIT_min,
    UNIT_mmole,
    UNIT_mM,
    UNIT_mmole_per_min,
]

functions: List[Function] = []

compartments = [Compartment("c", 1.0, unit=UNIT_KIND_LITRE)]

species = [
    Species(
        "S1",
        initialConcentration=5.0,
        compartment="c",
        substanceUnit=UNIT_mmole,
        name="S1",
        hasOnlySubstanceUnits=False,
        sboTerm=SBO_SIMPLE_CHEMICAL,
    )
]

parameters = [
    Parameter(
        "R1_Km", name="Km R1", value=0.1, unit=UNIT_mM, sboTerm=SBO_MICHAELIS_CONSTANT
    ),
    Parameter(
        "R1_Vmax",
        name="Vmax R1",
        value=10.0,
        unit=UNIT_mmole_per_min,
        sboTerm=SBO_MAXIMAL_VELOCITY,
    ),
]
assignments = [
    InitialAssignment("S1", "10.0 mM", UNIT_mM),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.core2"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
