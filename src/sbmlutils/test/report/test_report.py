"""Test SBML report."""
from pathlib import Path

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import (
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    REPRESSILATOR_SBML,
    UNCERTAINTY_PATH,
    VDP_SBML,
)


uncertainty_paths = [
    UNCERTAINTY_PATH / f"00{i:0>3}-sbml-l3v1.xml"
    for i in (
        [i for i in range(40, 48)]
        + [49, 50, 51, 52, 56, 65, 69]
        + [i for i in range(69, 104)]
    )
] + [
    UNCERTAINTY_PATH / f"00{i:0>3}-sbml-l3v2.xml"
    for i in (
        [i for i in range(40, 48)]
        + [49, 50, 51, 52, 56, 65, 69]
        + [i for i in range(69, 104)]
    )
]

sbml_paths = [
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    REPRESSILATOR_SBML,
    VDP_SBML,
]


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


@pytest.mark.parametrize("sbml_path", uncertainty_paths, ids=sbml_paths_idfn)
def test_report_uncertainty(sbml_path: Path, tmp_path):
    """Test creation of report with Presentation MathML."""
    check_report_math_type(sbml_path=sbml_path, math_type="cmathml", tmp_path=tmp_path)
