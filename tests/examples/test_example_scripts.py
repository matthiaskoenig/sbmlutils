"""Run the examples which are scripts.

The model definitions are checked by `test_examples.py`, this runs the examples
which do something with a model: interpolate data, convert a model, merge
models or simulate one. Every example is run as a module in a temporary working
directory, so the files it writes do not end up in the repository.

The examples which need Cytoscape (`visualize_sbml`) or network access are not
run here.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest


#: the root of the repository, `python -m examples.<module>` is run from here
REPO_DIR = Path(__file__).parent.parent.parent

#: examples which run without Cytoscape and without network access
SCRIPTS = [
    "examples.converters.odefac",
    "examples.converters.xpp",
    "examples.distrib.distrib_packages_examples",
    "examples.distrib.distrib_uncertainty",
    "examples.interpolation.interpolation",
    "examples.interpolation.pancreas",
    "examples.merge_models.merge_models",
    "examples.tiny.simulation",
]


@pytest.mark.parametrize("module", SCRIPTS)
def test_example_script(module: str, tmp_path: Path) -> None:
    """Every example runs without an error and writes into the working directory."""
    env = dict(os.environ, PYTHONPATH=str(REPO_DIR), MPLBACKEND="Agg")
    result = subprocess.run(
        [sys.executable, "-m", module],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
