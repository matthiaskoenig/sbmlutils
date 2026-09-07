"""Test parsing of SBML."""

from pathlib import Path

import pytest
from pymetadata.omex import ManifestEntry, Omex

from sbmlutils.factory import Model, create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import sbml_paths_idfn
from sbmlutils.validation import ValidationOptions

#: the biomodels archives are test data of the repository, they are not part of
#: the distribution, see `[tool.hatch.build]` in `pyproject.toml`
BIOMODELS_DIR = (
    Path(__file__).parent.parent
    / "src"
    / "sbmlutils"
    / "resources"
    / "models"
    / "biomodels"
)

omex_paths: list[Path] = []
for k in range(100):
    path: Path = BIOMODELS_DIR / f"BIOMD0000000{k:0>3}.omex"
    if path.exists():
        omex_paths.append(path)


@pytest.mark.parametrize("omex_path", omex_paths, ids=sbml_paths_idfn)
def test_model_from_biomodels_omex(omex_path: Path, tmp_path: Path) -> None:
    """Test creation of json for paths."""
    assert omex_path.exists()

    omex = Omex().from_omex(omex_path)
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
                validation_options=ValidationOptions(units_consistency=False),
            )
