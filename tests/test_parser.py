"""Test parsing of SBML."""
from pathlib import Path

import pytest

from sbmlutils.factory import Model, create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import BIOMODELS_CURATED_PATH, sbml_paths_idfn

sbml_paths = []
for k in range(100):
    path = BIOMODELS_CURATED_PATH / f"BIOMD0000000{k:0>3}.omex"
    if path.exists():
        sbml_paths.append(path)


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_model_from_sbml(sbml_path: Path, tmp_path: Path) -> None:
    """Test creation of json for paths."""
    assert sbml_path.exists()

    print(str(sbml_path))
    model: Model = sbml_to_model(sbml_path)
    create_model(
        models=model,
        output_dir=tmp_path,
        filename="model.xml",
        units_consistency=False,
        sbml_level=3,
        sbml_version=2,
    )
