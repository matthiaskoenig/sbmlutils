"""
Test SBML report.
"""
import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import (
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    VDP_SBML,
)


@pytest.mark.parametrize(
    "source", [DEMO_SBML, GALACTOSE_SINGLECELL_SBML, GLUCOSE_SBML, BASIC_SBML, VDP_SBML]
)
def test_report(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path)


@pytest.mark.parametrize("source", [GZ_SBML])
def test_report_gz(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path)
