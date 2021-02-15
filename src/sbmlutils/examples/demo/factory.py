"""Create demo model."""
from pathlib import Path

from sbmlutils.creator import create_model
from sbmlutils.examples.demo import model


def create(tmp: bool = False) -> None:
    """Create model."""
    output_dir = Path(__file__).parent
    create_model(
        modules=["sbmlutils.examples.demo.model"],
        output_dir=output_dir / "results",
        annotations=output_dir / "demo_annotations.xlsx",
        tmp=tmp,
    )

    # without annotations
    create_model(
        modules=["sbmlutils.examples.demo.model"],
        output_dir=output_dir / "results",
        mid="{}_{}_{}".format(model.mid, model.version, "no_annotations"),
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
