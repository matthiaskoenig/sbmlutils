"""Module for interacting with Cytoscape."""
import tempfile
from pathlib import Path
from typing import Any, Union

from py2cytoscape.data.cyrest_client import CyRestClient  # type: ignore
from requests.exceptions import ConnectionError  # type: ignore

from sbmlutils import log
from sbmlutils.parser import antimony_to_sbml


logger = log.get_logger(__name__)


def visualize_antimony(source: Union[Path, str], delete_session: bool = False) -> Any:
    """Visualize antimony in cytoscape."""
    sbml_str = antimony_to_sbml(source=source)
    tmp_file = tempfile.NamedTemporaryFile()
    with open(tmp_file.name, "w") as f_tmp:
        f_tmp.write(sbml_str)

    visualize_sbml(Path(f_tmp.name), delete_session=delete_session)


def visualize_sbml(sbml_path: Path, delete_session: bool = False) -> Any:
    """Visualize SBML networks in cytoscape."""
    try:
        cy = CyRestClient()
        if delete_session:
            # reset Cytoscape session
            cy.session.delete()
        networks = cy.network.create_from(str(sbml_path))
        return networks
    except ConnectionError:
        logger.error(
            "Could not connect to a running Cytoscape instance. Please "
            "start a Cytoscape instance before execution."
        )
        return None
