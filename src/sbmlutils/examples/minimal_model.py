"""Example creating minimal model.

This demonstrates just the very core SBML functionality.
"""
from pathlib import Path

from sbmlutils import EXAMPLES_DIR
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *


model_minimal = Model(
    sid="minimal_model",
    packages=["fbc"],
    compartments=[
        Compartment(sid="cell", value=1.0, port=True),
    ],
    species=[
        Species(sid="S1", initialConcentration=10.0, compartment="cell", port=True),
        Species(sid="S2", initialConcentration=0.0, compartment="cell"),
    ],
    parameters=[
        Parameter(sid="k1", value=0.1),
    ],
    reactions=[
        Reaction(sid="J0", equation="S1 -> S2", formula="k1 * S2"),
    ],
)


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=model_minimal,
        output_dir=EXAMPLES_DIR,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path, delete_session=True)
