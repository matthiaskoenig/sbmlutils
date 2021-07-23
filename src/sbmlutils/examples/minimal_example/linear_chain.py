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


n_chain = 20
# -------------------------------------------------------------------------------------
mid: str = "linear_chain"
compartments: List[Compartment] = [
    Compartment(sid="cell", value=1.0),
]
species: List[Species] = [
    Species(sid="S1", initialConcentration=10.0, compartment="cell"),
]
parameters: List[Parameter] = []
reactions: List[Reaction] = []
for k in range(n_chain):
    species.append(
        Species(sid=f"S{k + 2}", initialConcentration=0.0, compartment="cell"),
    )
    parameters.append(
        Parameter(sid=f"k{k+1}", value=0.1),
    )
    reactions.append(
        Reaction(
            sid=f"J{k+1}", equation=f"S{k+1} -> S{k+2}", formula=f"k{k+1} * S{k+1}"
        ),
    )
# -------------------------------------------------------------------------------------


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        modules=["sbmlutils.examples.minimal_example.linear_chain"],
        output_dir=Path(__file__).parent,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
