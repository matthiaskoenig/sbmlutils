"""Example creating minimal model.

This demonstrates just the very core SBML functionality.
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
# packages: List[str] = ['fbc']
mid: str = "minimal_model"
compartments: List[Compartment] = [
    Compartment(sid="cell", value=1.0, port=True),
]
species: List[Species] = [
    Species(sid="S1", initialConcentration=10.0, compartment="cell", port=True),
    Species(sid="S2", initialConcentration=0.0, compartment="cell"),
]
parameters: List[Parameter] = [
    Parameter(sid="k1", value=0.1),
]
reactions: List[Reaction] = [
    Reaction(sid="J0", equation="S1 -> S2", formula="k1 * S2"),
]
# -------------------------------------------------------------------------------------


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        modules=["sbmlutils.examples.minimal_example.minimal_model"],
        # annotations=Path(__file__).parent / "minimal_model_annotations.xlsx",
        output_dir=Path(__file__).parent,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path, delete_session=True)
