"""Test interpolation."""

from pathlib import Path

import pandas as pd
import pytest

from sbmlutils.data import interpolation as ip

x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
z = [10.0, 5.0, 2.5, 1.25, 0.6, 0.3]
data1 = pd.DataFrame({"time": x, "y": y, "z": z})


def f_interpolation(method: str, tmp_path: Path) -> None:
    """Create different interpolations."""
    roadrunner = pytest.importorskip("roadrunner")
    tmp_f = tmp_path / "tests.xml"
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


def test_method_given_as_equal_string() -> None:
    """A method string which is not the identical object of the constant works."""
    x_ser = pd.Series([0.0, 1.0, 2.0], name="time")
    y_ser = pd.Series([0.0, 1.0, 0.0], name="y")
    method = "".join(["cubic", " ", "spline"])
    assert method is not ip.INTERPOLATION_CUBIC_SPLINE
    assert (
        ip.Interpolator(x=x_ser, y=y_ser, method=method)
        .formula()
        .startswith("piecewise(")
    )


def test_unknown_method_raises() -> None:
    """An unknown method is rejected on construction."""
    x_ser = pd.Series([0.0, 1.0, 2.0], name="time")
    y_ser = pd.Series([0.0, 1.0, 0.0], name="y")
    with pytest.raises(ValueError):
        ip.Interpolator(x=x_ser, y=y_ser, method="quadratic")
    with pytest.raises(ValueError):
        ip.Interpolation(data=pd.DataFrame({"time": x, "y": y}), method="quadratic")


def test_natural_spline_coefficients() -> None:
    """Coefficients match the natural spline through (0,0), (1,1), (2,0) by hand.

    Segment 0: a=0, b=1.5, c=0, d=-0.5. Segment 1: a=1, b=0, c=-1.5, d=0.5.
    """
    x_ser = pd.Series([0.0, 1.0, 2.0], name="time")
    y_ser = pd.Series([0.0, 1.0, 0.0], name="y")
    coeffs = ip.Interpolator._natural_spline_coeffs(x_ser, y_ser)
    assert coeffs == [
        pytest.approx((0.0, 1.5, 0.0, -0.5)),
        pytest.approx((1.0, 0.0, -1.5, 0.5)),
    ]


@pytest.mark.parametrize(
    "method",
    [ip.INTERPOLATION_CONSTANT, ip.INTERPOLATION_LINEAR, ip.INTERPOLATION_CUBIC_SPLINE],
)
def test_unsorted_data_equals_sorted_data(method: str) -> None:
    """Shuffled rows give the same SBML as sorted rows."""
    order = [3, 0, 5, 1, 4, 2]
    # fresh index labels, so that they do not follow the order of x after sorting
    shuffled = pd.DataFrame(
        {col: [data1[col][k] for k in order] for col in data1.columns}
    )
    sorted_sbml = ip.Interpolation(data=data1, method=method).write_sbml_to_string()
    shuffled_sbml = ip.Interpolation(
        data=shuffled, method=method
    ).write_sbml_to_string()
    assert sorted_sbml == shuffled_sbml


def test_example() -> None:
    """Test the interpolation example."""
    pytest.importorskip("roadrunner")
    from matplotlib import pyplot as plt

    from examples.interpolation.interpolation import interpolation_example

    figure = interpolation_example()
    assert figure
    plt.close(figure)
