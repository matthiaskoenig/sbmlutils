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

    def xpp_check(self, ode_id):
        tmp_dir = tempfile.mkdtemp(suffix="_xpp")
        sbml_file = os.path.join(tmp_dir, "{}.xml".format(ode_id))
        xpp_file = os.path.join(xpp_dir, "{}.ode".format(ode_id))

        xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
        Nall, Nerr, Nwarn = validation.check_sbml(sbml_file, ucheck=False)
        assert Nall == 0
        assert Nerr == 0
        assert Nwarn == 0

    def test_PLoSCompBiol_Fig1(self):
        self.xpp_check(ode_id="PLoSCompBiol_Fig1")



if __name__ == "__main__":
    unittest.main()



