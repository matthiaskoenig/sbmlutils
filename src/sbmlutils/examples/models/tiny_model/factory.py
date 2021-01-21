"""
Script to create the tiny model SBML.
The memote report can be created via

    memote report snapshot --filename "report.html" path/to/model.xml
"""

from pathlib import Path

from sbmlutils.modelcreator.creator import create_model


def create(tmp=False):
    models_dir = Path(__file__).parent
    create_model(
        modules=["sbmlutils.examples.models.tiny_model.model"],
        output_dir=models_dir / "results",
        annotations=models_dir / "annotations.xlsx",
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
