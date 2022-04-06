"""Testing model with NaN values."""
from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


_m = Model(
    "nan",
    name="model with NaN values",
    notes="""
    # Model with NaN values
    Example model with NaN values.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    objects=[
        Compartment(
            "Vmem",
            NaN,
        ),
        Species(
            "S1",
            compartment="Vmem",
            initialConcentration=NaN,
        ),
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(models=_m, output_dir=EXAMPLES_DIR, tmp=tmp, units_consistency=False)


if __name__ == "__main__":
    create()
