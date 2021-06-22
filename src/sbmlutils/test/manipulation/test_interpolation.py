"""Test interpolation."""
from pathlib import Path

import pandas as pd
import pytest
import roadrunner

from sbmlutils.manipulation import interpolation as ip
from sbmlutils.manipulation.interpolation_example import interpolation_example


x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
z = [10.0, 5.0, 2.5, 1.25, 0.6, 0.3]
data1 = pd.DataFrame({"x": x, "y": y, "z": z})


def f_interpolation(method: str, tmp_path: Path) -> None:
    """Helper function to test the various interpolations."""

    tmp_f = tmp_path / "test.xml"
    interpolation = ip.Interpolation(data=data1, method=method)
    interpolation.write_sbml_to_file(tmp_f)
    assert tmp_f.exists()
    assert tmp_f.is_file()

    r = roadrunner.RoadRunner(str(tmp_f))
    r.timeCourseSelections = ["time", "y", "z"]
    s = r.simulate(0, 5, steps=5)
    for k in range(len(data1)):
        # all interpolations must go through the datapoints
        assert s["y"][k] == pytest.approx(data1["y"][k])
        assert s["z"][k] == pytest.approx(data1["z"][k])


@pytest.mark.parametrize(
    "method",
    [ip.INTERPOLATION_CONSTANT, ip.INTERPOLATION_LINEAR, ip.INTERPOLATION_CUBIC_SPLINE],
)
def test_interpolation(method: str, tmp_path: Path) -> None:
    """Constant interpolation of data points."""
    f_interpolation(method=method, tmp_path=tmp_path)


def test_example() -> None:
    """Test the interpolation example."""
    interpolation_example()
