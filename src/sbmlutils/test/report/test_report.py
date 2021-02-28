"""Test SBML report."""
from pathlib import Path

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import ALL_SBML_PATHS, GZ_SBML, sbml_paths_idfn


@pytest.mark.parametrize("sbml_path", [GZ_SBML], ids=sbml_paths_idfn)
def test_report_gz(sbml_path: Path, tmp_path: Path) -> None:
    """Test report generation for compressed models."""
    sbmlreport.create_report(sbml_path=sbml_path, output_dir=tmp_path)


@pytest.mark.parametrize("sbml_path", ALL_SBML_PATHS, ids=sbml_paths_idfn)
def test_report_cmathml(sbml_path: Path, tmp_path: Path) -> None:
    """Test creation of report with Content MathML."""
    check_report_math_type(sbml_path=sbml_path, math_type="cmathml", tmp_path=tmp_path)


@pytest.mark.parametrize("sbml_path", ALL_SBML_PATHS, ids=sbml_paths_idfn)
def test_report_pmathml(sbml_path: Path, tmp_path: Path) -> None:
    """Test creation of report with Presentation MathML."""
    check_report_math_type(sbml_path=sbml_path, math_type="pmathml", tmp_path=tmp_path)


@pytest.mark.parametrize("sbml_path", ALL_SBML_PATHS, ids=sbml_paths_idfn)
def test_report_latex(sbml_path: Path, tmp_path: Path) -> None:
    """Test creation of report with Latex Math."""
    check_report_math_type(sbml_path=sbml_path, math_type="latex", tmp_path=tmp_path)


def check_report_math_type(sbml_path: Path, math_type: str, tmp_path: Path) -> None:
    """Checks SBML report with given math type."""
    html = sbmlreport.create_report(
        sbml_path=sbml_path, output_dir=tmp_path, math_type=math_type
    )

    # check the returned HTML in the variable for correctness of type
    assert html
    assert isinstance(html, str)
