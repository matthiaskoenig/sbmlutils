"""
Test interpolation
"""
import os
import shutil
import tempfile

import pandas as pd
import pytest
import roadrunner

from sbmlutils.manipulation import interpolation as ip


x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
z = [10.0, 5.0, 2.5, 1.25, 0.6, 0.3]
data1 = pd.DataFrame({"x": x, "y": y, "z": z})


def f_interpolation(method):
    """ Helper function to test the various interpolations. """
    temp_dir = tempfile.mkdtemp()
    try:
        tmp_f = os.path.join(temp_dir, "test.xml")

        interpolation = ip.Interpolation(data=data1, method=method)
        interpolation.write_sbml_to_file(tmp_f)
        assert os.path.isfile(tmp_f)

        r = roadrunner.RoadRunner(tmp_f)
        r.timeCourseSelections = ["time", "y", "z"]
        s = r.simulate(0, 5, steps=5)
        for k in range(len(data1)):
            # all interpolations must go through the datapoints
            assert s["y"][k] == pytest.approx(data1["y"][k])
            assert s["z"][k] == pytest.approx(data1["z"][k])

    finally:
        shutil.rmtree(temp_dir)


def test_constant_interpolation():
    """ Constant interpolation of data points. """
    f_interpolation(method=ip.INTERPOLATION_CONSTANT)


def test_linear_interpolation():
    """ Linear interpolation of data points. """
    f_interpolation(method=ip.INTERPOLATION_LINEAR)


def test_cubic_interpolation():
    """ Natural cubic spline interpolation of data points. """
    f_interpolation(method=ip.INTERPOLATION_CUBIC_SPLINE)
