"""Create reaction example."""
import numpy as np

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


_m = Model(
    "reaction_example",
    notes="""
    # Example `core_example2`
    ## Description
    This example demonstrates the creation of a reaction.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    compartments=[
        Compartment(sid="c", name="cytosol", value=np.NaN),
    ],
    species=[
        Species(
            sid="x",
            compartment="c",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            initialConcentration=np.NaN,
        ),
        Species(
            sid="y",
            compartment="c",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            initialConcentration=np.NaN,
        ),
    ],
    reactions=[
        Reaction(
            sid="v1",
            equation="x -> y",
            compartment="c",
        )
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
        units_consistency=False,
    )


if __name__ == "__main__":
    create()
