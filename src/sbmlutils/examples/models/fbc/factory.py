from pathlib import Path

from sbmlutils.modelcreator.creator import Factory


def create(tmp=False):
    """Create demo model.

    :return:
    """
    models_dir = Path(__file__).parent
    output_dir = models_dir / "results"

    factory = Factory(
        modules=["sbmlutils.examples.models.fbc.fbc_ex1"], output_dir=output_dir
    )
    factory.create(tmp)

    factory = Factory(
        modules=["sbmlutils.examples.models.fbc.fbc_ex2"], output_dir=output_dir
    )
    factory.create(tmp)


if __name__ == "__main__":
    create()
