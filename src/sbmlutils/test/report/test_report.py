"""Test SBML report."""
from pathlib import Path

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import ALL_SBML_PATHS, GLUCOSE_SBML, GZ_SBML, sbml_paths_idfn


def check_report(sbml_path: Path, tmp_path: Path, validate: bool) -> None:
    """Check report creation for given SBML."""
    sbmlreport.create_report(
        sbml_path=sbml_path,
    )


@pytest.mark.parametrize("sbml_path", [GZ_SBML], ids=sbml_paths_idfn)
def test_report_gz(sbml_path: Path, tmp_path: Path) -> None:
    """Test report generation for compressed models."""
    check_report(sbml_path=sbml_path, tmp_path=tmp_path, validate=False)


@pytest.mark.parametrize("sbml_path", ALL_SBML_PATHS, ids=sbml_paths_idfn)
def test_report(sbml_path: Path, tmp_path: Path) -> None:
    """Test creation of report with Latex Math."""
    check_report(sbml_path=sbml_path, tmp_path=tmp_path, validate=False)
