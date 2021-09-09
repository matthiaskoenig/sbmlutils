"""Create reaction example."""
import numpy as np

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.units import *


_m = Model("reaction_example")
_m.notes = Notes(
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
_m.creators = templates.creators

_m.compartments = [
    Compartment(sid="c", name="cytosol", value=np.NaN),
]

_m.species = [
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
]

_m.reactions = [
    Reaction(
        sid="v1",
        equation="x -> y",
        compartment="c",
    )
]


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
