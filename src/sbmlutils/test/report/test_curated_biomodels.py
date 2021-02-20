"""Test SBML report."""
import shutil
from pathlib import Path

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import BIOMODELS_CURATED_PATH

from . import test_report


sbml_paths = [
    BIOMODELS_CURATED_PATH / f"BIOMD0000000{k:0>3}.xml.gz" for k in range(1, 988)
] - [
    BIOMODELS_CURATED_PATH / f"BIOMD0000000649.xml.gz",
    BIOMODELS_CURATED_PATH / f"BIOMD0000000694.xml.gz",
    BIOMODELS_CURATED_PATH / f"BIOMD0000000923.xml.gz",
]


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=test_report.sbml_paths_idfn)
def test_report_latex(sbml_path, tmp_path):
    """Test report generation for GZ reports with Latex rendering"""
    test_report.check_report_math_type(
        sbml_path=sbml_path, math_type="latex", tmp_path=tmp_path
    )


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=test_report.sbml_paths_idfn)
def test_report_cmathml(sbml_path: Path, tmp_path):
    """Test report generation for GZ reports with Content MathML rendering"""
    test_report.check_report_math_type(
        sbml_path=sbml_path, math_type="cmathml", tmp_path=tmp_path
    )


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=test_report.sbml_paths_idfn)
def test_report_pmathml(sbml_path: Path, tmp_path):
    """Test report generation for GZ reports with Presentation MathML rendering"""
    test_report.check_report_math_type(
        sbml_path=sbml_path, math_type="cmathml", tmp_path=tmp_path
    )
