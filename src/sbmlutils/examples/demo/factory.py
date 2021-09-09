"""Create demo model."""
from pathlib import Path

from sbmlutils.examples.demo.model import demo_model
from sbmlutils.factory import create_model


def create(tmp: bool = False) -> None:
    """Create model."""
    output_dir = Path(__file__).parent
    create_model(
        models=demo_model,
        output_dir=output_dir / "results",
        annotations=output_dir / "demo_annotations.xlsx",
        tmp=tmp,
    )

    # without annotations
    create_model(
        models=demo_model,
        output_dir=output_dir / "results",
        mid=f"{demo_model.sid}_no_annotations",
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
