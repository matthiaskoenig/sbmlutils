"""API for the sbmlreport web service.

This provides basic functionality of
parsing the model and returning the JSON representation based on fastAPI.
"""

import json
import logging
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any, Dict

import requests
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pymetadata.identifiers.miriam import BQB
from pymetadata.core.annotation import RDFAnnotationData, RDFAnnotation


from sbmlutils.report.api_examples import examples_info
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo, clean_empty
from sbmlutils.report.caching import create_job_id, get_report_from_cache, cache_report

logger = logging.getLogger(__name__)
api = FastAPI()

# API Permissions Data
origins = ["127.0.0.1", "*"]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _write_to_file_and_generate_report(
    filename: str, file_content: str, mode: str, uuid: str = "UUID001"
) -> Dict:
    """Write file content to temporary file and generate reoirt."""
    content = {}
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / filename
        with open(path, mode) as sbml_file:
            sbml_file.write(file_content)
            content = _content_for_source(source=path)
    cache_report(uuid, content)
    return content


@api.get("/")
def read_root() -> Dict:
    """Information to be returned by root path of the API."""
    return {"sbmlutils": "sbml4humans"}


@api.post("/sbml")
async def upload_sbml(request: Request) -> Response:
    """Upload SBML file and return JSON report.

    FIXME: support COMBINE archives
    """
    file_data = await request.form()
    file_content = await file_data["source"].read()
    content = get_report_using_uuid(file_content)
    # try:
    #     file_data = await request.form()
    #
    #     filename = file_data["source"].filename
    #     file_content = await file_data["source"].read()
    #     content = _write_to_file_and_generate_report(filename, file_content, "wb")
    # except IOError as err:
    #     logger.error(err)
    #     content = {"error": "SBML Document could not be parsed."}

    return _render_json_content(content)


@api.get("/examples")
def examples() -> Response:
    """Get sbml4humans example SBML models."""
    api_examples = []
    for example in examples_info.values():
        api_examples.append(example["metadata"])

    content = {"examples": api_examples}
    return _render_json_content(content)


@api.get("/examples/{example_id}")
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


@api.get("/resource_info/{resource_id}")
def get_resource_info(resource_id: str) -> Response:
    """Get information for given resource.

    Used to resolve annotation information.

    :param resource_id: unique identifier of resource (url or miriam urn)
    :return: Response
    """
    try:
        print("-" * 80)
        print(resource_id)
        annotation = RDFAnnotation(qualifier=BQB.IS, resource=resource_id)
        data = RDFAnnotationData(annotation=annotation)
        info = data.to_dict()
        print(info)
        print("-" * 80)
        return Response(
            content=json.dumps(info), media_type="application/json"
        )
    except Exception as e:
        logger.error(e)

        res = {
            "errors": [
                f"{e.__str__()}",
                f"{''.join(traceback.format_exception(None, e, e.__traceback__))}"
            ],
            "warnings": []
        }

        return Response(content=json.dumps(res), media_type="application/json")


@api.get("/model_urls/")
def get_report_from_model_url(url: str) -> Response:
    """Get report via URL."""
    data = requests.get(url)

    if data.status_code == 200:
        filename = "temp_sbml.xml"
        file_content = data.text
        content = get_report_using_uuid(file_content)
        #content = _write_to_file_and_generate_report(filename, file_content, "w")
    else:
        content = {"error": "File not found!"}

    return Response(content=json.dumps(content), media_type="application/json")


@api.post("/sbml_content")
async def get_report_from_file_contents(request: Request) -> Response:
    """Create JSON report from file contents."""
    file_content = await request.body()
    filename = "sbml_file.xml"

    try:
        content = _write_to_file_and_generate_report(filename, file_content, "wb")
    except Exception as e:
        print(e)
        content = {"error": "Invalid SBML!"}

    print(content)
    return Response(content=json.dumps(content), media_type="application/json")

def get_report_using_uuid(file_content: str):
    uuid = create_job_id(file_content)
    try:
        report = get_report_from_cache(uuid)
    except Exception as e:
        logger.error(e)
        report = _write_to_file_and_generate_report("temp_model.xml", file_content, "wb", uuid)

    return report

if __name__ == "__main__":
    # shell command: uvicorn sbmlutils.report.api:app --reload --port 1444
    uvicorn.run(
        "sbmlutils.report.api:api",
        host="localhost",
        port=1444,
        log_level="info",
        reload=True,
    )
