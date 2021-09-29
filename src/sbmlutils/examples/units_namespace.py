"""Example creating model with id clash between units and other objects.

Model used for testing units namespacing.
"""
from pathlib import Path

from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitDefinitions."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    m = UnitDefinition("m", "meter")
    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")


_m = Model(
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


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
