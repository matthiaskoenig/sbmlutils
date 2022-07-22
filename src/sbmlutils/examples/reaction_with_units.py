"""Reaction example."""

from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitDefinitions."""

    s = UnitDefinition("s", "second")
    m = UnitDefinition("m", "meter")
    m2 = UnitDefinition("m2", "meter^2")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole = UnitDefinition("mmole", "mmole")
    mmole_per_s = UnitDefinition("mmole_per_s", "mmole/s")
    liter = UnitDefinition("liter", "liter")


model = Model(
    "reaction_with_units",
    name="model reaction with units",
    notes="""
    # Model reaction with units

    This example demonstrates how to create a compartment, species and reaction.
    The model uses units.
    Model with single irreversible reaction v1: A -> B.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    units=U,
    model_units=ModelUnits(
        time=U.s,
        extent=U.mmole,
        substance=U.mmole,
        length=U.m,
        area=U.m2,
        volume=U.liter,
    ),
    objects=[
        Compartment(
            sid="cell",
            value=1.0,
            unit=U.liter,
            constant=True,
            name="cell",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
        ),
        Species(
            sid="A",
            compartment="cell",
            initialConcentration=10.0,  # [mM]
            substanceUnit=U.mmole,
            boundaryCondition=False,
            name="A",
            sboTerm=SBO.SIMPLE_CHEMICAL,
        ),
        Species(
            sid="B",
            compartment="cell",
            initialConcentration=10.0,  # [mM]
            substanceUnit=U.mmole,
            boundaryCondition=False,
            name="B",
            sboTerm=SBO.SIMPLE_CHEMICAL,
        ),
        Reaction(
            sid="v1",
            name="v1: A -> B",
            equation="A -> B []",
            compartment="cell",
            pars=[
                Parameter(sid="v1_Vmax", value=1.0, unit=U.mmole_per_s),
                Parameter("v1_Km_A", 0.1, unit=U.mM),
            ],
            formula=(
                "v1_Vmax * v1_Km_A/(v1_Km_A + A)",
                U.mmole_per_s,
            ),
            sboTerm=SBO.BIOCHEMICAL_REACTION,
        ),
    ],
)


if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    create_model(model=model, filepath=EXAMPLES_DIR / f"{model.sid}.xml")
