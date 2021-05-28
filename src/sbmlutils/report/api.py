"""
API for the sbmlreport web service. This provides basic functionality of
parsing the model and returning the JSON representation.

flask
fastapi

"""
import logging

from pathlib import Path
from typing import Optional, Dict

from fastapi import FastAPI

from sbmlutils.test import REPRESSILATOR_SBML
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo

logger = logging.getLogger(__name__)
app = FastAPI()

# TODO: create prototype of vue-report in sbml4humans branch;
# remove the feature vue-prototype branch;
# close issue #226 https://github.com/matthiaskoenig/sbmlutils/issues/226


# TODO: very simple first prototype for component: component SBase; component Species; component for SBaseListView
# -> Long list of all SBases: * (id, metaId, sbml_type) <- on click show detail View

# TODO: add `sbml_type` attribute in SBMLInfo: Reaction; Species, Compartment, ...


# TODO: implement sbml endpoint;
# TODO: consume this in the vue report
# post SBML file and returns JSON sbmlinfo
# @app.post("/sbml")

# post COMBINE archive and returns JSON sbmlinfo
# @app.post("/combine")

@app.get("/")
def read_root():
    return {"sbmlutils": "sbml4humans"}


examples = {
    "repressilator": REPRESSILATOR_SBML
}
# TODO: add a large model example: Recon3D/Recon bigg collection


# TODO: consume this in the vue report
@app.get("/examples/{example_id}")
def read_item(example_id: str) -> Dict:
    """

    example endpoint for testing

    http://127.0.0.1:1444/examples/0 -> JSON for repressilator
    :param item_id:
    :return:
    """
    source = examples.get(example_id, None)
    content: Dict

    if source:
        # TODO: add timing information
        info = SBMLDocumentInfo.from_sbml(source=source, math_render="latex")
        content = info.info
    else:
        content = {
            "error": f"example for id does not exist '{example_id}'"
        }

    content["debug"] = {
        # FIXME inject time
        "json_report_time": 5.1234

    }

    return content


if __name__ == "__main__":
    pass
    # TODO: start uvicorn from python
    # shell command:
    #   uvicorn sbmlutils.report.api:app --reload --port 1444

