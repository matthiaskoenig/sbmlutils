"""Model example setting the boundaryCondition attribute on a specie.

The boundaryCondition defines if a species is a constant boundary species.
"""
from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR
from sbmlutils.factory import *


def create(tmp: bool = False) -> None:
    """Create example setting boundaryCondition."""

    m1 = {
        "mid": "m1_boundary_condition",
        "compartments": [Compartment(sid="C", value=1.0)],
        "species": [
            Species(
                sid="S1",
                initialConcentration=10.0,
                compartment="C",
                hasOnlySubstanceUnits=False,
                boundaryCondition=True,
            )
        ],
        "parameters": [Parameter(sid="k1", value=1.0)],
        "reactions": [
            Reaction(sid="R1", equation="S1 ->", formula=("k1 * S1 * sin(time)", None))
        ],
        "assignments": [],
    }

    m2 = m1.copy()
    m2["mid"] = "m2_boundary_condition"
    m2["assignments"] = [AssignmentRule("S1", 20.0)]

    for d in [m1, m2]:
        create_model(
            modules=d,
            output_dir=EXAMPLE_RESULTS_DIR,
            tmp=tmp,
            units_consistency=False,
        )


if __name__ == "__main__":
    create()
