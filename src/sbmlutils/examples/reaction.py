"""Create reaction example."""
import numpy as np

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


mid = "reaction_example"
notes = Notes(
    [
        """
    <h1>Koenig sbmlutils example</h1>
    <h2>Description</h2>
    <p>Model creating a simple reaction.
    </p>
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators

compartments = [
    Compartment(sid="c", name="cytosol", value=np.NaN),
]

species = [
    Species(
        sid="x",
        compartment="c",
        sboTerm=SBO_SIMPLE_CHEMICAL,
        initialConcentration=np.NaN,
    ),
    Species(
        sid="y",
        compartment="c",
        sboTerm=SBO_SIMPLE_CHEMICAL,
        initialConcentration=np.NaN,
    ),
]

reactions = [
    Reaction(
        sid="v1",
        equation="x -> y",
        compartment="c",
    )
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.reaction"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
        units_consistency=False,
    )


if __name__ == "__main__":
    create()
