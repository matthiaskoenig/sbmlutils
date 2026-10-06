"""Test interpolation."""

import math
from pathlib import Path

import libsbml
import numpy as np
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
    with pytest.raises(ValueError, match="quadratic"):
        ip.Interpolator(x=x_ser, y=y_ser, method="quadratic")
    with pytest.raises(ValueError, match="quadratic"):
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


@pytest.mark.parametrize("method", ["constant", "linear", "cubic spline"])
def test_interpolation_model_id_is_valid(method: str) -> None:
    """The model id is a valid SId for every method."""
    interpolation = ip.Interpolation(data=data1, method=method)
    sbml_str = interpolation.write_sbml_to_string()
    assert sbml_str is not None
    doc = libsbml.readSBMLFromString(sbml_str)
    assert doc.getModel().getId() == "Interpolation_" + method.replace(" ", "_")


METHODS = [
    ip.INTERPOLATION_CONSTANT,
    ip.INTERPOLATION_LINEAR,
    ip.INTERPOLATION_CUBIC_SPLINE,
]


def _piecewise(*args: float | bool) -> float:
    """Evaluate the arguments of an SBML `piecewise` in python."""
    for k in range(0, len(args) - 1, 2):
        if args[k + 1]:
            return float(args[k])
    return float(args[-1])


def _evaluate(interpolator: ip.Interpolator, value: float) -> float:
    """Evaluate the formula of an interpolator at a value of x."""
    expression = interpolator.formula().replace("^", "**")
    return float(
        eval(expression, {"piecewise": _piecewise, interpolator.xid: value})  # noqa: S307
    )


@pytest.mark.parametrize("method", METHODS)
def test_formula_through_data_points(method: str) -> None:
    """Every method goes through the data points."""
    interpolator = ip.Interpolator(x=data1["time"], y=data1["y"], method=method)
    for xk, yk in zip(data1["time"], data1["y"], strict=True):
        assert _evaluate(interpolator, xk) == pytest.approx(yk)


@pytest.mark.parametrize("method", METHODS)
def test_formula_holds_end_values(method: str) -> None:
    """Before the data the first value, after it the last value."""
    interpolator = ip.Interpolator(x=data1["time"], y=data1["z"], method=method)
    assert _evaluate(interpolator, -1.0) == pytest.approx(10.0)
    assert _evaluate(interpolator, 5.0) == pytest.approx(0.3)
    assert _evaluate(interpolator, 100.0) == pytest.approx(0.3)


def test_formula_between_points() -> None:
    """Constant takes the previous point, linear the straight line."""
    x_ser = pd.Series([0.0, 2.0, 4.0], name="time")
    y_ser = pd.Series([1.0, 3.0, 2.0], name="y")
    constant = ip.Interpolator(x=x_ser, y=y_ser, method="constant")
    linear = ip.Interpolator(x=x_ser, y=y_ser, method="linear")
    assert _evaluate(constant, 1.0) == pytest.approx(1.0)
    assert _evaluate(constant, 3.0) == pytest.approx(3.0)
    assert _evaluate(linear, 1.0) == pytest.approx(2.0)
    assert _evaluate(linear, 3.0) == pytest.approx(2.5)


def test_ast_holds_numbers_exactly() -> None:
    """The AST holds the numbers of the data exactly, `time` is the csymbol."""
    x_ser = pd.Series([0.0, 1.0 / 3.0], name="time")
    y_ser = pd.Series([0.1 + 0.2, -2.5e-12], name="y")
    ast = ip.Interpolator(x=x_ser, y=y_ser, method="constant").ast()
    assert ast.getType() == libsbml.AST_FUNCTION_PIECEWISE
    assert ast.getChild(0).getValue() == 0.1 + 0.2
    assert ast.getChild(1).getChild(0).getType() == libsbml.AST_NAME_TIME
    assert ast.getChild(1).getChild(1).getValue() == 1.0 / 3.0
    assert ast.getChild(2).getValue() == -2.5e-12


@pytest.mark.parametrize(
    ("x_values", "y_values", "method", "match"),
    [
        ([0.0], [1.0], "linear", "at least 2 data points"),
        ([0.0, 1.0], [1.0, 2.0], "cubic spline", "at least 3 data points"),
        ([0.0, 1.0, 1.0], [1.0, 2.0, 3.0], "linear", "strictly increasing"),
        ([0.0, 1.0, 2.0], [1.0, math.nan, 3.0], "linear", "missing or infinite"),
        ([0.0, 1.0, 2.0], [1.0, np.inf, 3.0], "linear", "missing or infinite"),
        ([0.0, 1.0, 2.0], ["mM", "1.0", "2.0"], "linear", "not numeric"),
    ],
)
def test_invalid_series_raise(
    x_values: list[float], y_values: list[object], method: str, match: str
) -> None:
    """An interpolator refuses series it cannot interpolate."""
    with pytest.raises(ValueError, match=match):
        ip.Interpolator(
            x=pd.Series(x_values, name="time"),
            y=pd.Series(y_values, name="y"),
            method=method,
        )
