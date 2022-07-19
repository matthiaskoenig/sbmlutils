"""Create demo model."""
from pathlib import Path

from sbmlutils.examples.demo.model import demo_model
from sbmlutils.factory import create_model
import tempfile


def create(tmp: bool = False) -> None:
    """Create model."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        if tmp:
            output_dir = Path(tmp_dir)
        else:
            output_dir = Path(__file__).parent / "results"

    if tmp:
        sbml_path:
    else:
        sbml_path = output_dir / "results" / f"{demo_model.sid}.xml",

    create_model(
        model=demo_model,
        filepath=output_dir / "results" / f"{demo_model.sid}.xml",
        annotations=output_dir / "demo_annotations.xlsx",
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
