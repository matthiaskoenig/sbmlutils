"""Module for interacting with Cytoscape."""
from pathlib import Path
from typing import Any

from py2cytoscape.data.cyrest_client import CyRestClient  # type: ignore


def visualize_sbml(sbml_path: Path, delete_session: bool = False) -> Any:
    """Visualize networks in cytoscape."""
    cy = CyRestClient()
    if delete_session:
        # reset Cytoscape session
        cy.session.delete()
    networks = cy.network.create_from(str(sbml_path))
    return networks
