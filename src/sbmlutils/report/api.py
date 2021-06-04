"""
API for the sbmlreport web service. This provides basic functionality of
parsing the model and returning the JSON representation.

fastapi

"""
import os
import logging
import json

from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

import libsbml
from sbmlutils.test import (
    REPRESSILATOR_SBML, RECON3D_SBML, ICG_LIVER, ICG_BODY_FLAT, ICG_BODY,
)
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo

logger = logging.getLogger(__name__)
app = FastAPI()

origins = [
    "127.0.0.1",
    "*"
]

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


@app.post("/sbml")
async def send_sbml_file(request: Request):
    """
    Upload SBML file and return JSON report.
    """
    content = {}
    try:
        file_data = await request.form()

        math_render = file_data["math"]
        filename = file_data["source"].filename
        file_content = await file_data["source"].read()

        files_dir = Path(__file__).parent / "file_uploads"
        if not files_dir.exists():
            files_dir.mkdir(parents=True, exist_ok=True)

        with open(files_dir / filename, "wb") as sbml_file:
            sbml_file.write(file_content)
        source = files_dir / filename

        fetch_start = datetime.now()    # debug information
        info = SBMLDocumentInfo.from_sbml(source=source, math_render=math_render)
        fetch_end = datetime.now()    # debug information
        content["report"] = info.info

        time_elapsed = (fetch_end - fetch_start).total_seconds()

        os.remove(files_dir / filename)
    except:
        content = {
            "error": "SBML Document could not be parsed."
        }

        time_elapsed = 0

    content["debug"] = {
        "json_report_time": f"{round(time_elapsed, 3)} seconds"
    }

    res = Response(content=json.dumps(content, indent=2), media_type="application/json")
    print(res.__dict__)
    return res


# post COMBINE archive and returns JSON sbmlinfo
# @app.post("/combine")
@app.get("/")
def read_root():
    return {"sbmlutils": "sbml4humans"}


examples = {
    "repressilator": REPRESSILATOR_SBML,
    "recon3d": RECON3D_SBML,
    "icg_liver": ICG_LIVER,
    "icg_body_flat": ICG_BODY_FLAT,
    "icg_body": ICG_BODY,
}

@app.get("/examples/list")
async def list_of_examples():
    """
    Endpoint to fetch all available examples in the API
    """
    list_of_examples = []
    for key in examples:
        list_of_examples.append({
            "name": key.replace('_', ' ').title(),
            "id": key
        })

    content = {
        "examples": list_of_examples
    }
    res = Response(content=json.dumps(content, indent=2), media_type="application/json")

    print(res.__dict__)
    return res


@app.get("/examples/{example_id}")
def read_item(example_id: str) -> Dict:
    """
    example endpoint for testing

    http://127.0.0.1:1444/examples/repressilator -> JSON for repressilator
    :param item_id:
    :return:
    """
    source = examples.get(example_id, None)
    content: Dict = {}

    try:
        fetch_start = datetime.now()    # debug information
        info = SBMLDocumentInfo.from_sbml(source=source, math_render="latex")
        fetch_end = datetime.now()      # debug information
        content["report"] = info.info

        time_elapsed = (fetch_end - fetch_start).total_seconds()
    except:
        content = {
            "error": f"example for id does not exist '{example_id}'"
        }
        time_elapsed = 0

    content["debug"] = {
        "json_report_time": f"{round(time_elapsed, 3)} seconds"
    }

    res = Response(content=json.dumps(content, indent=2), media_type="application/json")
    print(res.__dict__)
    return res


if __name__ == "__main__":
    # shell command: uvicorn sbmlutils.report.api:app --reload --port 1444
    uvicorn.run("sbmlutils.report.api:app", host="localhost", port=1444, log_level="info")

