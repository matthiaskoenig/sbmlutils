from pathlib import Path

from sbmlutils.creator import create_model


def create(tmp=False):
    create_model(
        modules=["sbmlutils.examples.dallaman.model"],
        output_dir=Path(__file__).parent / "results",
        tmp=tmp,
        units_consistency=False,
    )


if __name__ == "__main__":
    create()
