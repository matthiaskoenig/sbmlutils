"""
Test the SBML report.
"""
from __future__ import print_function, division
import unittest

import tempfile
from sbmlutils.test import data
from sbmlutils.report import sbmlreport

class MyTestCase(unittest.TestCase):

    def test_demo_report(self):
        tmpdir = tempfile.mkdtemp(suffix="_sbml_report")
        sbmlreport.create_sbml_report(data.DEMO_SBML, tmpdir)

    def test_galactose_report(self):
        tmpdir = tempfile.mkdtemp(suffix="_sbml_report")
        sbmlreport.create_sbml_report(data.GALACTOSE_SINGLECELL_SBML, tmpdir)

    def test_glucose_report(self):
        tmpdir = tempfile.mkdtemp(suffix="_sbml_report")
        sbmlreport.create_sbml_report(data.GLUCOSE_SBML, tmpdir)

    def test_test_report(self):
        tmpdir = tempfile.mkdtemp(suffix="_sbml_report")
        sbmlreport.create_sbml_report(data.BASIC_SBML, tmpdir)

    def test_vdp_report(self):
        tmpdir = tempfile.mkdtemp(suffix="_sbml_report")
        sbmlreport.create_sbml_report(data.VDP_SBML, tmpdir)

if __name__ == '__main__':
    unittest.main()
