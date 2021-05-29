"""
API for the sbmlreport web service. This provides basic functionality of
parsing the model and returning the JSON representation.

flask
fastapi

"""
import logging

from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

import uvicorn
from fastapi import FastAPI

import libsbml
from sbmlutils.test import REPRESSILATOR_SBML, RECON3D_SBML
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo

logger = logging.getLogger(__name__)
app = FastAPI()

# TODO: create prototype of vue-report in sbml4humans branch;
# TODO: remove the feature vue-prototype branch;
# TODO: close issue #226 https://github.com/matthiaskoenig/sbmlutils/issues/226


# TODO: very simple first prototype for component: component SBase; component Species; component for SBaseListView
# -> Long list of all SBases: * (id, metaId, sbml_type) <- on click show detail View

# TODO: add `sbml_type` attribute in SBMLInfo: Reaction, Species, Compartment, ...


# TODO: implement sbml endpoint;
# TODO: consume this in the vue report
# post SBML file and returns JSON sbmlinfo
# @app.post("/sbml")
# def send_sbml_file(source: libsbml.SBMLDocument, math_render: str): #, file_content: str, filename: str):
#     try:
#         # files_dir = Path(__file__).parent / "file_uploads"
#         # if not output_dir.exists():
#         #     output_dir.mkdir(parents=True, exist_ok=True)
#         #
#         # with open(files_dir / filename, "w") as sbml_file:
#         #     sbml_file.write(file_content)
#         # source = files_dir / filename
#
#         fetch_start = datetime.now()    # debug information
#         info = SBMLDocumentInfo.from_sbml(source=source, math_render=math_render)
#         fetch_end = datetime.now()    # debug information
#         content = info.info
#
#         time_elapsed = (fetch_end - fetch_start).total_seconds()
#     except:
#         content = {
#             "error": "SBML Document could not be parsed."
#         }
#
#         time_elapsed = 0
#
#     content["debug"] = {
#         "json_report_time": f"{time_elapsed} seconds"
#     }
#
#     return content


# post COMBINE archive and returns JSON sbmlinfo
# @app.post("/combine")
@app.get("/")
def read_root():
    return {"sbmlutils": "sbml4humans"}


examples = {
    "repressilator": REPRESSILATOR_SBML,
    "recon3d": RECON3D_SBML
}
# TODO: add a large model example: Recon3D/Recon bigg collection


# TODO: consume this in the vue report
@app.get("/examples/{example_id}")
def read_item(example_id: str) -> Dict:
    """
    example endpoint for testing

    http://127.0.0.1:1444/examples/repressilator -> JSON for repressilator
    :param item_id:
    :return:
    """
    source = examples.get(example_id, None)
    content: Dict

    if source:
        fetch_start = datetime.now()    # debug information
        info = SBMLDocumentInfo.from_sbml(source=source, math_render="latex")
        fetch_end = datetime.now()      # debug information
        content = info.info

        time_elapsed = (fetch_end - fetch_start).total_seconds()
    else:
        content = {
            "error": f"example for id does not exist '{example_id}'"
        }
        time_elapsed = 0

    content["debug"] = {
        "json_report_time": f"{round(time_elapsed, 3)} seconds"
    }

    return content


if __name__ == "__main__":
    # shell command: uvicorn sbmlutils.report.api:app --reload --port 1444
    uvicorn.run("sbmlutils.report.api:app", host="127.0.0.1", port=1444, log_level="info")

