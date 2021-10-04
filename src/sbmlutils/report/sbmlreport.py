"""SBML report using https://sbml4humans.de."""

import http.server
import socketserver
import threading
import time
import webbrowser
from pathlib import Path
from typing import Dict

from sbmlutils import __version__
from sbmlutils.console import console
from sbmlutils.log import get_logger


logger = get_logger(__name__)


def start_server(path: Path, port: int = 5115) -> None:
    """Start a simple webserver serving path on port."""

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):  # type: ignore
            """Initialize handler for requests."""
            super().__init__(directory=path, *args, **kwargs)

    with socketserver.TCPServer(("", port), Handler) as httpd:
        httpd.serve_forever()


def create_report(
    sbml_path: Path,
    validate: bool = False,
    server: str = "https://sbml4humans.de",
    fileserver_duration: int = 10,
    fileserver_port: int = 5115,
) -> None:
    """Create sbml4humans report."""

    # FIXME: implement static report
    logger.info(f"No support for 'create_report' in sbmlutils-v{__version__}.")
    pass


def create_online_report(
    sbml_path: Path,
    validate: bool = False,
    server: str = "https://sbml4humans.de",
    fileserver_duration: int = 10,
    fileserver_port: int = 5115,
) -> None:
    """Create sbml4humans report.

    The SBML file can be validated during report generation.
    Local parameters can be promoted during report generation.

    :param sbml_path: path to SBML file
    :param validate: FIXME: add validation option and information in frontend
    :param server: server to use for report, for local development use `localhost:3456`
    :param fileserver_duration: duration of file server in seconds
    :param fileserver_port: port of file server

    :return: None
    """

    # validate and check arguments
    if not isinstance(sbml_path, Path):
        logger.warning(
            f"All paths should be of type 'Path', "
            f"but '{type(sbml_path)}' found for: {sbml_path}"
        )
        sbml_path = Path(sbml_path)

    if not sbml_path.exists():
        raise IOError(f"'sbml_path' does not exist: '{sbml_path}'")

    # serve files

    daemon = threading.Thread(
        name="daemon_server",
        target=start_server,
        args=(sbml_path.parent, fileserver_port),
    )
    # Set as a daemon so it will be killed once the main thread is dead.
    daemon.setDaemon(True)
    daemon.start()

    # post file via url to sbml4humans server
    url = f"http://0.0.0.0:{fileserver_port}/{sbml_path.name}"
    url_encoded = url.replace(":", "%253A")
    url_encoded = url_encoded.replace("/", "%252F")
    sbml4humans_url = f"{server}/model_url?url={url_encoded}"
    logger.info(f"Create report: `{sbml4humans_url}`")

    # open in browser
    webbrowser.open(sbml4humans_url, new=0)

    # give some time to render report (the fileserver must stay alive)
    time.sleep(fileserver_duration)


if __name__ == "__main__":
    from sbmlutils.test import REPRESSILATOR_SBML

    # create_online_report(sbml_path=REPRESSILATOR_SBML)
    create_online_report(sbml_path=REPRESSILATOR_SBML, server="localhost:3456")
