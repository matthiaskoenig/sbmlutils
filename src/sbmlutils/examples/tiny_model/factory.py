"""Create the tiny model SBML.

The MEMOTE report can be created via

    memote report snapshot --filename "report.html" path/to/model.xml
"""

from pathlib import Path

from sbmlutils.examples.tiny_model.model import _m
from sbmlutils.factory import FactoryResult, create_model


models_dir = Path(__file__).parent


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""

    return create_model(
        models=_m,
        output_dir=models_dir / "results",
        annotations=models_dir / "annotations.xlsx",
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
