"""
Create simple reaction.
"""
from pathlib import Path

import numpy as np

from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator.creator import create_model
from sbmlutils.units import *


# ---------------------------------------------------------------------------------------------------------------------
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


def create(tmp=False):
    create_model(
        modules=["sbmlutils.examples.models.core.reaction_example"],
        output_dir=Path(__file__).parent / "results",
        tmp=tmp,
        units_consistency=False,
    )


if __name__ == "__main__":
    create()
