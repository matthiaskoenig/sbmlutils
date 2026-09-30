"""Tests for the local file server of the online report."""

import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from unittest import mock

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.resources import REPRESSILATOR_SBML


def _get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=5) as response:
        return bytes(response.read())


def test_server_serves_only_the_model(tmp_path: Path) -> None:
    """Only the model file is served, bound to loopback, without listings."""
    model = tmp_path / "model.xml"
    model.write_text("<sbml/>")
    (tmp_path / "secret.txt").write_text("secret")
    httpd = sbmlreport.start_server(model, port=0)
    try:
        host, port = httpd.server_address[:2]
        assert host == "127.0.0.1"
        base = f"http://127.0.0.1:{port}"
        assert _get(f"{base}/model.xml") == b"<sbml/>"
        for other in [
            "/",
            "/secret.txt",
            "/../secret.txt",
            "/%2e%2e/secret.txt",
            "/model.xml/x",
        ]:
            with pytest.raises(urllib.error.HTTPError) as exc:
                _get(base + other)
            assert exc.value.code == 404
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_create_online_report_stops_server() -> None:
    """The report opens the url of the model and stops the server after the duration."""
    with mock.patch("webbrowser.open") as opened:
        sbmlreport.create_online_report(
            REPRESSILATOR_SBML, fileserver_duration=0, fileserver_port=0
        )
    url = opened.call_args.args[0]
    assert url.startswith(
        "https://sbml4humans.de/model_url?url=http%253A%252F%252F127.0.0.1%253A"
    )
    inner = urllib.parse.unquote(urllib.parse.unquote(url.split("url=")[1]))
    with pytest.raises(urllib.error.URLError):
        _get(inner)
