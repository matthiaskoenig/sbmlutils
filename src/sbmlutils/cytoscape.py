"""Module for interacting with Cytoscape."""
from pathlib import Path
from typing import Any

from py2cytoscape.data.cyrest_client import CyRestClient  # type: ignore
from requests.exceptions import ConnectionError  # type: ignore

from sbmlutils import log


logger = log.get_logger(__name__)


def visualize_sbml(sbml_path: Path, delete_session: bool = False) -> Any:
    """Visualize networks in cytoscape."""
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
