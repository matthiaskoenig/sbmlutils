"""Example creating model with id clash between units and other objects.

Model used for testing units namespacing.
"""
from pathlib import Path

from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.resources import EXAMPLES_DIR


class U(Units):
    """UnitDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m = UnitDefinition("m", "meter")
    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")


model = Model(
    "units_namespace",
    name="model with unit and sid namespace clash",
    notes="""
    # Model testing units and sid namespace

    The UnitDefinitions and other Objects in an SBMLDocument have different SId
    namespaces. This examples tests clashes of this namespace by creating a unit
    with `sid=m3` and a compartment `sid=m3`.

    """
    + templates.terms_of_use,
    creators=templates.creators,
    packages=[Package.COMP_V1],
    units=U,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.m,
        area=U.m2,
        volume=U.m3,
    ),
    compartments=[
        Compartment(
            sid="m3",
            value=1.0,
            unit=U.m3,
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            port=True,
        ),
    ],
)


if __name__ == "__main__":
    create_model(model=model, filepath=EXAMPLES_DIR / f"{model.sid}.xml")
