"""API for the sbmlreport web service.

This provides basic functionality of
parsing the model and returning the JSON representation based on fastAPI.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

# TODO: create prototype of vue-report in sbml4humans branch;
# TODO: remove the feature vue-prototype branch;
# TODO: close issue #226 https://github.com/matthiaskoenig/sbmlutils/issues/226


@app.get("/")
def read_root():
    """Information to be returned by root path of the API."""
    return {"sbmlutils": "sbml4humans"}


@app.post("/sbml")
async def upload_sbml(request: Request):
    """Upload SBML file and return JSON report.

    FIXME: support COMBINE archives
    """
    content = {}
    try:
        file_data = await request.form()

        math_render = "latex"
        filename = file_data["source"].filename
        file_content = await file_data["source"].read()

        files_dir = Path(__file__).parent / "file_uploads"
        if not files_dir.exists():
            files_dir.mkdir(parents=True, exist_ok=True)

        with open(files_dir / filename, "wb") as sbml_file:
            sbml_file.write(file_content)
        source = files_dir / filename

        fetch_start = datetime.now()  # debug information
        info = SBMLDocumentInfo.from_sbml(source=source, math_render=math_render)
        fetch_end = datetime.now()  # debug information
        content["report"] = info.info

        time_elapsed = (fetch_end - fetch_start).total_seconds()

        os.remove(files_dir / filename)
    except IOError as err:
        logger.error(err)
        content = {"error": "SBML Document could not be parsed."}

        time_elapsed = 0

    content["debug"] = {"jsonReportTime": f"{round(time_elapsed, 3)} seconds"}
    return _render_json_content(content)


@app.get("/examples")
def examples() -> JSONResponse:
    """Get sbml4humans example SBML models."""
    api_examples = []
    for key in examples_info:
        api_examples.append(examples_info[key]["model"])

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
    if example is not None:
        source = example["file"]
    else:
        source = None
    content: Dict = {}

    try:
        fetch_start = datetime.now()  # debug information
        info = SBMLDocumentInfo.from_sbml(source=source)
        fetch_end = datetime.now()  # debug information
        content["report"] = info.info
        time_elapsed = (fetch_end - fetch_start).total_seconds()
        logger.warning(f"JSON created for '{source}' in '{time_elapsed}'")

        # check JSON encoding/decoding
        json_str = info.to_json()
        json.loads(json_str)

    except IOError as err:
        logger.error(err)
        content = {"error": f"example for id does not exist '{example_id}'"}
        time_elapsed = 0

    content["debug"] = {"jsonReportTime": f"{round(time_elapsed, 3)} seconds"}
    return _render_json_content(content)


def _render_json_content(content: Dict) -> Response:
    """Render content to JSON."""
    # FIXME: use the minimal dict
    # content = clean_empty(content)
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
