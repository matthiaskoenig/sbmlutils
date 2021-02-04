"""
Simple assignment test case.
"""
from pathlib import Path

from sbmlutils.factory import *
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator.creator import create_model
from sbmlutils.units import *


# ---------------------------------------------------------------------------------------------------------------------
mid = "boundary_condition_example"
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
    create_model(
        modules=["sbmlutils.examples.models.core.boundary_condition_example"],
        output_dir=Path(__file__).parent / "results",
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
