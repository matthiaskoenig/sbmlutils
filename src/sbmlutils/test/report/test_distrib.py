"""Tests for distrib features in report.

These tests are specific to the distrib features.
General report generation tests are `test_report.py`.
"""
import logging
from pathlib import Path
from typing import Dict, List

from sbmlutils.io.sbml import read_sbml
from sbmlutils.report import sbmlinfo
from sbmlutils.test import TESTSUITE_PATH


logger = logging.getLogger(__name__)


def test_report_uncertainty_example(tmp_path: Path) -> None:
    """Test creation of report to check uncertainty feature"""
    doc = read_sbml(
        source=TESTSUITE_PATH / "distrib" / "testsuite" / "uncertainty.xml",
        promote=True,
        validate=True,
        log_errors=True,
        units_consistency=True,
        modeling_practice=True,
    )
    model = doc.getModel()
    model_info = sbmlinfo.SBMLModelInfo(doc=doc, model=model, math_render="cmathml")

    assert isinstance(model_info.info, Dict)

    params_info = model_info.info["parameters"]
    assert isinstance(params_info, List)

    param = params_info[0]
    uncertainties = param["uncertainties"]
    assert isinstance(uncertainties, List)

    first_uncertainty = uncertainties[0]

    assert first_uncertainty["metaId"] == "<code>meta_uncertainty1</code>"
    assert first_uncertainty["cvterm"] == (
        '<div class="cvterm"><span class="collection">BQB_IS_DESCRIBED_BY</span>'
        + '<br /><a href="https://identifiers.org/pubmed/123456" target="_blank">'
        + '123456</a><br /><span class="collection">BQB_HAS_PROPERTY</span><br />'
        + '<a href="http://purl.obolibrary.org/obo/ECO_0006016" target="_blank">'
        + "ECO_0006016</a></div>"
    )
    assert first_uncertainty["name"] == "Basic example: 5.0 +- 0.3 [2.0 - 8.0]"

    uncert_parameters = first_uncertainty["uncert_parameters"]
    assert isinstance(uncert_parameters, List)

    first_uncert_param = uncert_parameters[0]
    assert first_uncert_param["value"] == 5.0
    assert first_uncert_param["units"] == "mole"
    assert first_uncert_param["type"] == "mean"
