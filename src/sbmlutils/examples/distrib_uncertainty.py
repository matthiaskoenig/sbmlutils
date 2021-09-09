"""Distrib uncertainty example."""
import libsbml

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.units import *


_m = Model("uncertainty_example")
_m.packages = ["distrib"]
_m.creators = templates.creators
_m.notes = Notes(
    [
        """
    <h1>sbmlutils {}</h1>
    <h2>Description</h2>
    <p>Example creating distrib model with uncertainty elements.</p>
    """,
        templates.terms_of_use,
    ]
)

_m.model_units = ModelUnits(
    time=UNIT_hr,
    extent=UNIT_KIND_MOLE,
    substance=UNIT_KIND_MOLE,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
_m.units = [
    UNIT_hr,
    UNIT_m,
    UNIT_m2,
]

_m.parameters = [
    Parameter(
        sid="p1",
        value=1.0,
        unit=UNIT_KIND_MOLE,
        constant=True,
        uncertainties=[
            Uncertainty(
                formula="normal(2.0, 2.0)",
                uncertParameters=[
                    UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=2.0),
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
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
