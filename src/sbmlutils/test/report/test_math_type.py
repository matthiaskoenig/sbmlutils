"""
Test SBML Report for Math rendering in Latex and PMathML
"""
from os import path

import pytest

from sbmlutils.report import sbmlreport
from sbmlutils.test import REPRESSILATOR_SBML


@pytest.mark.parametrize("source", [REPRESSILATOR_SBML])
def test_report_latex(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path, math_type="latex")

    basename = source.name
    name = ".".join(basename.split(".")[:-1])

    # check HTML report created
    path_html = tmp_path / f"{name}.html"
    assert path.exists(path_html)

    # check XML report created
    path_xml = tmp_path / f"{name}.xml"
    assert path.exists(path_xml)


@pytest.mark.parametrize("source", [REPRESSILATOR_SBML])
def test_report_cmathml(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path, math_type="cmathml")

    basename = source.name
    name = ".".join(basename.split(".")[:-1])

    # check HTML report created
    path_html = tmp_path / f"{name}.html"
    assert path.exists(path_html)

    # check XML report created
    path_xml = tmp_path / f"{name}.xml"
    assert path.exists(path_xml)


@pytest.mark.parametrize("source", [REPRESSILATOR_SBML])
def test_report_pmathml(source, tmp_path):
    sbmlreport.create_report(sbml_path=source, output_dir=tmp_path, math_type="pmathml")

    basename = source.name
    name = ".".join(basename.split(".")[:-1])

    # check HTML report created
    path_html = tmp_path / f"{name}.html"
    assert path.exists(path_html)

    # check XML report created
    path_xml = tmp_path / f"{name}.xml"
    assert path.exists(path_xml)
