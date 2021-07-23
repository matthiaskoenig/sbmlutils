"""Example for model compositon via multiple files."""
from pathlib import Path
from typing import List

from sbmlutils.creator import FactoryResult, create_model
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *


# -------------------------------------------------------------------------------------
mid: str = "model_composition"
parameters: List[Parameter] = [
    Parameter(sid="k2", value=0.1),
]
reactions: List[Reaction] = [
    Reaction(sid="J1", equation="-> S1", formula="k2"),
]
# -------------------------------------------------------------------------------------


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        modules=[
            "sbmlutils.examples.minimal_example.minimal_model",
            "sbmlutils.examples.minimal_example.model_composition",
        ],
        output_dir=Path(__file__).parent,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
