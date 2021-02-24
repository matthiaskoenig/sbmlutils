"""Test SBML report."""
from pathlib import Path

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import DISTRIB_PATHS as distrib_paths
from sbmlutils.test import GZ_SBML, REPRESSILATOR_SBML
from sbmlutils.test import SBML_PATHS as sbml_paths
from sbmlutils.test import UNCERTAINTY_MODEL_PATHS as uncertainty_model_paths


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
