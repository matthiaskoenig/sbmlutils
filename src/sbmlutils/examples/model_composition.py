"""Example for model composition via multiple models."""
from pathlib import Path

from sbmlutils import EXAMPLES_DIR
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples.minimal_model import model_minimal
from sbmlutils.factory import *
from sbmlutils.metadata import *


model = Model(
    sid="model_composition",
    name="model composition from multiple models",
    annotations=[(BQB.IS, "taxonomy/911")],
    parameters=[
        Parameter(sid="k2", value=0.1),
    ],
    reactions=[
        Reaction(sid="J1", equation="-> S1", formula="k2"),
    ],
)


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=[model_minimal, model],
        output_dir=EXAMPLES_DIR,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
