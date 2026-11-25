"""Offline tests of the curated BioModels maintenance script."""

import json
import runpy
from pathlib import Path
from unittest.mock import Mock, call

import pytest
from requests import Response
from requests.exceptions import HTTPError

from scripts import biomodels


def _response(payload: dict[str, object], status: int = 200) -> Response:
    """Build a response with normal JSON and HTTP error handling."""
    response = Response()
    response.status_code = status
    response.url = f"{biomodels.BIOMODELS_URL}/search"
    response._content = json.dumps(payload).encode("utf-8")
    return response


def test_search_paginates_and_sorts(monkeypatch: pytest.MonkeyPatch) -> None:
    """All pages use the curated query and one retrying session."""
    ids = [f"BIOMD{i:010d}" for i in range(101)]
    session = Mock()
    session.get.side_effect = [
        _response({"matches": len(ids)}),
        _response({"models": [{"id": model_id} for model_id in reversed(ids[1:])]}),
        _response({"models": [{"id": ids[0]}]}),
    ]
    get_session = Mock(return_value=session)
    monkeypatch.setattr(biomodels, "get_session", get_session)

    assert biomodels.query_curated_biomodels() == ids
    get_session.assert_called_once_with()
    assert [
        (request.kwargs["params"]["numResults"], request.kwargs["params"].get("offset"))
        for request in session.get.call_args_list
    ] == [(1, None), (100, 0), (100, 100)]
    assert all(
        request.kwargs["params"]["query"] == 'curationstatus:"Manually curated"'
        for request in session.get.call_args_list
    )


def test_search_reports_http_failure_on_a_later_page(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A partial result cannot appear as a complete search."""
    session = Mock()
    session.get.side_effect = [
        _response({"matches": 101}),
        _response({"models": [{"id": "BIOMD0000000001"}]}),
        _response({}, status=503),
    ]
    monkeypatch.setattr(biomodels, "get_session", Mock(return_value=session))

    assert biomodels.main(["search"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "503" in captured.err


def test_refresh_caches_archives_and_creates_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The first refresh creates the fixture directory and later calls reuse it."""
    model_id = "BIOMD0000000001"
    output_dir = tmp_path / "new" / "fixtures"
    monkeypatch.setattr(
        biomodels, "query_curated_biomodels", Mock(return_value=[model_id])
    )

    def fake_download(
        identifier: str, directory: Path, *, output_format: str
    ) -> list[str]:
        assert directory.is_dir()
        assert output_format == "omex"
        (directory / f"{identifier}.omex").touch()
        return ["model.xml"]

    download = Mock(side_effect=fake_download)
    monkeypatch.setattr(biomodels, "download_biomodel_sbml", download)

    argv = ["refresh", "--output-dir", str(output_dir)]
    assert biomodels.main(argv) == 0
    assert biomodels.main(argv) == 0
    assert biomodels.main([*argv, "--no-cache"]) == 0
    expected = call(model_id, output_dir, output_format="omex")
    assert download.call_args_list == [expected, expected]


@pytest.mark.parametrize(
    "failure", [HTTPError("503 Service Unavailable"), []], ids=["http", "no-sbml"]
)
def test_refresh_reports_failure(
    failure: HTTPError | list[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An HTTP error or missing SBML entries fails the explicit refresh."""
    monkeypatch.setattr(
        biomodels, "query_curated_biomodels", Mock(return_value=["BIOMD0000000001"])
    )
    download = (
        Mock(side_effect=failure)
        if isinstance(failure, HTTPError)
        else Mock(return_value=failure)
    )
    monkeypatch.setattr(biomodels, "download_biomodel_sbml", download)

    assert biomodels.main(["refresh", "--output-dir", str(tmp_path)]) == 1
    assert "BioModels refresh failed" in capsys.readouterr().err


def test_refresh_validates_ids_before_cache_lookup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A path to an existing archive outside the directory is never a cache hit."""
    (tmp_path / "outside.omex").touch()
    download = Mock()
    monkeypatch.setattr(biomodels, "download_biomodel_sbml", download)

    with pytest.raises(ValueError, match="Invalid BioModels identifier"):
        biomodels.create_biomodels_testfiles(["../outside"], tmp_path / "fixtures")
    download.assert_not_called()


def test_import_and_no_command_do_not_touch_network_or_disk(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Importing or invoking the CLI without a command does no maintenance."""
    get_session = Mock()
    monkeypatch.setattr("pymetadata.webservices.webservice.get_session", get_session)
    monkeypatch.chdir(tmp_path)
    module = runpy.run_path(biomodels.__file__)
    with pytest.raises(SystemExit) as exc:
        module["main"]([])

    assert exc.value.code == 2
    get_session.assert_not_called()
    assert list(tmp_path.iterdir()) == []


def test_search_command_is_read_only(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The search prints one identifier per line and never runs a refresh."""
    ids = ["BIOMD0000000001", "BIOMD0000000002"]
    monkeypatch.setattr(biomodels, "query_curated_biomodels", Mock(return_value=ids))
    refresh = Mock()
    monkeypatch.setattr(biomodels, "create_biomodels_testfiles", refresh)

    assert biomodels.main(["search"]) == 0
    assert capsys.readouterr().out.splitlines() == ids
    refresh.assert_not_called()


def test_refresh_defaults_to_the_checkout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The default fixture location belongs to the checkout containing the script."""
    monkeypatch.setattr(
        biomodels, "__file__", str(tmp_path / "scripts" / "biomodels.py")
    )
    monkeypatch.setattr(biomodels, "query_curated_biomodels", Mock(return_value=[]))
    refresh = Mock()
    monkeypatch.setattr(biomodels, "create_biomodels_testfiles", refresh)

    assert biomodels.main(["refresh"]) == 0
    refresh.assert_called_once_with(
        [],
        tmp_path / "src" / "sbmlutils" / "resources" / "models" / "biomodels",
        caching=True,
    )
