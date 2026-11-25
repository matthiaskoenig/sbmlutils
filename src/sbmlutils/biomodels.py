"""Utilities for downloading biomodel models.

The downloads go through the shared session of
[pymetadata](https://matthiaskoenig.github.io/pymetadata/api/webservices.webservice/),
which retries the transient error responses (429, 500, 502, 503, 504) with an
exponential backoff and times out after 30 seconds, so a single hiccup of the
BioModels service does not fail a download.
"""

import logging
import re
import shutil
import tempfile
from pathlib import Path

from pymetadata.omex import EntryFormat, ManifestEntry, Omex
from pymetadata.webservices.webservice import get_session
from rich.text import Text

from sbmlutils.console import console, path_text
from sbmlutils.utils import contained_path

logger = logging.getLogger(__name__)


BIOMODELS_URL: str = "https://biomodels.org"

#: size of the chunks a download is streamed in
CHUNK_SIZE: int = 64 * 1024


def _check_biomodel_id(biomodel_id: str) -> None:
    """Accept a single identifier, never a URL or filesystem path."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", biomodel_id):
        raise ValueError(f"Invalid BioModels identifier: {biomodel_id!r}")


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
    path = Path(path)
    # the content goes into a file next to the target, which replaces the
    # target only once the download is complete: an interrupted download
    # leaves neither a truncated file nor the previous one damaged
    partial = path.with_name(f".{path.name}.part")
    try:
        with get_session().get(url, stream=True) as response:
            response.raise_for_status()
            with partial.open("wb") as f_out:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    f_out.write(chunk)
        partial.replace(path)
    finally:
        partial.unlink(missing_ok=True)

    return path


def download_biomodel_omex(biomodel_id: str, omex_path: Path) -> Path:
    """Download omex for biomodel id.

    This downloads the latest version of the OMEX from biomodels
    via the rest service.

    :returns: path to omex
    Raises :class:`HTTPError`, if one occurred, i.e. if the model does not exist.
    """
    _check_biomodel_id(biomodel_id)
    url = f"{BIOMODELS_URL}/model/download/{biomodel_id}"
    console.print(
        Text.assemble(("Download", "bold"), f" {url} to ", path_text(omex_path))
    )
    download_file(url, omex_path)
    return omex_path


def _contained_path(output_dir: Path, location: str) -> Path:
    """Resolve the location of a manifest entry below the output directory.

    The location comes from the manifest of a downloaded archive and is not
    trusted: an absolute location or one which climbs out with `..` must not
    make the download write outside of the output directory.

    Args:
        output_dir: directory the file has to stay in
        location: location of the entry in the archive, e.g. `./model.xml`

    Returns:
        The path of the file in the output directory.

    Raises:
        ValueError: if the location leaves the output directory
    """
    return contained_path(output_dir, location)


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
    Raises :class:`ValueError`, if invalid format string is provided or if the
    location of an entry in the archive is outside of `output_dir`.
    """
    _check_biomodel_id(biomodel_id)
    if output_format not in {"sbml", "omex"}:
        raise ValueError(f"Unsupported format: '{output_format}'.")
    output_dir = Path(output_dir)
    omex_out_path = contained_path(output_dir, f"{biomodel_id}.omex")
    with tempfile.TemporaryDirectory() as f_tmp:
        tmp_path = Path(f_tmp)

        omex_path = tmp_path / f"{biomodel_id}.omex"
        download_biomodel_omex(biomodel_id=biomodel_id, omex_path=omex_path)
        omex = Omex.from_omex(omex_path)

        # get SBML models in archive
        sbml_entries = omex.entries_by_format(format_key="sbml")
        if not sbml_entries:
            logger.error("No SBML entries found in archive '%s'.", omex_path)
            return []

        if output_format == "omex":
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
            console.print(
                Text.assemble(
                    ("OMEX", "bold"), " written to ", path_text(omex_out_path)
                )
            )

        elif output_format == "sbml":
            for sbml_entry in sbml_entries:
                entry_path = omex.get_path(sbml_entry.location)
                sbml_path = _contained_path(Path(output_dir), sbml_entry.location)
                sbml_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src=entry_path, dst=sbml_path)
                console.print(
                    Text.assemble(
                        ("SBML", "bold"), " written to ", path_text(sbml_path)
                    )
                )
        else:
            raise ValueError(f"Unsupported format: '{output_format}'.")

        return [e.location for e in sbml_entries]
