"""Testing model with NaN values."""

from sbmlutils.examples import EXAMPLE_RESULTS_DIR
from sbmlutils.factory import *
from sbmlutils.metadata import *


_m = Model(
    "nan_test",
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
    create_model(
        models=_m, output_dir=EXAMPLE_RESULTS_DIR, tmp=tmp, units_consistency=False
    )


if __name__ == "__main__":
    create()
