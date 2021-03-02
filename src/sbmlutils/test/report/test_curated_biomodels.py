"""Test SBML report."""
from pathlib import Path

import pytest

from sbmlutils.test import BIOMODELS_CURATED_PATH

from . import test_report


sbml_paths = [
    BIOMODELS_CURATED_PATH / f"BIOMD0000000{k:0>3}.xml.gz"
    for k in range(1, 988)
    if k not in [649, 694, 923]
]


@pytest.mark.parametrize("sbml_path", sbml_paths, ids=test_report.sbml_paths_idfn)
def test_report_latex(sbml_path: Path, tmp_path: Path) -> None:
    """Test report generation for GZ reports with Latex rendering"""
    test_report.check_report_math_type(
        sbml_path=sbml_path, math_type="latex", tmp_path=tmp_path, validate=False
    )
