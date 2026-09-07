"""Merging SBML models into one comp model.

`sbmlutils.manipulation.merge_models` combines several models into a single
model of the comp package, in which every input model is a submodel.

Run it from the root of the repository:

```bash
python -m examples.merge_models.merge_models
```

The merged models are written into the current working directory.
"""

from pathlib import Path

from sbmlutils.console import console
from sbmlutils.manipulation import merge_models
from sbmlutils.resources import TESTDATA_DIR


def merge_models_example(output_dir: Path) -> None:
    """Merge the first four biomodels into one comp model.

    Args:
        output_dir: directory the merged models are written to
    """
    input_dir = TESTDATA_DIR / "manipulation" / "merge"

    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = [f"BIOMD000000000{k}" for k in range(1, 5)]
    model_paths = dict(
        zip(model_ids, [input_dir / f"{mid}.xml" for mid in model_ids], strict=True)
    )

    console.print(model_paths)
    output_dir.mkdir(parents=True, exist_ok=True)
    merge_models(model_paths, output_dir=output_dir)


if __name__ == "__main__":
    merge_models_example(output_dir=Path.cwd())
