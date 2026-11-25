"""Search curated BioModels and refresh the repository's SBML fixtures."""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from pymetadata.webservices.webservice import get_session
from requests.exceptions import RequestException
from rich.console import Console

from sbmlutils import RESOURCES_DIR
from sbmlutils.biomodels import (
    BIOMODELS_URL,
    _check_biomodel_id,
    download_biomodel_sbml,
)
from sbmlutils.console import console
from sbmlutils.resources import BIOMODELS_CURATED_PATH
from sbmlutils.utils import contained_path

logger = logging.getLogger(__name__)


def query_curated_biomodels() -> list[str]:
    """Return sorted identifiers of manually curated models.

    The shared pymetadata session retries transient responses and applies a
    timeout. Request failures abort the search.

    Raises:
        RequestException: if any page could not be retrieved.
    """
    session = get_session()
    url = f"{BIOMODELS_URL}/search"
    params: dict[str, str | int] = {
        "query": 'curationstatus:"Manually curated"',
        "format": "json",
    }
    response = session.get(url, params={**params, "numResults": 1})
    response.raise_for_status()
    matches: int = response.json()["matches"]

    page_size = 100
    biomodel_ids: list[str] = []
    for offset in range(0, matches, page_size):
        response = session.get(
            url, params={**params, "numResults": page_size, "offset": offset}
        )
        response.raise_for_status()
        biomodel_ids.extend(model["id"] for model in response.json()["models"])
    return sorted(biomodel_ids)


def create_biomodels_testfiles(
    biomodel_ids: Sequence[str], output_dir: Path, caching: bool = True
) -> None:
    """Save the SBML entries of each model in a fixture OMEX archive.

    Args:
        biomodel_ids: model identifiers to download.
        output_dir: directory in which to save the fixtures.
        caching: skip existing fixture archives when true.

    Raises:
        RequestException: if a model could not be downloaded.
        ValueError: if a model identifier or archive destination is unsafe, or
            an archive contains no SBML entries.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for biomodel_id in biomodel_ids:
        _check_biomodel_id(biomodel_id)
        archive = contained_path(output_dir, f"{biomodel_id}.omex")
        if caching and archive.is_file():
            logger.info("Skip cached BioModels fixture '%s'", biomodel_id)
            continue

        if not download_biomodel_sbml(biomodel_id, output_dir, output_format="omex"):
            raise ValueError(
                f"BioModels archive '{biomodel_id}' contains no SBML files."
            )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the read-only search or an explicit fixture refresh."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("search", help="Print sorted curated model identifiers.")
    refresh = commands.add_parser("refresh", help="Download SBML-only OMEX fixtures.")
    refresh.add_argument(
        "--output-dir", type=Path, help="Fixture directory (defaults to the checkout)."
    )
    refresh.add_argument(
        "--no-cache", action="store_true", help="Download existing fixtures again."
    )
    args = parser.parse_args(argv)

    try:
        biomodel_ids = query_curated_biomodels()
        if args.command == "search":
            for biomodel_id in biomodel_ids:
                console.print(biomodel_id, highlight=False)
        else:
            output_dir = args.output_dir
            if output_dir is None:
                resource_path = BIOMODELS_CURATED_PATH.relative_to(RESOURCES_DIR)
                root = Path(__file__).resolve().parent.parent
                output_dir = root / "src" / "sbmlutils" / "resources" / resource_path
            create_biomodels_testfiles(
                biomodel_ids, output_dir, caching=not args.no_cache
            )
    except (OSError, RequestException, ValueError) as err:
        Console(stderr=True).print(
            f"BioModels {args.command} failed. {err}", style="red", markup=False
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
