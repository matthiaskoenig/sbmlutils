"""Test SBML report."""
from pathlib import Path

import pytest
from rich import print

from sbmlutils import RESOURCES_DIR
from sbmlutils.report import api
from sbmlutils.test import BIOMODELS_CURATED_PATH, sbml_paths_idfn


sbml_paths = []
for k in range(100):
    path = BIOMODELS_CURATED_PATH / f"BIOMD0000000{k:0>3}.omex"
    if path.exists():
        sbml_paths.append(path)


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_json_for_omex(sbml_path: Path, tmp_path: Path) -> None:
    """Test creation of json for paths."""
    print(str(sbml_path))
    assert sbml_path.is_file()
    assert sbml_path.exists()

    json = api.json_for_omex(omex_path=sbml_path)
    assert json
    assert json["manifest"]
    assert json["reports"]
