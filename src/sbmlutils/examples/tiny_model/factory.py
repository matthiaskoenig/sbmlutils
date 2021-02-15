"""Create the tiny model SBML.

The memote report can be created via

    memote report snapshot --filename "report.html" path/to/model.xml
"""

from pathlib import Path

from sbmlutils.creator import create_model


def create(tmp: bool = False) -> None:
    """Create model."""
    models_dir = Path(__file__).parent
    create_model(
        modules=["sbmlutils.examples.tiny_model.model"],
        output_dir=models_dir / "results",
        annotations=models_dir / "annotations.xlsx",
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
