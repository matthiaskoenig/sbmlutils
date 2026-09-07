"""Testing the biomodels module.

The tests query the BioModels web service and therefore need network access.
The service refuses the requests of some hosts, e.g. the GitHub runners, which
is not a problem of sbmlutils: such a test is skipped instead of failing, see
`biomodels_available`.
"""

from pathlib import Path

import pytest
import requests
from pymetadata.omex import Omex
from requests.exceptions import HTTPError, RequestException

from sbmlutils.biomodels import (
    BIOMODELS_URL,
    download_biomodel_omex,
    download_biomodel_sbml,
)


@pytest.fixture(scope="module")
def biomodels_available() -> None:
    """Skip the test when the BioModels service does not answer.

    Raises:
        Skipped: if the service is unreachable or refuses the request.
    """
    try:
        response = requests.get(f"{BIOMODELS_URL}/BIOMD0000000001", timeout=30)
        response.raise_for_status()
    except RequestException as err:
        pytest.skip(f"BioModels is not available: {err}")


def test_download_biomodel_omex_success(
    tmp_path: Path, biomodels_available: None
) -> None:
    """Download OMEX for existing biomodels."""
    biomodel_id = "BIOMD0000000001"
    omex_path = tmp_path / "tests.omex"
    download_biomodel_omex(biomodel_id=biomodel_id, omex_path=omex_path)
    assert omex_path.exists()
    assert omex_path.is_file()
    omex = Omex.from_omex(omex_path)
    assert omex


def test_download_biomodel_omex_failure(tmp_path: Path) -> None:
    """Download OMEX for existing biomodels."""
    with pytest.raises(HTTPError):
        omex_path = tmp_path / "tests.omex"
        download_biomodel_omex(biomodel_id="BIOMDXYZ", omex_path=omex_path)


def test_download_biomodel_sbml_sbml_success(
    tmp_path: Path, biomodels_available: None
) -> None:
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


def test_download_biomodel_sbml_omex_success(
    tmp_path: Path, biomodels_available: None
) -> None:
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
