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
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from pymetadata.omex import EntryFormat, ManifestEntry, Omex
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


@pytest.mark.network
@pytest.mark.usefixtures("biomodels_available")
def test_download_biomodel_omex_success(tmp_path: Path) -> None:
    """Download OMEX for existing biomodels."""
    omex_path = tmp_path / "tests.omex"
    download_biomodel_omex(biomodel_id=BIOMODEL_ID, omex_path=omex_path)
    assert omex_path.exists()
    assert omex_path.is_file()
    omex = Omex.from_omex(omex_path)
    assert omex


@pytest.mark.network
@pytest.mark.usefixtures("biomodels_available")
def test_download_biomodel_omex_failure(tmp_path: Path) -> None:
    """Download OMEX for a biomodel which does not exist."""
    omex_path = tmp_path / "tests.omex"
    with pytest.raises(HTTPError):
        download_biomodel_omex(biomodel_id=BIOMODEL_ID_INVALID, omex_path=omex_path)


@pytest.mark.network
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


@pytest.mark.network
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


@pytest.mark.network
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


class _CraftedOmex:
    """An archive whose manifest lists one SBML entry at a chosen location."""

    def __init__(self, location: str, sbml_file: Path) -> None:
        self.location = location
        self.sbml_file = sbml_file

    def entries_by_format(
        self,
        format_key: str,  # noqa: ARG002 - called by keyword, the name is the API
    ) -> list[ManifestEntry]:
        """Return the single crafted entry.

        pymetadata validates the location of a `ManifestEntry` and refuses an
        absolute or escaping one, so the hostile entry a crafted archive could
        carry is built without validation: `_contained_path` of sbmlutils is
        what the tests below exercise, not the validation of pymetadata.
        """
        return [
            ManifestEntry.model_construct(
                location=self.location, format=EntryFormat.SBML
            )
        ]

    def get_path(self, _location: str) -> Path:
        """Return the file behind the entry."""
        return self.sbml_file


@pytest.fixture
def crafted_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[[str], Path]:
    """Make `download_biomodel_sbml` read a crafted archive without the network.

    Returns a function which sets the location of the manifest entry and gives the
    output directory, which sits inside a parent directory the test can inspect.
    """
    sbml_file = tmp_path / "source.xml"
    sbml_file.write_text("<sbml/>")
    out_dir = tmp_path / "parent" / "out"
    out_dir.mkdir(parents=True)

    def prepare(location: str) -> Path:
        crafted = _CraftedOmex(location, sbml_file)
        monkeypatch.setattr(
            "sbmlutils.biomodels.download_biomodel_omex", lambda **_kwargs: None
        )
        monkeypatch.setattr(
            "sbmlutils.biomodels.Omex.from_omex", lambda *_args, **_kwargs: crafted
        )
        return out_dir

    return prepare


@pytest.mark.parametrize("location", ["../escaped.xml", "sub/../../escaped.xml"])
def test_download_biomodel_sbml_rejects_escaping_location(
    crafted_download: Callable[[str], Path], location: str
) -> None:
    """A location which climbs out of the output directory is refused."""
    out_dir = crafted_download(location)
    with pytest.raises(ValueError, match="outside of the output directory"):
        download_biomodel_sbml("BIOMD0000000001", output_dir=out_dir)
    assert not (out_dir.parent / "escaped.xml").exists()


def test_download_biomodel_sbml_rejects_absolute_location(
    crafted_download: Callable[[str], Path], tmp_path: Path
) -> None:
    """An absolute location does not write to that absolute path."""
    target = tmp_path / "absolute.xml"
    out_dir = crafted_download(str(target))
    with pytest.raises(ValueError, match="outside of the output directory"):
        download_biomodel_sbml("BIOMD0000000001", output_dir=out_dir)
    assert not target.exists()


@pytest.mark.parametrize(
    "location", ["../escaped.xml", "sub/../../escaped.xml", "/absolute/escaped.xml"]
)
def test_manifest_entry_rejects_hostile_location(location: str) -> None:
    """The validation of pymetadata refuses an absolute or escaping location.

    This is the first line of defense and the reason the tests above build the
    entry without validation; `_contained_path` stays as the second one for an
    entry which did not come through the validation.
    """
    with pytest.raises(ValueError, match="location"):
        ManifestEntry(location=location, format=EntryFormat.SBML)


def test_download_biomodel_sbml_subdirectory_location(
    crafted_download: Callable[[str], Path],
) -> None:
    """A location in a subdirectory creates the directory inside the output."""
    out_dir = crafted_download("./sub/model.xml")
    locations = download_biomodel_sbml("BIOMD0000000001", output_dir=out_dir)
    assert locations == ["./sub/model.xml"]
    assert (out_dir / "sub" / "model.xml").read_text() == "<sbml/>"
