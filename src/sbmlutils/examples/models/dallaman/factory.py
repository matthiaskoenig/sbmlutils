from pathlib import Path

from sbmlutils.modelcreator import creator


def create(tmp=False):
    creator.create_model(
        modules=["sbmlutils.examples.models.dallaman.model"],
        output_dir=Path(__file__).parent / "results",
        tmp=tmp,
        units_consistency=False,
    )


if __name__ == "__main__":
    create()
