"""Simple assignment test case."""
from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *


class U(Units):
    """UnitDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m2 = UnitDefinition("m2", "meter^2")


model = Model(
    "boundary_condition",
    name="model with boundary conditions",
    creators=templates.creators,
    notes="""
    Example model for testing boundary_condition.
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
            boundaryCondition=False,
        ),
        Species(
            "A2",
            initialAmount=1.0,
            constant=False,
            substanceUnit=U.mmole,
            compartment="c",
            hasOnlySubstanceUnits=True,
            boundaryCondition=True,
        ),
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=model,
        output_dir=EXAMPLES_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
