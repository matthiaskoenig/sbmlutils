"""Utilities for downloading biomodel models."""
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

import requests
from pymetadata.omex import EntryFormat, ManifestEntry, Omex
from requests.exceptions import HTTPError

from sbmlutils import log
from sbmlutils.console import console
from sbmlutils.test import BIOMODELS_CURATED_PATH


logger = log.get_logger(__name__)


def download_file(url: str, path: Path) -> Path:
    """Download file from url to path.

    Raises :class:`HTTPError`, if one occurred.
    """

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return path


def download_biomodel_omex(biomodel_id: str, omex_path: Path) -> Path:
    """Download omex for biomodel id.

    This downloads the latest version of the OMEX from biomodels
    via the rest service.

    :returns: path to omex
    Raises :class:`HTTPError`, if one occurred, i.e. if the model does not exist.
    """
    url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodel_id}"
    logger.info(f"Download '{url}' -> '{omex_path}'")
    download_file(url, omex_path)
    return omex_path


def download_biomodel_sbml(
    biomodel_id: str, output_dir: Path, output_format: str = "sbml"
) -> List[str]:
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
            raise ValueError(msg)

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
            logger.info(f"Save '{omex_path}'")

        elif output_format == "sbml":
            for sbml_entry in sbml_entries:
                entry_path = omex.get_path(sbml_entry.location)
                sbml_path = Path(output_dir) / sbml_entry.location
                shutil.copyfile(src=entry_path, dst=sbml_path)
                logger.info(f"Save '{sbml_path}'")
        else:
            raise ValueError(f"Unsupported format: '{output_format}'.")

        return [e.location for e in sbml_entries]


def query_curated_biomodels() -> List[str]:
    """Query the curated biomodels.

    :return List of biomodel identifiers
    """
    url = "https://www.ebi.ac.uk/biomodels/search?query=curationstatus%3A%22Manually%20curated%22&numResults=1&format=json"
    response = requests.get(url)
    response.raise_for_status()
    json = response.json()

    matches: int = json["matches"]
    offset = 0
    biomodel_ids = []
    while offset < matches:
        url = f"https://www.ebi.ac.uk/biomodels/search?query=curationstatus%3A%22Manually%20curated%22&numResults=100&offset={offset}&format=json"
        logger.info(url)
        response = requests.get(url)
        response.raise_for_status()
        json = response.json()
        ids = [model["id"] for model in json["models"]]
        biomodel_ids.extend(ids)
        offset += 100

    logger.info(f"Retrieved '{len(biomodel_ids)}' identifiers")
    return sorted(biomodel_ids)


def _create_biomodels_testfiles(output_dir: Path) -> None:
    """Download all curated biomodels and create omex files."""
    # query the
    biomodel_ids = query_curated_biomodels()
    console.print(biomodel_ids)
    for biomodel_id in biomodel_ids:

        # download SBML model as omex
        try:
            download_biomodel_sbml(biomodel_id, output_dir, output_format="omex")
        except HTTPError as err:
            logger.error(f"Could not retrieve OMEX for biomodel: '{biomodel_id}'")
            logger.error(err)


if __name__ == "__main__":
    """Download curated biomodels

    This script provides support for downloading models from biomodels.

    """

    with tempfile.TemporaryDirectory() as f_tmp:
        output_dir = Path(f_tmp)
        # output_dir = Path(__name__).parent / "tmp"

        download_biomodel_omex(
            biomodel_id="BIOMD0000000001",
            omex_path=output_dir / "BIOMD0000000001_1.omex",
        )
        download_biomodel_sbml(
            biomodel_id="BIOMD0000000001",
            output_dir=output_dir,
            output_format="sbml",
        )
        download_biomodel_sbml(
            biomodel_id="BIOMD0000000001",
            output_dir=Path(output_dir),
            output_format="omex",
        )
        omex_path = output_dir / "BIOMD0000000001.omex"
        omex = Omex.from_omex(omex_path)
        console.log(omex)

    _create_biomodels_testfiles(output_dir=BIOMODELS_CURATED_PATH)
