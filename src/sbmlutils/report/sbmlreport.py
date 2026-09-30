"""SBML report using a local sbml4humans instance."""

import http.server
import logging
import threading
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class _SingleFileHandler(http.server.BaseHTTPRequestHandler):
    """Handler which serves exactly one file and answers 404 for everything else."""

    served_path: Path
    served_name: str

    def _send_file(self, with_body: bool) -> None:
        """Answer a request for the served file, or 404 for any other path."""
        requested = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        if requested != f"/{self.served_name}":
            self.send_error(404, "Not Found")
            return
        try:
            content = self.served_path.read_bytes()
        except OSError:
            self.send_error(404, "Not Found")
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/xml")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if with_body:
            self.wfile.write(content)

    def do_GET(self) -> None:
        """Serve the model file."""
        self._send_file(with_body=True)

    def do_HEAD(self) -> None:
        """Answer with the headers of the model file."""
        self._send_file(with_body=False)

    def log_message(self, format: str, *args: Any) -> None:
        """Log requests with the module logger instead of stderr."""
        logger.debug("fileserver: %s", format % args)


class _Server(http.server.ThreadingHTTPServer):
    """Threading server which signals that its serve loop is running."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the server."""
        super().__init__(*args, **kwargs)
        self.serving = threading.Event()

    def service_actions(self) -> None:
        """Called on every iteration of the serve loop."""
        if not self.serving.is_set():
            self.serving.set()


def start_server(path: Path, port: int = 5115) -> http.server.ThreadingHTTPServer:
    """Start a webserver on the loopback interface which serves only the file `path`.

    The server runs in a daemon thread and is stopped with `shutdown()`.

    Args:
        path: the one file which is served.
        port: port of the server, 0 selects a free port (see `server_address`).

    Returns:
        the running server.
    """

    class Handler(_SingleFileHandler):
        served_path = path
        served_name = path.name

    httpd = _Server(("127.0.0.1", port), Handler)
    threading.Thread(
        name="daemon_server", target=httpd.serve_forever, daemon=True
    ).start()
    # shutdown() called before serve_forever() is running would block forever
    if not httpd.serving.wait(timeout=5):
        httpd.server_close()
        raise RuntimeError("The file server did not start serving within 5 seconds.")
    return httpd


def create_online_report(
    sbml_path: Path,
    server: str = "http://localhost:3456",
    fileserver_duration: int = 10,
    fileserver_port: int = 5115,
) -> None:
    """Create sbml4humans report.

    The SBML file can be validated during report generation.
    Local parameters can be promoted during report generation.

    :param sbml_path: path to SBML file
    :param server: server to use for report, an sbml4humans instance running on the same machine, with scheme and port
    :param fileserver_duration: duration of file server in seconds
    :param fileserver_port: port of file server

    The model is served on the loopback address (127.0.0.1) and fetched from there by
    the report server, so this works with an sbml4humans running on the same machine
    (the `server` parameter). A remote server cannot reach the model.

    :return: None
    """
    # validate and check arguments
    if not isinstance(sbml_path, Path):
        logger.warning(
            "All paths should be of type 'Path', but '%s' found for: %s",
            type(sbml_path),
            sbml_path,
        )
        sbml_path = Path(sbml_path)

    if not sbml_path.exists():
        raise OSError(f"'sbml_path' does not exist: '{sbml_path}'")

    # serve only the model file, on the loopback interface
    httpd = start_server(sbml_path, fileserver_port)
    # stop the server after the duration, it must not outlive the report in a long running process
    timer = threading.Timer(fileserver_duration, httpd.shutdown)
    timer.daemon = True
    timer.start()

    try:
        # post file via url to sbml4humans server
        url = f"http://127.0.0.1:{httpd.server_address[1]}/{urllib.parse.quote(sbml_path.name)}"
        sbml4humans_url = f"{server}/report?url={urllib.parse.quote(url, safe='')}"
        logger.info("Create report: `%s`", sbml4humans_url)

        # open in browser
        webbrowser.open(sbml4humans_url, new=0)

        # give some time to render report (the fileserver must stay alive)
        timer.join()
    finally:
        timer.cancel()
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    from sbmlutils.resources import REPRESSILATOR_SBML

    create_online_report(sbml_path=REPRESSILATOR_SBML, server="http://localhost:3456")
