"""Module for interacting with Cytoscape."""
import logging
from pathlib import Path
from typing import Any

from py2cytoscape.data.cyrest_client import CyRestClient  # type: ignore
from requests.exceptions import ConnectionError

logger = logging.getLogger(__name__)


def visualize_sbml(sbml_path: Path, delete_session: bool = False) -> Any:
    """Visualize networks in cytoscape."""
    try:
        cy = CyRestClient()
        if delete_session:
            # reset Cytoscape session
            cy.session.delete()
        networks = cy.network.create_from(str(sbml_path))
        return networks
    except (ConnectionRefusedError, ConnectionError) as err:
        logger.error("Could not connect to a running Cytoscape instance. Please "
                     "start a Cytoscape instance before execution.")
        return None
