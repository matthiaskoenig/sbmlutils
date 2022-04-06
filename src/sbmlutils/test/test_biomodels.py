"""Testing the biomodels module"""
from pathlib import Path

import pytest
from pymetadata.omex import Omex
from requests.exceptions import HTTPError

from sbmlutils.biomodels import download_biomodel_omex, download_biomodel_sbml


def test_download_biomodel_omex_success(tmp_path: Path) -> None:
    """Download OMEX for existing biomodels."""
    biomodel_id = "BIOMD0000000001"
    omex_path = tmp_path / "test.omex"
    download_biomodel_omex(biomodel_id=biomodel_id, omex_path=omex_path)
    assert omex_path.exists()
    assert omex_path.is_file()
    omex = Omex.from_omex(omex_path)
    assert omex


def test_download_biomodel_omex_failure(tmp_path: Path) -> None:
    """Download OMEX for existing biomodels."""
    with pytest.raises(HTTPError):
        omex_path = tmp_path / "test.omex"
        download_biomodel_omex(biomodel_id="BIOMDXYZ", omex_path=omex_path)


def test_download_biomodel_sbml_sbml_success(tmp_path: Path) -> None:
    """Download SBML for existing biomodels."""
    biomodel_id = "BIOMD0000000001"
    locations = download_biomodel_sbml(
        biomodel_id=biomodel_id, output_dir=tmp_path, output_format="sbml"
    )
    assert len(locations) == 2
    assert "./BIOMD0000000001_urn.xml" in locations
    assert "./BIOMD0000000001_url.xml" in locations
    assert (tmp_path / locations[0]).exists()
    assert (tmp_path / locations[1]).exists()


def test_download_biomodel_sbml_omex_success(tmp_path: Path) -> None:
    """Download SBML for existing biomodels."""
    biomodel_id = "BIOMD0000000001"
    locations = download_biomodel_sbml(
        biomodel_id=biomodel_id, output_dir=tmp_path, output_format="omex"
    )
    assert len(locations) == 2
    print(locations)
    assert "./BIOMD0000000001_urn.xml" in locations
    assert "./BIOMD0000000001_url.xml" in locations

    omex_path = tmp_path / f"{biomodel_id}.omex"
    assert omex_path.exists()
    omex = Omex.from_omex(omex_path=omex_path)
    assert len(omex.manifest.entries) == 4


def test_download_biomodel_sbml_failure(tmp_path: Path) -> None:
    """Download OMEX for existing biomodels."""
    with pytest.raises(HTTPError):
        download_biomodel_sbml(biomodel_id="BIOMDXYZ", output_dir=tmp_path)
