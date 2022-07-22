"""Example creating random network."""
import random

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *
from sbmlutils.resources import EXAMPLES_DIR
from sbmlutils.validation import ValidationOptions


random.seed(1234)
n_species = 100
n_links = 10

# -------------------------------------------------------------------------------------
model = Model(
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

model.reactions = []
for k in range(n_links):
    k_source = random.randint(0, n_species - 1)
    k_target = random.randint(0, n_species - 1)

    model.reactions.append(
        Reaction(
            sid=f"J{k+1}",
            equation=f"S{k_source} -> S{k_target}",
            formula=f"k * S{k_source}",
        ),
    )
# -------------------------------------------------------------------------------------

if __name__ == "__main__":
    fac_result: FactoryResult = create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )
    visualize_sbml(sbml_path=fac_result.sbml_path)
