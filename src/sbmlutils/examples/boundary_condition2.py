"""Simple assignment test case."""
from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.units import *


mid = "boundary_condition_example2"
creators = templates.creators
notes = Notes(
    [
        """<p>Example model for testing boundary_condition</p>""",
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
        boundaryCondition=False,
    ),
    Species(
        "A2",
        initialAmount=1.0,
        constant=False,
        substanceUnit=UNIT_mmole,
        compartment="c",
        hasOnlySubstanceUnits=True,
        boundaryCondition=True,
    ),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.boundary_condition2"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
