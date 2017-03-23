"""
Test interpolation
"""
from __future__ import print_function, division, absolute_import

import os
import shutil
import unittest
import tempfile
import pandas as pd
import roadrunner

from sbmlutils import interpolation as ip


class InterpolationTestCase(unittest.TestCase):
    """ Unit tests for the interpolation functions. """
    def setUp(self):
        # test data1
        x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
        z = [10.0, 5.0, 2.5, 1.25, 0.6, 0.3]
        self.data1 = pd.DataFrame({'x': x, 'y': y, 'z': z})

    def interpolation(self, method):
        """ Helper function to test the various interpolations. """
        temp_dir = tempfile.mkdtemp()
        try:
            tmp_f = os.path.join(temp_dir, 'test.xml')

            interpolation = ip.Interpolation(data=self.data1, method=method)
            interpolation.write_sbml_to_file(tmp_f)
            self.assertTrue(os.path.isfile(tmp_f))

            r = roadrunner.RoadRunner(tmp_f)
            r.timeCourseSelections = ['time', 'y', 'z']
            s = r.simulate(0, 5, steps=5)
            for k in range(len(self.data1)):
                # all interpolations must go through the datapoints
                self.assertAlmostEqual(s['y'][k], self.data1['y'][k])
                self.assertAlmostEqual(s['z'][k], self.data1['z'][k])

        finally:
            shutil.rmtree(temp_dir)

    def test_constant_interpolation(self):
        """ Constant interpolation of data points. """
        self.interpolation(method=ip.INTERPOLATION_CONSTANT)

    def test_linear_interpolation(self):
        """ Linear interpolation of data points. """
        self.interpolation(method=ip.INTERPOLATION_LINEAR)

    def test_cubic_interpolation(self):
        """ Natural cubic spline interpolation of data points. """
        self.interpolation(method=ip.INTERPOLATION_CUBIC_SPLINE)


if __name__ == '__main__':
    unittest.main()
