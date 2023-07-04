"""Multiple model definitions."""
from sbmlutils.examples import templates
from sbmlutils.factory import *


class U(Units):
    """UnitsDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m2 = UnitDefinition("m2", "meter^2")


model = Model(
    "model_definitions",
    creators=templates.creators,
    notes="""
    # Example model with multiple ModelDefinitions.
    """
    + templates.terms_of_use,
    packages=[Package.COMP_V1],
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


model.model_definitions = [
    ModelDefinition(
        sid="m1",
        name="Model Definition 1",
        # units=model.units,
        compartments=[Compartment("d", value=1.0, unit=U.liter)],
        species=[
            Species(
                "A",
                initialAmount=1.0,
                constant=False,
                # substanceUnit=U.mmole,
                compartment="d",
                hasOnlySubstanceUnits=True,
            )
        ],
    )
]

if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )
