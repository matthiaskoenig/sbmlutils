"""Distrib uncertainty example."""
import libsbml

from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *


class U(Units):
    """UnitDefinitions."""

    hr = UnitDefinition("hr", "hour")
    m2 = UnitDefinition("m2", "meter^2")


_m = Model(
    "distrib_uncertainties",
    name="""model with distrib uncertainties""",
    packages=["distrib"],
    creators=templates.creators,
    notes="""
    # Uncertainty example
    Example creating distrib model with uncertainty elements.
    """
    + templates.terms_of_use,
    units=U,
    model_units=ModelUnits(
        time=U.hr,
        extent=U.mole,
        substance=U.mole,
        length=U.meter,
        area=U.m2,
        volume=U.liter,
    ),
    parameters=[
        Parameter(
            sid="p1",
            value=1.0,
            unit=U.mole,
            constant=True,
            uncertainties=[
                Uncertainty(
                    formula="normal(2.0, 2.0)",
                    uncertParameters=[
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=2.0
                        ),
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=2.0
                        ),
                    ],
                    uncertSpans=[
                        UncertSpan(
                            type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                            valueLower=1.0,
                            valueUpper=4.0,
                        ),
                    ],
                )
            ],
        )
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
