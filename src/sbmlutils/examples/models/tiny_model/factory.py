"""
Script to create the tiny model SBML.
The memote report can be created via

    memote report snapshot --filename "report.html" path/to/model.xml
"""

from pathlib import Path

from sbmlutils.modelcreator.creator import Factory


def create(tmp=False):
    """Create demo model.

    :return:
    """
    models_dir = Path(__file__).parent
    factory = Factory(
        modules=["sbmlutils.examples.models.tiny_model.model"],
        output_dir=models_dir / "results",
        annotations=models_dir / "annotations.xlsx",
    )
    factory.create(tmp)


if __name__ == "__main__":
    create()
