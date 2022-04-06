"""Examples demonstrating the merging of SBML models."""

from pathlib import Path
from pprint import pprint

from sbmlutils.manipulation import merge_models
from sbmlutils.test import TESTDATA_DIR


def merge_models_example() -> None:
    """Demonstrate merging of models."""

    input_dir = TESTDATA_DIR / "manipulation" / "merge"

    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = [f"BIOMD000000000{k}" for k in range(1, 5)]
    model_paths = dict(zip(model_ids, [input_dir / f"{mid}.xml" for mid in model_ids]))

    pprint(model_paths)
    output_dir = Path(__file__).parent / "_results"
    merge_models(model_paths, output_dir=output_dir)


if __name__ == "__main__":
    merge_models_example()
