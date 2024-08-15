"""Module for visualiation in Cytoscape."""

import os
import tempfile


os.environ["PY4CYTOSCAPE_DETAIL_LOGGER_DIR"] = str(tempfile.gettempdir())

from pathlib import Path  # noqa: E402
from typing import Any, Union  # noqa: E402

import py4cytoscape as p4c  # type: ignore  # noqa: E402
from requests.exceptions import RequestException  # noqa: E402

from sbmlutils import log  # noqa: E402
from sbmlutils.console import console  # noqa: E402
from sbmlutils.parser import antimony_to_sbml  # noqa: E402


logger = log.get_logger(__name__)


def visualize_antimony(source: Union[Path, str], delete_session: bool = False) -> Any:
    """Visualize antimony in cytoscape."""
    sbml_str = antimony_to_sbml(source=source)
    tmp_file = tempfile.NamedTemporaryFile()
    with open(tmp_file.name, "w") as f_tmp:
        f_tmp.write(sbml_str)

    visualize_sbml(Path(f_tmp.name), delete_session=delete_session)


def visualize_sbml(sbml_path: Path, delete_session: bool = False) -> None:
    """Visualize SBML networks in cytoscape."""

    try:
        console.print(p4c.cytoscape_version_info())

        if delete_session:
            p4c.session.close_session(save_before_closing=False)

        p4c.networks.import_network_from_file(str(sbml_path))

    except RequestException:
        logger.error(
            "Could not connect to a running Cytoscape instance. "
            "Start Cytoscape before running the python script."
        )
