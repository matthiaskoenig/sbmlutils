"""Testing the biomodels module.

The tests query the live BioModels web service and therefore need network
access. `sbmlutils.biomodels` retries the transient error responses, so a hiccup
of the service does not fail a test, but two things are outside its control:
the service can be unreachable, and it refuses the requests of some hosts (the
GitHub runners get a `403 Forbidden`). Neither is a problem of sbmlutils, so
every test which queries the service uses `biomodels_available` and is skipped
rather than failed when the service does not answer.

The probe goes to the endpoint the tests download from, so a test which runs has
actually reached the service, and the failure cases (`BIOMDXYZ` does not exist)
assert what they mean to assert instead of passing on a `403` for everything.
"""

import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from pymetadata.omex import Omex
from pymetadata.webservices.webservice import get_session
from requests.exceptions import HTTPError, RequestException

from sbmlutils.biomodels import (
    BIOMODELS_URL,
    download_biomodel_omex,
    download_biomodel_sbml,
    download_file,
)

#: a model which exists, used by the tests and by the probe
BIOMODEL_ID = "BIOMD0000000001"
#: an identifier which does not exist, the service answers with an error
BIOMODEL_ID_INVALID = "BIOMDXYZ"


@pytest.fixture(scope="module")
def biomodels_available() -> None:
    """Skip the test when the BioModels download service does not answer.

    The request goes through the retrying session of `sbmlutils.biomodels`, so a
    transient error is retried before the tests are given up on.

    Raises:
        Skipped: if the service is unreachable or refuses the request.
    """
    url = f"{BIOMODELS_URL}/model/download/{BIOMODEL_ID}"
    try:
        with get_session().get(url, stream=True) as response:
            response.raise_for_status()
    except RequestException as err:
        pytest.skip(f"BioModels does not answer '{url}': {err}")


@pytest.mark.usefixtures("biomodels_available")
def test_download_biomodel_omex_success(tmp_path: Path) -> None:
    """Download OMEX for existing biomodels."""
    omex_path = tmp_path / "tests.omex"
    download_biomodel_omex(biomodel_id=BIOMODEL_ID, omex_path=omex_path)
    assert omex_path.exists()
    assert omex_path.is_file()
    omex = Omex.from_omex(omex_path)
    assert omex


@pytest.mark.usefixtures("biomodels_available")
def test_download_biomodel_omex_failure(tmp_path: Path) -> None:
    """Download OMEX for a biomodel which does not exist."""
    with pytest.raises(HTTPError):
        omex_path = tmp_path / "tests.omex"
        download_biomodel_omex(biomodel_id=BIOMODEL_ID_INVALID, omex_path=omex_path)


@pytest.mark.usefixtures("biomodels_available")
def test_download_biomodel_sbml_sbml_success(tmp_path: Path) -> None:
    """Download SBML for existing biomodels."""
    locations = download_biomodel_sbml(
        biomodel_id=BIOMODEL_ID, output_dir=tmp_path, output_format="sbml"
    )
    assert len(locations) == 2
    assert f"./{BIOMODEL_ID}_urn.xml" in locations
    assert f"./{BIOMODEL_ID}_url.xml" in locations
    assert (tmp_path / locations[0]).exists()
    assert (tmp_path / locations[1]).exists()


@pytest.mark.usefixtures("biomodels_available")
def test_download_biomodel_sbml_omex_success(tmp_path: Path) -> None:
    """Download SBML for existing biomodels."""
    locations = download_biomodel_sbml(
        biomodel_id=BIOMODEL_ID, output_dir=tmp_path, output_format="omex"
    )
    assert len(locations) == 2
    assert f"./{BIOMODEL_ID}_urn.xml" in locations
    assert f"./{BIOMODEL_ID}_url.xml" in locations

    omex_path = tmp_path / f"{BIOMODEL_ID}.omex"
    assert omex_path.exists()
    omex = Omex.from_omex(omex_path=omex_path)
    assert len(omex.manifest.entries) == 4


@pytest.mark.usefixtures("biomodels_available")
def test_download_biomodel_sbml_failure(tmp_path: Path) -> None:
    """Download SBML for a biomodel which does not exist."""
    with pytest.raises(HTTPError):
        download_biomodel_sbml(biomodel_id=BIOMODEL_ID_INVALID, output_dir=tmp_path)


class _FlakyHandler(BaseHTTPRequestHandler):
    """Answer with `503` until `failures` responses were given, then with the content."""

    #: number of error responses before the request succeeds
    failures = 2
    #: what a successful response returns
    content = b"<sbml/>"
    #: responses given so far, reset by the fixture
    calls = 0

    def do_GET(self) -> None:
        """Answer a GET request."""
        type(self).calls += 1
        if type(self).calls <= type(self).failures:
            self.send_error(503, "temporarily unavailable")
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(type(self).content)))
        self.end_headers()
        self.wfile.write(type(self).content)

    def log_message(self, format: str, *args: object) -> None:
        """Keep the server quiet."""


@pytest.fixture
def flaky_server() -> Iterator[str]:
    """Serve a url which fails with `503` twice before it answers.

    Yields:
        The url of the server, which is shut down afterwards.
    """
    _FlakyHandler.calls = 0
    server = HTTPServer(("127.0.0.1", 0), _FlakyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/model.xml"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_download_file_retries_transient_error(
    tmp_path: Path, flaky_server: str
) -> None:
    """A transient error response is retried instead of failing the download."""
    path = download_file(flaky_server, tmp_path / "model.xml")

    assert path.read_bytes() == _FlakyHandler.content
    # the two error responses plus the one which answered
    assert _FlakyHandler.calls == _FlakyHandler.failures + 1
