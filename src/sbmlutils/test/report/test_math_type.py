"""
Test SBML Report for Math rendering in Latex, CMathML and PMathML
"""
from os import path

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import (
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    GLUCOSE_SBML,
    GZ_SBML,
    REPRESSILATOR_SBML,
    VDP_SBML,
)


@pytest.mark.parametrize(
    "source",
    [
        BASIC_SBML,
        DEMO_SBML,
        GALACTOSE_SINGLECELL_SBML,
        GLUCOSE_SBML,
        GZ_SBML,
        VDP_SBML,
        REPRESSILATOR_SBML,
    ],
)
def test_report_latex(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path, math_type="latex")

    basename = source.name
    name = ".".join(basename.split(".")[:-1])

    # check HTML report created
    path_html = tmp_path / f"{name}.html"
    assert path.exists(path_html)

    # check source doc created
    path_source = tmp_path / f"{source.name}"
    assert path.exists(path_source)


@pytest.mark.parametrize(
    "source",
    [
        BASIC_SBML,
        DEMO_SBML,
        GALACTOSE_SINGLECELL_SBML,
        GLUCOSE_SBML,
        GZ_SBML,
        VDP_SBML,
        REPRESSILATOR_SBML,
    ],
)
def test_report_cmathml(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path, math_type="cmathml")

    basename = source.name
    name = ".".join(basename.split(".")[:-1])

    # check HTML report created
    path_html = tmp_path / f"{name}.html"
    assert path.exists(path_html)

    # check source doc created
    path_source = tmp_path / f"{source.name}"
    assert path.exists(path_source)


@pytest.mark.parametrize(
    "source",
    [
        BASIC_SBML,
        DEMO_SBML,
        GALACTOSE_SINGLECELL_SBML,
        GLUCOSE_SBML,
        GZ_SBML,
        VDP_SBML,
        REPRESSILATOR_SBML,
    ],
)
def test_report_pmathml(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path, math_type="pmathml")

    basename = source.name
    name = ".".join(basename.split(".")[:-1])

    # check HTML report created
    path_html = tmp_path / f"{name}.html"
    assert path.exists(path_html)

    # check source doc created
    path_source = tmp_path / f"{source.name}"
    assert path.exists(path_source)
