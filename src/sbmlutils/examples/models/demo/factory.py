"""
Create model.
"""
from pathlib import Path

from sbmlutils.examples.models.demo import model
from sbmlutils.modelcreator.creator import create_model


def create(tmp=False):
    output_dir = Path(__file__).parent
    create_model(
        modules=["sbmlutils.examples.models.demo.model"],
        output_dir=output_dir / "results",
        annotations=output_dir / "demo_annotations.xlsx",
        tmp=tmp,
    )

    # without annotations
    create_model(
        modules=["sbmlutils.examples.models.demo.model"],
        output_dir=output_dir / "results",
        mid="{}_{}_{}".format(model.mid, model.version, "no_annotations"),
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
