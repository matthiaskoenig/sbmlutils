"""Test SBML report."""
import logging
from pathlib import Path
from typing import Dict, List

import pytest

from sbmlutils.io.sbml import read_sbml
from sbmlutils.report import sbmlinfo, sbmlreport
from sbmlutils.test import (
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    REPRESSILATOR_SBML,
    TESTSUITE_PATH,
    VDP_SBML,
)


logger = logging.getLogger(__name__)

# fetch individual models under the testsuite

# distrib
distrib_model_ids = (
    [i for i in range(40, 48)]
    + [49, 50, 51, 52, 56, 65, 69]
    + [i for i in range(69, 104)]
)
distrib_paths = [TESTSUITE_PATH / "distrib" / "testsuite" / "uncertainty.xml"]
for level_ver in ["l3v1", "l3v2"]:
    for i in distrib_model_ids:
        distrib_paths.append(
            TESTSUITE_PATH / "distrib" / "testsuite" / f"00{i:0>3}-sbml-{level_ver}.xml"
        )

# dfba
diauxic_types = ["bounds", "fba", "top", "update"]
dfba_paths = [TESTSUITE_PATH / "dfba" / f"diauxic_{type}.xml" for type in diauxic_types]

# interpolation
interpolation_types = ["constant", "cubic", "linear"]
interpolation_paths = []
for type in interpolation_types:
    interpolation_paths.append(TESTSUITE_PATH / "interpolation" / f"data1_{type}.xml")

# manipulation
manip_paths = []
for id in range(1, 5):
    manip_paths.append(
        TESTSUITE_PATH / "manipulation" / "merge" / f"BIOMD000000000{id}.xml"
    )
    manip_paths.append(
        TESTSUITE_PATH / "manipulation" / "output" / f"BIOMD000000000{id}_L3.xml"
    )
manip_paths.append(
    TESTSUITE_PATH / "manipulation" / "output" / "merged.xml",
)
manip_paths.append(
    TESTSUITE_PATH / "manipulation" / "output" / "merged_flat.xml",
)

# sbml
sbml_paths = [
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    REPRESSILATOR_SBML,
    VDP_SBML,
]

# concatenated model paths for uncertainty tests
uncertainty_model_paths = (
    distrib_paths + dfba_paths + manip_paths + interpolation_paths + sbml_paths
)


# tests and helper functions
def sbml_paths_idfn(sbml_path):
    return sbml_path.name


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_report(sbml_path, tmp_path):
    """Test report generation."""
    sbmlreport.create_report(sbml_path=sbml_path, output_dir=tmp_path)


@pytest.mark.parametrize("sbml_path", [GZ_SBML], ids=sbml_paths_idfn)
def test_report_gz(sbml_path, tmp_path):
    """Test report generation for GZ reports."""
    sbmlreport.create_report(sbml_path=sbml_path, output_dir=tmp_path)


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_report_latex(sbml_path: Path, tmp_path):
    """Test creation of report with Latex Math."""
    check_report_math_type(sbml_path=sbml_path, math_type="latex", tmp_path=tmp_path)


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_report_cmathml(sbml_path: Path, tmp_path):
    """Test creation of report with Content MathML."""
    check_report_math_type(sbml_path=sbml_path, math_type="cmathml", tmp_path=tmp_path)


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=sbml_paths_idfn)
def test_report_pmathml(sbml_path: Path, tmp_path):
    """Test creation of report with Presentation MathML."""
    check_report_math_type(sbml_path=sbml_path, math_type="cmathml", tmp_path=tmp_path)


def check_report_math_type(sbml_path: Path, math_type: str, tmp_path):
    """Checks SBML report with given math type."""
    html = sbmlreport.create_report(
        sbml_path=sbml_path, output_dir=tmp_path, math_type=math_type
    )

    # check the returned HTML in the variable for correctness of type
    assert html
    assert isinstance(html, str)


@pytest.mark.parametrize("sbml_path", uncertainty_model_paths, ids=sbml_paths_idfn)
def test_report_uncertainty(sbml_path: Path, tmp_path):
    """Test creation of report to check uncertainty feature"""
    check_report_math_type(sbml_path=sbml_path, math_type="cmathml", tmp_path=tmp_path)


@pytest.mark.parametrize("sbml_path", [distrib_paths[0]], ids=sbml_paths_idfn)
def test_report_uncertainty_example(sbml_path: Path, tmp_path):
    """Test creation of report to check uncertainty feature"""
    check_uncertainty_info(sbml_path)


def check_uncertainty_info(sbml_path: Path):
    doc = read_sbml(
        source=sbml_path,
        promote=True,
        validate=True,
        log_errors=True,
        units_consistency=True,
        modeling_practice=True,
    )
    model = doc.getModel()
    if model is not None:
        model_info = sbmlinfo.SBMLModelInfo(doc=doc, model=model, math_render="cmathml")
    else:
        # no model exists
        logging.error(f"No model in SBML file when creating model report: {doc}")

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

    uncert_params = first_uncertainty["uncert_params"]
    assert isinstance(uncert_params, List)

    first_uncert_param = uncert_params[0]
    assert first_uncert_param["param_value"] == 5.0
    assert first_uncert_param["param_units"] == "mole"
    assert first_uncert_param["param_type"] == "mean"
