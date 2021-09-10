"""Example creating model with id clash between units and other objects.

Model used for testing units namespacing.
"""
from pathlib import Path
from typing import List

from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.units import *


_m = Model(
    "units_namespace",
    model_units=ModelUnits(
        time=UNIT_min,
        extent=UNIT_mmole,
        substance=UNIT_mmole,
        length=UNIT_m,
        area=UNIT_m2,
        volume=UNIT_m3,
    ),
    units=[
        UNIT_m,
        UNIT_m2,
        UNIT_m3,
        UNIT_min,
        UNIT_mmole,
    ],
    compartments=[
        Compartment(
            sid="m3",
            value=1.0,
            unit=UNIT_m3,
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            port=True,
        ),
    ],
)


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=_m,
        output_dir=Path(__file__).parent / "_results",
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
