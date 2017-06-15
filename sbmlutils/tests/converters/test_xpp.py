"""
Test XPP generation
"""
from __future__ import absolute_import, print_function

import tempfile
import unittest
import os

from sbmlutils.converters import xpp
from sbmlutils.tests import data
from sbmlutils import validation


xpp_dir = os.path.join(data.data_dir, 'xpp')

class XPPTestCase(unittest.TestCase):

    def xpp_check(self, ode_id, Nall=0, Nerr=0, Nwarn=0):
        tmp_dir = tempfile.mkdtemp(suffix="_xpp")
        sbml_file = os.path.join(tmp_dir, "{}.xml".format(ode_id))
        xpp_file = os.path.join(xpp_dir, "{}.ode".format(ode_id))

        xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
        Nall_res, Nerr_res, Nwarn_res = validation.check_sbml(sbml_file, ucheck=False)
        assert Nall_res == Nall
        assert Nerr_res == Nerr
        assert Nwarn_res == Nwarn

    def test_PLoSCompBiol_Fig1(self):
        self.xpp_check(ode_id="PLoSCompBiol_Fig1")

    def test_SkM_AP_KCa(self):
        self.xpp_check(ode_id="SkM_AP_KCa")


if __name__ == "__main__":
    unittest.main()



