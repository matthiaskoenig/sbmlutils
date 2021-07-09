"""API for the sbmlreport web service.

This provides basic functionality of
parsing the model and returning the JSON representation based on fastAPI.
"""
import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from sbmlutils.report.api_examples import examples_info
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo, clean_empty


logger = logging.getLogger(__name__)
app = FastAPI()

# API Permissions Data
origins = ["127.0.0.1", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> Dict:
    """Information to be returned by root path of the API."""
    return {"sbmlutils": "sbml4humans"}


@app.post("/sbml")
async def upload_sbml(request: Request) -> Response:
    """Upload SBML file and return JSON report.

    FIXME: support COMBINE archives
    """
    try:
        file_data = await request.form()

        filename = file_data["source"].filename
        file_content = await file_data["source"].read()
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / filename
            with open(path, "wb") as sbml_file:
                sbml_file.write(file_content)
                content = _content_for_source(source=path)

    except IOError as err:
        logger.error(err)
        content = {"error": "SBML Document could not be parsed."}

    return _render_json_content(content)


@app.get("/examples")
def examples() -> Response:
    """Get sbml4humans example SBML models."""
    api_examples = []
    for example in examples_info.values():
        api_examples.append(example["metadata"])

    content = {"examples": api_examples}
    return _render_json_content(content)


@app.get("/examples/{example_id}")
def example(example_id: str) -> Response:
    """Endpoint to get specific example.

    see `examples`

    E.g. http://127.0.0.1:1444/examples/repressilator -> JSON for repressilator
    :param example_id:
    :return:
    """
    example = examples_info.get(example_id, None)
    content: Dict
    if example:
        source: Path = example["file"]  # type: ignore
        content = _content_for_source(source=source)
    else:
        content = {"error": f"example for id does not exist '{example_id}'"}

    return _render_json_content(content)


def _content_for_source(source: Path) -> Dict:
    """Create content for given source."""
    content: Dict[str, Any] = {}
    try:
        time_start = time.time()
        info = SBMLDocumentInfo.from_sbml(source=source)
        content["report"] = info.info
        time_elapsed = round(time.time() - time_start, 3)
        logger.warning(f"JSON created for '{source}' in '{time_elapsed}'")
        content["debug"] = {"jsonReportTime": f"{time_elapsed} [s]"}

    except IOError as err:
        logger.error(err)
        content = {"error": f"Error creating JSON for '{source}'"}
    return content


def _render_json_content(content: Dict) -> Response:
    """Render content to JSON."""
    # content = clean_empty(content)  # FIXME: use minimal dict
    json_bytes = json.dumps(
        content,
        ensure_ascii=False,
        allow_nan=True,
        indent=0,
        separators=(",", ":"),
    ).encode("utf-8")

    return Response(content=json_bytes, media_type="application/json")


if __name__ == "__main__":
    # shell command: uvicorn sbmlutils.report.api:app --reload --port 1444
    uvicorn.run(
        "sbmlutils.report.api:app",
        host="localhost",
        port=1444,
        log_level="info",
        reload=True,
    )
