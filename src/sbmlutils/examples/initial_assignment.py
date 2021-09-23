"""Simple assignment test case."""
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *


class U(Units):
    """UnitDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m2 = UnitDefinition("m2", "meter^2")


_m = Model(
    "initial_assignment_example",
    creators=templates.creators,
    notes="""
    Example model for testing InitialAssignments in roadrunner.
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
    objects=[
        Compartment("c", value=2.0, unit=U.liter),
        Species(
            "A1",
            initialAmount=1.0,
            constant=False,
            substanceUnit=U.mmole,
            compartment="c",
            hasOnlySubstanceUnits=True,
        ),
        Parameter("D", 5.0, U.mmole, constant=True),
        InitialAssignment("A1", "D * 2 dimensionless", U.mmole),
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
