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


def download_biomodel_omex(biomodel_id: str, output_dir: Path) -> Path:
    """Download omex for given biomodel id.

    Raises :class:`HTTPError`, if one occurred.
    """
    url = f"https://www.ebi.ac.uk/biomodels/model/download/{biomodel_id}"
    omex_path = Path(output_dir) / f"{biomodel_id}.omex"
    logger.info(f"Download: {omex_path}")
    download_file(url, omex_path)
    return omex_path


def download_biomodel_sbml(
    biomodel_id: str, output_dir: Path, format: str = "sbml"
) -> Optional[Path]:
    """Download SBML file for biomodel.

    :param format: 'sbml' or 'omex'
    """
    with tempfile.TemporaryDirectory() as f_tmp:
        tmp_path = Path(f_tmp)

        try:
            omex_path = download_biomodel_omex(
                biomodel_id=biomodel_id, output_dir=tmp_path
            )
        except HTTPError as err:
            logger.error(err)
            return None

        omex = Omex.from_omex(omex_path)
        # console.log(omex)
        sbml_entries = omex.entries_by_format(format_key="sbml")
        sbml_entry: Optional[ManifestEntry] = None
        for entry in sbml_entries:
            if entry.location.endswith("_url.xml"):
                sbml_entry = entry
                break
        else:
            logger.warning(
                f"No '*_url.xml' in archive: " f"{[e.location for e in sbml_entries]}"
            )
            sbml_entry = sbml_entries[0]

        if sbml_entry:
            entry_path = omex.get_path(sbml_entry.location)
            if format == "sbml":
                sbml_path = Path(output_dir) / sbml_entry.location
                shutil.copyfile(src=entry_path, dst=sbml_path)
                logger.info(sbml_path)
                return Path(sbml_path)
            elif format == "omex":
                omex_path = output_dir / f"{biomodel_id}.omex"
                omex_out = Omex()
                omex_out.add_entry(
                    entry_path=entry_path,
                    entry=ManifestEntry(
                        location=f"./{entry_path.name}",
                        format=EntryFormat.SBML,
                    ),
                )
                omex_out.to_omex(omex_path)
                return omex_path
            else:
                raise ValueError(f"Unsupported format: '{format}'.")

        return None


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


def create_biomodels_testfiles(output_dir: Path) -> None:
    """Download all curated biomodels and create omex files."""
    # query the
    biomodel_ids = query_curated_biomodels()
    console.print(biomodel_ids)
    for biomodel_id in biomodel_ids:

        # download SBML model as omex
        download_biomodel_sbml(biomodel_id, output_dir, format="omex")


if __name__ == "__main__":
    # download_biomodel_sbml(
    #     biomodel_id="BIOMD0000000507", output_dir=Path("./tmp")
    # )
    create_biomodels_testfiles(output_dir=BIOMODELS_CURATED_PATH)
