"""Example for model compositon via multiple files."""
from pathlib import Path
from typing import List

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *
from sbmlutils.metadata import *
from minimal_model import model_minimal

model = Model(
    sid="model_composition",
    annotations=[(BQB.IS, "taxonomy/911")],
    parameters=[
        Parameter(sid="k2", value=0.1),
    ],
    reactions=[
        Reaction(sid="J1", equation="-> S1", formula="k2"),
    ]
)


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=[model_minimal, model],
        output_dir=Path(__file__).parent,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
