"""Tests for the cytoscape visualization, which never talks to a live Cytoscape."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from py4cytoscape.exceptions import CyError

from sbmlutils import cytoscape


def test_visualize_sbml_survives_cyerror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A CyError of py4cytoscape is logged and does not abort the script."""
    fake = MagicMock()
    fake.networks.import_network_from_file.side_effect = CyError(
        "Undefined combination of Level 0 and Version 0 for element unitDefinition"
    )
    monkeypatch.setattr(cytoscape, "p4c", fake)

    with caplog.at_level("WARNING", logger="sbmlutils.cytoscape"):
        result = cytoscape.visualize_sbml(tmp_path / "model.xml")

    assert result is None
    assert "Undefined combination of Level 0" in caplog.text


def test_visualize_antimony_returns_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """visualize_antimony returns the value of visualize_sbml."""
    monkeypatch.setattr(cytoscape, "visualize_sbml", lambda *a, **k: 7)
    assert cytoscape.visualize_antimony("J0: S1 -> S2; k1*S1; S1 = 10; k1 = 0.1") == 7


def test_test_session_never_reaches_cytoscape(
    cytoscape_calls: list[tuple[str, tuple, dict]], tmp_path: Path
) -> None:
    """The session guard replaces py4cytoscape and records the calls."""
    cytoscape.visualize_sbml(tmp_path / "model.xml", delete_session=True)
    names = [c[0] for c in cytoscape_calls]
    assert "session.close_session" in names
    assert "networks.import_network_from_file" in names
