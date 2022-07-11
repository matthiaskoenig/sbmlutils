"""Test parsing of SBML."""
from pathlib import Path

import pytest
from pymetadata.omex import ManifestEntry, Omex

from sbmlutils.factory import Model, create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import BIOMODELS_CURATED_PATH, sbml_paths_idfn
from sbmlutils.validation import ValidationOptions

sbml_paths = []
for k in range(100):
    path = BIOMODELS_CURATED_PATH / f"BIOMD0000000{k:0>3}.omex"
    if path.exists():
        sbml_paths.append(path)


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_model_from_biomodels_omex(sbml_path: Path, tmp_path: Path) -> None:
    """Test creation of json for paths."""
    assert sbml_path.exists()

    omex = Omex().from_omex(sbml_path)
    entry: ManifestEntry
    for entry in omex.manifest.entries:
        if entry.is_sbml():
            sbml_path: Path = omex.get_path(entry.location)

            print(str(sbml_path))
            m: Model = sbml_to_model(sbml_path)
            print(m)
            create_model(
                model=m,
                filepath=tmp_path / "models.xml",
                sbml_level=3,
                sbml_version=2,
                validation_options=ValidationOptions(units_consistency=False)
            )
