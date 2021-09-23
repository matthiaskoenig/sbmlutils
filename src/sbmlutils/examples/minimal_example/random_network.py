"""Example creating random network."""
import random
from pathlib import Path

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *


n_species = 500
n_links = 1000

# -------------------------------------------------------------------------------------
_m = Model(
    "random_network",
    compartments=[
        Compartment(sid="cell", value=1.0),
    ],
    species=[
        Species(sid=f"S{k}", initialConcentration=10.0, compartment="cell")
        for k in range(n_species)
    ],
    parameters=[
        Parameter(sid="k", value=0.1),
    ],
    reactions=[],
)

_m.reactions = []
for k in range(n_links):
    k_source = random.randint(0, n_species - 1)
    k_target = random.randint(0, n_species - 1)

    _m.reactions.append(
        Reaction(
            sid=f"J{k+1}",
            equation=f"S{k_source} -> S{k_target}",
            formula=f"k * S{k_source}",
        ),
    )
# -------------------------------------------------------------------------------------


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=_m,
        output_dir=Path(__file__).parent,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
