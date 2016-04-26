"""
Test interpolation
"""
from __future__ import print_function, division
import unittest
import tempfile

import pandas as pd
from pandas import DataFrame
from sbmlutils.interpolation import *


class InterpolationTestCase(unittest.TestCase):
    def setUp(self):
        x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
        self.data = DataFrame(data=(x, y), columns=('x', 'y'))

    def test_linear_interpolation(self):
        """ Linear interpolation of data points. """
        interpolation = Interpolation(self.data, INTERPOLATION_LINEAR)
        tmp_f = tempfile.NamedTemporaryFile()
        interpolation.createSBML(tmp_f)

        # simulate

        # check that the data points are identical in simulation
        # and the interpolation
        print(self.data)
        self.assertEqual(1, 0)

    def test_cubic_spline_interpolation(self):
        """ Cubic spline interpolation of data points. """
        interpolation = Interpolation(self.data, INTERPOLATION_CUBIC_SPLINE)
        tmp_f = tempfile.NamedTemporaryFile()
        interpolation.createSBML(tmp_f)

        # simulate

        # check that the data points are identical in simulation
        # and the interpolation
        print(self.data)
        self.assertEqual(1, 0)

if __name__ == '__main__':
    unittest.main()
