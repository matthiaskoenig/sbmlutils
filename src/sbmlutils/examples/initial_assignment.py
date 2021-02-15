"""Simple assignment test case."""
from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.units import *


mid = "initial_assignment_example"
creators = templates.creators
notes = Notes(
    [
        """<p>Example model for testing InitialAssignments in roadrunner.</p>""",
        templates.terms_of_use,
    ]
)
model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
units = [
    UNIT_min,
    UNIT_mmole,
    UNIT_m,
    UNIT_m2,
]
compartments = [Compartment("c", value=2.0, unit=UNIT_KIND_LITRE)]
species = [
    Species(
        "A1",
        initialAmount=1.0,
        constant=False,
        substanceUnit=UNIT_mmole,
        compartment="c",
        hasOnlySubstanceUnits=True,
    )
]
parameters = [
    Parameter("D", 5.0, UNIT_mmole, constant=True),
]
assignments = [
    InitialAssignment("A1", "D * 2 dimensionless", UNIT_mmole),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.initial_assignment"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
