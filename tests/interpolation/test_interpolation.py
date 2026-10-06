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


@pytest.mark.parametrize(
    ("data", "match"),
    [
        (pd.DataFrame({"time": [0.0, 1.0, 2.0]}), "at least 2 columns"),
        (pd.DataFrame({"t [h]": [0.0, 1.0], "y": [1.0, 2.0]}), "SBML id"),
        (pd.DataFrame({0: [0.0, 1.0], 1: [1.0, 2.0]}), "column names"),
        (
            pd.DataFrame([[0.0, 1.0], [1.0, 2.0]], columns=pd.Index(["time", "time"])),
            "twice",
        ),
        (pd.DataFrame({"time": [0.0, 1.0, 1.0], "y": [1.0, 2.0, 3.0]}), "strictly"),
        (pd.DataFrame({"time": [0.0, 1.0, 2.0], "y": [1.0, None, 3.0]}), "missing"),
        (
            pd.DataFrame({"time": ["h", "0.0", "1.0"], "y": ["mM", "1.0", "2.0"]}),
            "not numeric",
        ),
    ],
)
def test_invalid_data_raises(data: pd.DataFrame, match: str) -> None:
    """Data which cannot be interpolated is refused when it is given."""
    with pytest.raises(ValueError, match=match):
        ip.Interpolation(data=data, method="linear")


def test_interpolators_property() -> None:
    """One interpolator per column after the first, in column order."""
    interpolation = ip.Interpolation(data=data1, method="linear")
    assert interpolation.xid == "time"
    assert [i.yid for i in interpolation.interpolators] == ["y", "z"]
    assert all(i.xid == "time" for i in interpolation.interpolators)


def test_unsorted_data_is_sorted_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Data which is not ascending in x is sorted, with a warning."""
    data = data1.iloc[::-1]
    interpolation = ip.Interpolation(data=data, method="linear")
    assert list(interpolation.data["time"]) == x
    assert "ascending" in caplog.text


def _standalone(method: str, data: pd.DataFrame = data1) -> libsbml.Model:
    """The model of the standalone SBML of an interpolation."""
    sbml = ip.Interpolation(data=data, method=method).write_sbml_to_string()
    assert sbml is not None
    doc = libsbml.readSBMLFromString(sbml)
    assert doc.getNumErrors(libsbml.LIBSBML_SEV_ERROR) == 0
    return doc.getModel()


@pytest.mark.parametrize("method", METHODS)
def test_standalone_model(method: str) -> None:
    """L3V2, a non constant parameter with a port per column, a rule each."""
    model = _standalone(method)
    assert (model.getLevel(), model.getVersion()) == (3, 2)
    ports = {p.getIdRef() for p in model.getPlugin("comp").getListOfPorts()}
    assert ports == {"y", "z"}
    for sid in ("y", "z"):
        assert not model.getParameter(sid).getConstant()
        assert model.getAssignmentRuleByVariable(sid) is not None
    assert "sbmlutils" in model.getNotesString()
    assert "Copyright" not in model.getNotesString()


def test_standalone_model_with_x_quantity() -> None:
    """A quantity as x is a parameter with a port, which a parent replaces."""
    data = data1.rename(columns={"time": "glc"})
    model = _standalone("linear", data)
    x_parameter = model.getParameter("glc")
    assert x_parameter.getValue() == 0.0
    ports = {p.getIdRef() for p in model.getPlugin("comp").getListOfPorts()}
    assert ports == {"glc", "y", "z"}


def test_standalone_column_not_sid_raises() -> None:
    """A column whose name is used as an id has to be an SBML id."""
    data = data1.rename(columns={"y": "y [mM]"})
    with pytest.raises(ValueError, match="'y \\[mM\\]' is not an SBML id"):
        ip.Interpolation(data=data).write_sbml_to_string()


@pytest.mark.parametrize("method", METHODS)
def test_standalone_holds_end_values(method: str) -> None:
    """Simulated beyond the data, the last value is held."""
    roadrunner = pytest.importorskip("roadrunner")
    sbml = ip.Interpolation(data=data1, method=method).write_sbml_to_string()
    r = roadrunner.RoadRunner(sbml)
    s = r.simulate(0, 10, 11, selections=["time", "y", "z"])
    assert s["y"][-1] == pytest.approx(3.5)
    assert s["z"][-1] == pytest.approx(0.3)


def test_add_interpolator_to_model_is_removed() -> None:
    """The function which deleted a parameter of the same id is gone."""
    assert not hasattr(ip.Interpolation, "add_interpolator_to_model")
    assert not hasattr(ip.Interpolation, "create_interpolators")


def test_mixed_type_x_raises(caplog: pytest.LogCaptureFixture) -> None:
    """A first column with text is refused as not numeric, before it is sorted."""
    for x_values in (["min", 0.0, 1.0], ["min", "0.0", "1.0"]):
        data = pd.DataFrame({"time": x_values, "y": [0.0, 1.0, 2.0]})
        with pytest.raises(ValueError, match="'time' is not numeric"):
            ip.Interpolation(data=data, method="linear")
    assert "sorted" not in caplog.text
