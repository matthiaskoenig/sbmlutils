"""Utilities for downloading biomodel models.

The downloads go through the shared session of
[pymetadata](https://matthiaskoenig.github.io/pymetadata/api/webservices.webservice/),
which retries the transient error responses (429, 500, 502, 503, 504) with an
exponential backoff and times out after 30 seconds, so a single hiccup of the
BioModels service does not fail a download.
"""

import logging
import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path

from pymetadata.omex import EntryFormat, ManifestEntry, Omex
from pymetadata.webservices.webservice import get_session
from requests.exceptions import HTTPError

from sbmlutils.console import console

logger = logging.getLogger(__name__)


BIOMODELS_URL: str = "https://biomodels.org"

#: size of the chunks a download is streamed in
CHUNK_SIZE: int = 1024


def download_file(url: str, path: Path) -> Path:
    """Download a file.

    A transient error response is retried, see the module documentation.

    Args:
        url: url to download from
        path: file the content is written to

    Returns:
        The path the content was written to.

    Raises:
        HTTPError: if the server answered with an error status
        RequestException: if the server could not be reached
    """
    with get_session().get(url, stream=True) as response:
        response.raise_for_status()
        with open(path, "wb") as f_out:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f_out.write(chunk)

    return path


def download_biomodel_omex(biomodel_id: str, omex_path: Path) -> Path:
    """Download omex for biomodel id.

    This downloads the latest version of the OMEX from biomodels
    via the rest service.

    :returns: path to omex
    Raises :class:`HTTPError`, if one occurred, i.e. if the model does not exist.
    """
    url = f"{BIOMODELS_URL}/model/download/{biomodel_id}"
    logger.info("Download '%s' -> '%s'", url, omex_path)
    download_file(url, omex_path)
    return omex_path


def download_biomodel_sbml(
    biomodel_id: str, output_dir: Path, output_format: str = "sbml"
) -> list[str]:
    """Download SBML file for biomodel.

    Retrieves the archive from biomodels and gets the SBML files from it.
    Stores the raw SBML files for output_format='sbml' or creates an OMEX archive
    in case of output_format='omex'.

    :param output_format: 'sbml' or 'omex'

    :return: list of location strings
    Raises :class:`HTTPError`, if one occurred, i.e. if the model does not exist.
    Raises :class:`ValueError`, if invalid format string is provided.
    """
    with tempfile.TemporaryDirectory() as f_tmp:
        tmp_path = Path(f_tmp)

        omex_path = tmp_path / f"{biomodel_id}.omex"
        download_biomodel_omex(biomodel_id=biomodel_id, omex_path=omex_path)
        omex = Omex.from_omex(omex_path)

        # get SBML models in archive
        sbml_entries = omex.entries_by_format(format_key="sbml")
        if not sbml_entries:
            msg = f"No SBML entries found in archive '{omex_path}'."
            logger.error(msg)
            return []

        if output_format == "omex":
            omex_out_path = output_dir / f"{biomodel_id}.omex"
            omex_out = Omex()
            for sbml_entry in sbml_entries:
                entry_path = omex.get_path(sbml_entry.location)
                omex_out.add_entry(
                    entry_path=entry_path,
                    entry=ManifestEntry(
                        location=f"./{entry_path.name}",
                        format=EntryFormat.SBML,
                    ),
                )
            omex_out.to_omex(omex_out_path)
            logger.info("Save '%s'", omex_path)

        elif output_format == "sbml":
            for sbml_entry in sbml_entries:
                entry_path = omex.get_path(sbml_entry.location)
                sbml_path = Path(output_dir) / sbml_entry.location
                shutil.copyfile(src=entry_path, dst=sbml_path)
                logger.info("Save '%s'", sbml_path)
        else:
            raise ValueError(f"Unsupported format: '{output_format}'.")

        return [e.location for e in sbml_entries]


def query_curated_biomodels() -> list[str]:
    """Query the identifiers of the curated biomodels.

    A transient error response is retried, see the module documentation.

    Returns:
        The sorted identifiers of the manually curated models.

    Raises:
        HTTPError: if the server answered with an error status
        RequestException: if the server could not be reached
    """
    session = get_session()
    url = f"{BIOMODELS_URL}/search?query=curationstatus%3A%22Manually%20curated%22&numResults=1&format=json"
    response = session.get(url)
    response.raise_for_status()
    json = response.json()
    console.print(url)

    matches: int = json["matches"]
    console.print(f"Curated biomodels: {matches}")
    offset: int = 0
    num_results: int = 100
    biomodel_ids = []
    while offset < matches:
        url = f"{BIOMODELS_URL}/search?query=curationstatus%3A%22Manually%20curated%22&numResults={num_results}&offset={offset}&format=json"
        response = session.get(url)
        response.raise_for_status()
        json = response.json()
        ids = [model["id"] for model in json["models"]]
        console.print(f"n={len(ids)} ids, {url}")
        biomodel_ids.extend(ids)
        offset += num_results

    logger.info("Retrieved '%s' identifiers", len(biomodel_ids))
    return sorted(biomodel_ids)


def _create_biomodels_testfiles(
    biomodel_ids: Sequence[str], output_dir: Path, caching: bool = True
) -> None:
    """Download all curated biomodels and create omex files."""
    console.print(f"Number of models: {len(biomodel_ids)}")
    for biomodel_id in biomodel_ids:
        if caching and (output_dir / f"{biomodel_id}.omex").exists():
            console.print(f"Skip cached biomodel '{biomodel_id}'", style="grey0")
            continue

        # download SBML model as omex
        try:
            console.print(f"Download biomodel '{biomodel_id}'", style="blue")
            download_biomodel_sbml(biomodel_id, output_dir, output_format="omex")
        except HTTPError as err:
            logger.error("Could not retrieve OMEX for biomodel: '%s'", biomodel_id)
            logger.error(err)


if __name__ == "__main__":
    """Download curated biomodels

    This script provides support for downloading models from biomodels.

    """

    biomodel_id: str = "BIOMD0000000001"
    with tempfile.TemporaryDirectory() as f_tmp:
        output_dir = Path(f_tmp)
        # output_dir = Path(__name__).parent / "tmp"

        download_biomodel_omex(
            biomodel_id=biomodel_id,
            omex_path=output_dir / f"{biomodel_id}_1.omex",
        )
        download_biomodel_sbml(
            biomodel_id=biomodel_id,
            output_dir=output_dir,
            output_format="sbml",
        )
        download_biomodel_sbml(
            biomodel_id=biomodel_id,
            output_dir=Path(output_dir),
            output_format="omex",
        )
        omex_path = output_dir / f"{biomodel_id}.omex"
        omex = Omex.from_omex(omex_path)
        console.log(omex)

    # from sbmlutils.resources import BIOMODELS_CURATED_PATH
    #
    # biomodel_ids = query_curated_biomodels()
    # _create_biomodels_testfiles(
    #     biomodel_ids=biomodel_ids, output_dir=BIOMODELS_CURATED_PATH, caching=False
    # )
