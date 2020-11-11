"""
Simple assignment test case.
"""
from pathlib import Path

from sbmlutils.factory import *
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator.creator import Factory
from sbmlutils.units import *


# ---------------------------------------------------------------------------------------------------------------------
mid = "boundary_condition"
creators = templates.creators
notes = Notes(
    [
        """<p>Example model for testing boundary_condition in roadrunner.</p>""",
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
    factory = Factory(
        modules=["sbmlutils.examples.models.boundary_condition_2.model"],
        output_dir=Path(__file__).parent / "results",
    )
    factory.create(tmp)


if __name__ == "__main__":
    create()
