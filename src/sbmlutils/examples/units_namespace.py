"""Example creating model with id clash between units and other objects.

Model used for testing units namespacing.
"""
from pathlib import Path
from typing import List

from sbmlutils.creator import FactoryResult, create_model
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


# -------------------------------------------------------------------------------------
mid = "units_namespace"
model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_m3,
)
units = [
    UNIT_m,
    UNIT_m2,
    UNIT_m3,
    UNIT_min,
    UNIT_mmole,
]
compartments: List[Compartment] = [
    Compartment(
        sid="m3", value=1.0, unit=UNIT_m3, sboTerm=SBO.PHYSICAL_COMPARTMENT, port=True
    ),
]
# ------------------------------------------------------------------------------


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        modules=["sbmlutils.examples.units_namespace"],
        output_dir=Path(__file__).parent / "_results",
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path, delete_session=True)
