"""Example model with notes."""

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.miriam import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


_m = Model(
    sid="notes_example",
    notes="""
    # Model with notes
    ## Description
    """
    + templates.terms_of_use
    # notes=templates.terms_of_use
)


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
