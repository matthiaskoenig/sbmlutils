"""Multiple model definitions."""
from typing import List

from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *


class U(Units):
    """UnitsDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m2 = UnitDefinition("m2", "meter^2")


_m = Model(
    "model_definitions",
    creators=templates.creators,
    notes="""
    # Example model with multiple ModelDefinitions.
    """
    + templates.terms_of_use,
    units=U,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.meter,
        area=U.m2,
        volume=U.liter,
    ),
    compartments=[Compartment("c", value=2.0, unit=U.liter)],
    species=[
        Species(
            "A1",
            initialAmount=1.0,
            constant=False,
            substanceUnit=U.mmole,
            compartment="c",
            hasOnlySubstanceUnits=True,
        )
    ],
)


_m.model_definitions = [
    ModelDefinition(
        sid="m1",
        name="Model Definition 1",
        units=_m.units,
        compartments=[Compartment("d", value=1.0, unit=U.liter)],
        species=[
            Species(
                "A",
                initialAmount=1.0,
                constant=False,
                substanceUnit=U.mmole,
                compartment="d",
                hasOnlySubstanceUnits=True,
            )
        ],
    )
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
