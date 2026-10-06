# Driving models with data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drive an existing SBML model with interpolated data, in place (`Interpolation.drive`), through a comp model which leaves the original untouched (`Interpolation.drive_comp`) and in a python model definition (`Interpolation.assignment_rules`), with the guide and examples of #16.

**Architecture:** `sbmlutils/data/interpolation.py` keeps the public API (`InterpolationMethod`, `Interpolator`, `Interpolation`); the formulas hold the end values outside the data and are parsed once into a libsbml AST. A new private module `sbmlutils/data/_driving.py` holds the checks of the targets and the writing of the rules, in place and as a comp document; `Interpolation` delegates to it. The standalone model is written through the factory.

**Tech Stack:** python >= 3.12, libsbml (comp package), pandas, numpy, the factory of sbmlutils, roadrunner in the tests and examples only.

**Spec:** `docs/superpowers/specs/2026-10-06-interpolation-driving-design.md`

## Global Constraints

- The package never simulates: roadrunner and matplotlib are imported by tests (with `pytest.importorskip("roadrunner")`) and examples only.
- Every module, class and function has full type annotations and a google style docstring; ty must stay at zero diagnostics (`uvx ty check`), ruff clean (`ruff check`, `ruff format`).
- libsbml calls which return a status are wrapped in `check(...)` of `sbmlutils.validation`; libsbml objects are annotated explicitly and read through getters.
- Library code logs with `logging.getLogger(__name__)` and lazy `%s` formatting, it never prints.
- A user error raises a `ValueError` whose message names the column, element or id at fault.
- Outside the data every method holds the first value before it and the last value after it.
- The data is in the units of what it drives; nothing is converted.
- The comp document references the original by an `ExternalModelDefinition` by default, `embed=True` copies it in; the original file is never modified.
- Never use the em dash character; markdown has no hard line wraps.
- Commits without any attribution lines.
- Run tests quietly: `.venv/bin/pytest -q -x <path>`.

## Review Focus

- A table read from a csv without a header has integer column names: a `ValueError` naming the column, never a crash inside libsbml (test in Task 2).
- A column with text (e.g. a row of units under the header) is not numeric: a `ValueError` naming the column (test in Task 1 and Task 2).
- Two columns mapped to the same target: a `ValueError` naming both columns, never two assignment rules on one element (test in Task 4).
- A species target in a compartment which is itself a target: the comp document is valid and simulates as in place (test in Task 5).
- `drive` applied twice to the same document: the second call raises naming the existing assignment rule and leaves the document unchanged (test in Task 4).

---

## File Structure

- Modify `src/sbmlutils/data/interpolation.py`: formulas with held end values and exact numbers (`Interpolator.formula`, `Interpolator.ast`), data checks raising `ValueError`, `Interpolation.interpolators` property, the standalone model through the factory, the methods `drive`, `drive_comp`, `assignment_rules`. Removes `add_interpolator_to_model`, `create_interpolators`, `_init_sbml_model`, the module level `notes`.
- Create `src/sbmlutils/data/_driving.py`: `resolve_targets`, `check_sid`, `write_interpolation`, `drive`, `drive_comp` and their private helpers.
- Modify `tests/interpolation/test_interpolation.py`: formulas, data checks, standalone model.
- Create `tests/interpolation/test_drive.py`: in place.
- Create `tests/interpolation/test_drive_comp.py`: comp, equivalence with in place.
- Create `tests/interpolation/test_assignment_rules.py`: factory.
- Create `tests/interpolation/models.py`: the test models shared by the three test modules.
- Create `tests/interpolation/test_interpolation_docs.py`: runs the python code blocks of `docs/interpolation.md`.
- Create `examples/interpolation/driving.py`, `examples/interpolation/glucose_timecourse.tsv`.
- Modify `examples/interpolation/pancreas.py`, `tests/examples/test_example_scripts.py`.
- Modify `docs/interpolation.md`, `CLAUDE.md`; create `release-notes/0.16.0.md`.

---

### Task 1: Formulas which hold the end values, exact numbers, checked series

**Files:**
- Modify: `src/sbmlutils/data/interpolation.py` (class `Interpolator`, new module functions `_number`, `_piecewise`, `_check_series`)
- Test: `tests/interpolation/test_interpolation.py`

**Interfaces:**
- Produces: `Interpolator(x: pd.Series, y: pd.Series, method: InterpolationMethod | str = InterpolationMethod.CONSTANT)` raising `ValueError` for invalid series; `Interpolator.formula() -> str` (L3 formula, numbers as `repr` of floats); `Interpolator.ast() -> libsbml.ASTNode`; `Interpolator.xid -> str`, `Interpolator.yid -> str`; `Interpolator._natural_spline_coeffs(X, Y) -> list[tuple[float, float, float, float]]` (unchanged).

- [ ] **Step 1: Write the failing tests**

Append to `tests/interpolation/test_interpolation.py` (add `import math` and `import numpy as np` to the imports):

```python
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
    "x_values, y_values, method, match",
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest -q -x tests/interpolation/test_interpolation.py`
Expected: FAIL, `test_formula_holds_end_values` evaluates `0.0` after the data for linear (or `AttributeError: 'Interpolator' object has no attribute 'ast'`).

- [ ] **Step 3: Implement**

In `src/sbmlutils/data/interpolation.py` add `import numpy as np` and replace the formula code of `Interpolator`. The module functions go above the class:

```python
def _number(value: float) -> str:
    """Write a number exactly, in parentheses when it is negative.

    `repr` of a float is the shortest text which reads back as the same float,
    so the parsed formula holds the number of the data exactly.
    """
    text = repr(float(value))
    return f"({text})" if text.startswith("-") else text


def _piecewise(pieces: list[str], otherwise: float) -> str:
    """Write a `piecewise` of `value, condition` pieces and the value otherwise."""
    return f"piecewise({', '.join([*pieces, _number(otherwise)])})"


def _check_series(x: pd.Series, y: pd.Series, method: InterpolationMethod) -> None:
    """Check that `y` can be interpolated against `x` with the method.

    Raises:
        ValueError: if a series is not numeric, has a missing or an infinite
            value, has fewer data points than the method needs, or if `x` is
            not strictly increasing
    """
    min_points = 3 if method == InterpolationMethod.CUBIC_SPLINE else 2
    if len(x) != len(y):
        raise ValueError(
            f"'{x.name}' has {len(x)} values and '{y.name}' has {len(y)}, "
            f"both need one per data point."
        )
    if len(x) < min_points:
        raise ValueError(
            f"The {method} interpolation of '{y.name}' needs at least {min_points} "
            f"data points, the data has {len(x)}."
        )
    for series in (x, y):
        if not pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(
            series
        ):
            raise ValueError(f"Column '{series.name}' is not numeric.")
        if not np.isfinite(series.to_numpy(dtype=float)).all():
            raise ValueError(f"Column '{series.name}' has a missing or infinite value.")
    if not (np.diff(x.to_numpy(dtype=float)) > 0).all():
        raise ValueError(
            f"The values of '{x.name}' have to be strictly increasing, a value of "
            f"x must not repeat."
        )
```

The class (keep `__str__`, `xid`, `yid` and `_natural_spline_coeffs` as they are; replace `__init__`, `formula` and the three `_formula_*` methods):

```python
class Interpolator:
    """The interpolation of one data series `y` against `x`.

    Outside the data the first value is held before it and the last value
    after it, for every method.
    """

    def __init__(
        self,
        x: pd.Series,
        y: pd.Series,
        method: InterpolationMethod | str = InterpolationMethod.CONSTANT,
    ):
        """Initialize Interpolator.

        Args:
            x: The independent variable, strictly increasing, named as x is
                named in the model (`time` for the simulation time).
            y: The values interpolated against x.
            method: The interpolation method.

        Raises:
            ValueError: If the method is not an interpolation method or the
                series cannot be interpolated, see `_check_series`.
        """
        self.x: pd.Series = x.reset_index(drop=True)
        self.y: pd.Series = y.reset_index(drop=True)
        self.method: InterpolationMethod = InterpolationMethod(method)
        _check_series(self.x, self.y, self.method)

    def formula(self) -> str:
        """Get the formula of the interpolation as an SBML L3 formula string.

        Every number is written as the `repr` of its float, so `ast` holds it
        exactly.
        """
        match self.method:
            case InterpolationMethod.CONSTANT:
                return self._formula_constant()
            case InterpolationMethod.LINEAR:
                return self._formula_linear()
            case InterpolationMethod.CUBIC_SPLINE:
                return self._formula_cubic_spline()

    def ast(self) -> libsbml.ASTNode:
        """Get the formula as the libsbml AST the writers use.

        Raises:
            ValueError: If libsbml cannot parse the formula, which happens
                only for a name of x which is not an SBML id.
        """
        ast: libsbml.ASTNode | None = libsbml.parseL3Formula(self.formula())
        if ast is None:
            raise ValueError(
                f"The interpolation of '{self.yid}' over '{self.xid}' cannot be "
                f"written: {libsbml.getLastParseL3Error()}"
            )
        return ast

    def _formula_constant(self) -> str:
        """The value of the previous data point, the first one before the data."""
        xid = self.xid
        pieces = [
            f"{_number(self.y.iloc[k])}, {xid} < {_number(self.x.iloc[k + 1])}"
            for k in range(len(self.x) - 1)
        ]
        return _piecewise(pieces, otherwise=self.y.iloc[-1])

    def _formula_linear(self) -> str:
        """The straight line between two data points."""
        xid = self.xid
        x, y = self.x, self.y
        pieces = [f"{_number(y.iloc[0])}, {xid} < {_number(x.iloc[0])}"]
        for k in range(len(x) - 1):
            x1, x2 = float(x.iloc[k]), float(x.iloc[k + 1])
            y1, y2 = float(y.iloc[k]), float(y.iloc[k + 1])
            slope = (y2 - y1) / (x2 - x1)
            pieces.append(
                f"{_number(y1)} + {_number(slope)} * ({xid} - {_number(x1)}), "
                f"{xid} < {_number(x2)}"
            )
        return _piecewise(pieces, otherwise=y.iloc[-1])

    def _formula_cubic_spline(self) -> str:
        """The natural cubic spline through the data points."""
        xid = self.xid
        x, y = self.x, self.y
        coeffs = Interpolator._natural_spline_coeffs(x, y)
        pieces = [f"{_number(y.iloc[0])}, {xid} < {_number(x.iloc[0])}"]
        for k, (a, b, c, d) in enumerate(coeffs):
            dx = f"({xid} - {_number(x.iloc[k])})"
            pieces.append(
                f"{_number(d)} * {dx}^3 + {_number(c)} * {dx}^2 + "
                f"{_number(b)} * {dx} + {_number(a)}, {xid} < {_number(x.iloc[k + 1])}"
            )
        return _piecewise(pieces, otherwise=y.iloc[-1])
```

`Interpolation._create_sbml` and `add_interpolator_to_model` call `interpolator.formula()`, which still exists; nothing else changes in this task.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest -q -x tests/interpolation/`
Expected: PASS (the old `test_interpolation` through roadrunner passes as well).

- [ ] **Step 5: Lint, type check, commit**

```bash
.venv/bin/ruff check -q src tests && .venv/bin/ruff format -q src tests && uvx ty check
git add src/sbmlutils/data/interpolation.py tests/interpolation/test_interpolation.py
git commit -m "Interpolation formulas hold the end values outside the data, exact numbers (#16)"
```

---

### Task 2: Data checks of `Interpolation`, `interpolators` property

**Files:**
- Modify: `src/sbmlutils/data/interpolation.py` (class `Interpolation`: `__init__`, `validate_data`, `interpolators`, `from_csv`, `from_tsv`; remove `create_interpolators`)
- Modify: `examples/interpolation/pancreas.py` (the one call of `create_interpolators`)
- Test: `tests/interpolation/test_interpolation.py`

**Interfaces:**
- Consumes: `Interpolator` of Task 1.
- Produces: `Interpolation(data: pd.DataFrame, method: InterpolationMethod | str = InterpolationMethod.LINEAR)` raising `ValueError`; `Interpolation.interpolators -> list[Interpolator]` (property, one per column after the first, in column order); `Interpolation.xid -> str` (property, the name of the first column).

- [ ] **Step 1: Write the failing tests**

```python
@pytest.mark.parametrize(
    "data, match",
    [
        (pd.DataFrame({"time": [0.0, 1.0, 2.0]}), "at least 2 columns"),
        (pd.DataFrame({"t [h]": [0.0, 1.0], "y": [1.0, 2.0]}), "SBML id"),
        (pd.DataFrame({0: [0.0, 1.0], 1: [1.0, 2.0]}), "column names"),
        (pd.DataFrame([[0.0, 1.0], [1.0, 2.0]], columns=["time", "time"]), "twice"),
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest -q -x tests/interpolation/test_interpolation.py -k "invalid_data or interpolators_property or sorted_with_warning"`
Expected: FAIL (`DID NOT RAISE` for the columns check, `AttributeError: xid`).

- [ ] **Step 3: Implement**

Replace `__init__`, `validate_data`, `from_csv`, `from_tsv` and `create_interpolators` of `Interpolation`:

```python
class Interpolation:
    """The interpolation of a table of data points.

    The first column is x, every other column is interpolated against it.
    `time` as x is the simulation time, any other name the quantity of the
    model of that id.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        method: InterpolationMethod | str = InterpolationMethod.LINEAR,
    ):
        """Initialize Interpolation.

        Args:
            data: The data points, x in the first column.
            method: The interpolation method of every column.

        Raises:
            ValueError: If the method is not an interpolation method or the
                data cannot be interpolated, see `validate_data`.
        """
        self.data: pd.DataFrame = data
        self.method: InterpolationMethod = InterpolationMethod(method)
        self.validate_data()

    def validate_data(self) -> None:
        """Validate the data, and sort it by x if it is not ascending.

        Raises:
            ValueError: If the data has fewer than 2 columns, a column name
                which is not a string or which repeats, a first column whose
                name is not an SBML id, or a column which cannot be
                interpolated (see `Interpolator`).
        """
        columns = list(self.data.columns)
        if len(columns) < 2:
            raise ValueError(
                f"The data needs at least 2 columns, x and a column to "
                f"interpolate, it has {len(columns)}."
            )
        not_str = [c for c in columns if not isinstance(c, str)]
        if not_str:
            raise ValueError(
                f"The column names have to be strings, {not_str!r} are not; "
                f"read the data with its header."
            )
        repeated = sorted({c for c in columns if columns.count(c) > 1})
        if repeated:
            raise ValueError(f"The columns {repeated!r} are in the data twice.")
        if not libsbml.SyntaxChecker.isValidSBMLSId(self.xid):
            raise ValueError(
                f"The first column is x and names it in the model, '{self.xid}' "
                f"is not an SBML id."
            )
        x = self.data[self.xid]
        if not pd.Index(x).is_monotonic_increasing:
            logger.warning(
                "The data is sorted by its first column '%s', which is not ascending.",
                self.xid,
            )
            self.data = self.data.sort_values(by=self.xid).reset_index(drop=True)
        # the interpolators check every column
        self.interpolators  # noqa: B018

    @property
    def xid(self) -> str:
        """The name of x, the first column."""
        return str(self.data.columns[0])

    @property
    def interpolators(self) -> list[Interpolator]:
        """The interpolators of the columns after the first, in column order."""
        x = self.data[self.xid]
        return [
            Interpolator(x=x, y=self.data[column], method=self.method)
            for column in self.data.columns[1:]
        ]

    @staticmethod
    def from_csv(
        csv_file: Path | str,
        method: InterpolationMethod | str = InterpolationMethod.LINEAR,
        sep: str = ",",
    ) -> Interpolation:
        """Interpolation of the data of a csv file, x in the first column."""
        data: pd.DataFrame = pd.read_csv(csv_file, sep=sep)
        return Interpolation(data=data, method=method)

    @staticmethod
    def from_tsv(
        tsv_file: Path | str,
        method: InterpolationMethod | str = InterpolationMethod.LINEAR,
    ) -> Interpolation:
        """Interpolation of the data of a tsv file, x in the first column."""
        return Interpolation.from_csv(csv_file=tsv_file, method=method, sep="\t")
```

In `_create_sbml` replace `self.interpolators = Interpolation.create_interpolators(self.data, self.method)` and the loop over it by `for interpolator in self.interpolators:`; remove the attribute `self.interpolators` from `__init__`. Delete `create_interpolators`.

In `examples/interpolation/pancreas.py` replace

```python
            interpolators = interpolation.create_interpolators(
                data=data1, method=method
            )
            for interpolator in interpolators:
```

by

```python
            for interpolator in interpolation.interpolators:
```

and delete the old test `test_unsorted_data_equals_sorted_data` if it used `create_interpolators` (rewrite its body to compare `interpolation.interpolators[0].formula()` of the unsorted and the sorted data).

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest -q -x tests/interpolation/ tests/examples/test_example_scripts.py -k "interpolation or pancreas"`
Expected: PASS

- [ ] **Step 5: Lint, type check, commit**

```bash
.venv/bin/ruff check -q src tests examples && .venv/bin/ruff format -q src tests examples && uvx ty check
git add src/sbmlutils/data/interpolation.py tests/interpolation/test_interpolation.py examples/interpolation/pancreas.py
git commit -m "Interpolation refuses data it cannot interpolate, interpolators is a property (#16)"
```

---

### Task 3: The standalone model through the factory

**Files:**
- Modify: `src/sbmlutils/data/interpolation.py` (`_create_sbml`, new `_standalone_model`, remove module `notes`, `_init_sbml_model`, `add_interpolator_to_model`, the TODO module docstring)
- Create: `src/sbmlutils/data/_driving.py` with `check_sid` only (grows in Task 4)
- Test: `tests/interpolation/test_interpolation.py`

**Interfaces:**
- Consumes: `Interpolation.interpolators`, `Interpolation.xid` (Task 2), `Interpolator.formula()` (Task 1).
- Produces: `_driving.check_sid(sid: str, what: str) -> None` raising `ValueError(f"{what} '{sid}' is not an SBML id.")`; the standalone model: SBML L3V2, model id `Interpolation_<method>` (spaces as `_`), one non-constant parameter per column with a port `<id>_port`, a non-constant parameter x with a port when x is not `time`.

- [ ] **Step 1: Write the failing tests**

```python
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
    """x other than time is a parameter with a port, which a parent replaces."""
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest -q -x tests/interpolation/test_interpolation.py -k standalone`
Expected: FAIL (level 3 version 1, no ports).

- [ ] **Step 3: Implement**

Create `src/sbmlutils/data/_driving.py`:

```python
"""Drive a model with interpolated data, in place or through comp.

The functions of this module implement `Interpolation.drive`,
`Interpolation.drive_comp` and `Interpolation.assignment_rules` of
`sbmlutils.data.interpolation`, which document the behaviour.
"""

from __future__ import annotations

import logging

import libsbml

logger = logging.getLogger(__name__)


def check_sid(sid: str, what: str) -> None:
    """Check that a name used as an id is an SBML id.

    Args:
        sid: the name
        what: what the name is, for the message, e.g. "Column"

    Raises:
        ValueError: if the name is not an SBML id
    """
    if not libsbml.SyntaxChecker.isValidSBMLSId(sid):
        raise ValueError(f"{what} '{sid}' is not an SBML id.")
```

In `interpolation.py` replace the module docstring:

```python
"""Interpolation of data points, as a model of its own or driving a model.

A table of data points becomes assignment rules which evaluate a constant,
linear or natural cubic spline interpolation of every column against the
first. The rules make a standalone model (`Interpolation.write_sbml_to_file`),
drive the quantities of an existing model in place (`Interpolation.drive`) or
through a comp model which leaves the original untouched
(`Interpolation.drive_comp`), or go into a model definition of the factory
(`Interpolation.assignment_rules`). See the guide `docs/interpolation.md`.
"""
```

Delete the module level `notes`, `_init_sbml_model`, `add_interpolator_to_model` and the attributes `self.doc`/`self.model`. New imports: `from sbmlutils.data import _driving`, `from sbmlutils.factory import AssignmentRule, Document, Model, Package, Parameter`. Replace `_create_sbml`:

```python
    def _create_sbml(self) -> libsbml.SBMLDocument:
        """Create the document of the standalone model, SBML L3V2.

        Returns:
            The validated document.
        """
        doc: libsbml.SBMLDocument = Document(
            self._standalone_model(), sbml_level=3, sbml_version=2
        ).create_sbml()
        validate_doc(doc, options=ValidationOptions(units_consistency=False))
        return doc

    def _standalone_model(self) -> Model:
        """The standalone model: a parameter with a port and a rule per column.

        x other than `time` is a parameter with a port as well, set to the
        first value of x, so a parent model can replace it with its quantity.

        Raises:
            ValueError: If a column name is not an SBML id.
        """
        interpolators = self.interpolators
        parameters: list[Parameter] = []
        if self.xid != "time":
            parameters.append(
                Parameter(
                    self.xid,
                    value=float(self.data[self.xid].iloc[0]),
                    constant=False,
                    port=True,
                )
            )
        for interpolator in interpolators:
            _driving.check_sid(interpolator.yid, "Column")
            parameters.append(Parameter(interpolator.yid, constant=False, port=True))
        columns = ", ".join(f"`{i.yid}`" for i in interpolators)
        return Model(
            sid=f"Interpolation_{self.method}".replace(" ", "_"),
            name=f"Interpolation {self.method}",
            notes=(
                f"# Interpolation of data\n\nThe {self.method} interpolation of "
                f"{columns} over `{self.xid}`, written by sbmlutils. Outside the "
                f"data the first and the last value are held."
            ),
            packages=[Package.COMP_V1],
            parameters=parameters,
            rules=[AssignmentRule(i.yid, i.formula()) for i in interpolators],
        )
```

If `Document(...).create_sbml()` validates or logs on its own, keep its behaviour; if the factory `AssignmentRule` writes a unit onto the existing parameter, pass `unit=None`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest -q -x tests/interpolation/ tests/examples/test_example_scripts.py -k "interpolation or pancreas"`
Expected: PASS

- [ ] **Step 5: Lint, type check, commit**

```bash
.venv/bin/ruff check -q src tests examples && .venv/bin/ruff format -q src tests examples && uvx ty check
git add src/sbmlutils/data/interpolation.py src/sbmlutils/data/_driving.py tests/interpolation/test_interpolation.py
git commit -m "The standalone interpolation model through the factory, L3V2 with ports (#16)"
```

---

### Task 4: Driving a model in place

**Files:**
- Modify: `src/sbmlutils/data/_driving.py`
- Modify: `src/sbmlutils/data/interpolation.py` (method `Interpolation.drive`)
- Create: `tests/interpolation/models.py`, `tests/interpolation/test_drive.py`

**Interfaces:**
- Consumes: `Interpolation.interpolators`, `Interpolation.xid`, `Interpolator.ast()`, `check_sid`.
- Produces (in `_driving`):
  - `resolve_targets(interpolators: Sequence[Interpolator], xid: str, targets: Mapping[str, str] | None) -> dict[str, Interpolator]` (target id to its interpolator)
  - `read_document(source: Path | str | libsbml.SBMLDocument) -> libsbml.SBMLDocument`
  - `check_model(model: libsbml.Model, driven: Mapping[str, Interpolator], xid: str) -> dict[str, libsbml.Parameter | libsbml.Species | libsbml.Compartment]`
  - `write_interpolation(model: libsbml.Model, target: str, interpolator: Interpolator) -> libsbml.AssignmentRule`
  - `drive(source, interpolators, xid, targets, filepath) -> libsbml.SBMLDocument`
- Produces (public): `Interpolation.drive(self, source: Path | str | libsbml.SBMLDocument, targets: Mapping[str, str] | None = None, filepath: Path | None = None) -> libsbml.SBMLDocument`
- Produces (tests): `tests/interpolation/models.py` with `uptake_model(**changes) -> Model` and `write_model(model: Model, path: Path, level: int = 3, version: int = 1) -> Path`.

- [ ] **Step 1: Write the shared test models**

`tests/interpolation/models.py`:

```python
"""The models the tests of driving a model with data use."""

from pathlib import Path

import libsbml

from sbmlutils.factory import (
    AssignmentRule,
    Compartment,
    Model,
    Parameter,
    Reaction,
    Species,
    create_model,
)
from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.validation import ValidationOptions

#: the uptake model is written without units, the unit check is not the subject
OPTIONS = ValidationOptions(units_consistency=False)


def uptake_model() -> Model:
    """Glucose uptake: `glc_ext` in `ext` taken up into `glc` in `cell`."""
    return Model(
        "uptake",
        compartments=[Compartment("ext", 2.0), Compartment("cell", 1.0)],
        species=[
            Species("glc_ext", initialConcentration=5.0, compartment="ext"),
            Species("glc", initialConcentration=0.0, compartment="cell"),
        ],
        parameters=[Parameter("k", 0.5), Parameter("f", 1.0)],
        reactions=[
            Reaction("UPTAKE", "glc_ext -> glc", formula="f * k * glc_ext"),
            Reaction("USE", "glc -> ", formula="0.1 * glc"),
        ],
    )


def write_model(model: Model, path: Path, level: int = 3, version: int = 1) -> Path:
    """Write a model, converted to the level and version, and return the path."""
    create_model(model, filepath=path, validation_options=OPTIONS)
    if (level, version) != (3, 1):
        doc = read_sbml(path)
        assert doc.setLevelAndVersion(level, version, False)
        write_sbml(doc, filepath=path)
    return path


__all__ = ["AssignmentRule", "OPTIONS", "uptake_model", "write_model", "libsbml"]
```

- [ ] **Step 2: Write the failing tests**

`tests/interpolation/test_drive.py`:

```python
"""Driving a model in place with interpolated data."""

from pathlib import Path

import libsbml
import pandas as pd
import pytest

from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import (
    AlgebraicRule,
    AssignmentRule,
    Event,
    InitialAssignment,
    RateRule,
)
from tests.interpolation.models import uptake_model, write_model

TIMECOURSE = pd.DataFrame(
    {
        "time": [0.0, 2.0, 4.0, 6.0],
        "glc_ext": [5.0, 8.0, 6.0, 5.0],
        "f": [1.0, 2.0, 0.5, 1.0],
        "ext": [2.0, 2.5, 2.0, 1.5],
    }
)


def _interpolation(*columns: str) -> Interpolation:
    """The linear interpolation of the time course, x and the columns."""
    return Interpolation(TIMECOURSE[["time", *columns]], method="linear")


def test_drive_parameter(tmp_path: Path) -> None:
    """A parameter becomes non constant and follows the data."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive(path)
    model = doc.getModel()
    assert not model.getParameter("f").getConstant()
    assert model.getAssignmentRuleByVariable("f") is not None
    assert doc.getNumErrors(libsbml.LIBSBML_SEV_ERROR) == 0


def test_drive_species(tmp_path: Path) -> None:
    """A species becomes a boundary species and keeps its reactions."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    model = _interpolation("glc_ext").drive(path).getModel()
    species = model.getSpecies("glc_ext")
    assert species.getBoundaryCondition()
    assert not species.getConstant()
    assert model.getReaction("UPTAKE").getReactant(0).getSpecies() == "glc_ext"


def test_drive_compartment(tmp_path: Path) -> None:
    """A compartment becomes non constant."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    model = _interpolation("ext").drive(path).getModel()
    assert not model.getCompartment("ext").getConstant()


@pytest.mark.parametrize("only_substance", [False, True])
def test_drive_species_simulated(tmp_path: Path, only_substance: bool) -> None:
    """The data is the concentration, or the amount with only substance units."""
    roadrunner = pytest.importorskip("roadrunner")
    model = uptake_model()
    model.species[0].hasOnlySubstanceUnits = only_substance
    path = write_model(model, tmp_path / "uptake.xml")
    driven = tmp_path / "driven.xml"
    _interpolation("glc_ext").drive(path, filepath=driven)
    r = roadrunner.RoadRunner(str(driven))
    selection = "glc_ext" if only_substance else "[glc_ext]"
    s = r.simulate(0, 6, 4, selections=["time", selection])
    assert list(s[selection]) == pytest.approx([5.0, 8.0, 6.0, 5.0])


def test_drive_by_mapping_with_model_quantity_as_x(tmp_path: Path) -> None:
    """`targets` maps a column to an id, x is a quantity of the model."""
    roadrunner = pytest.importorskip("roadrunner")
    data = pd.DataFrame({"f": [0.0, 1.0, 2.0], "rate": [0.0, 0.25, 1.0]})
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    driven = tmp_path / "driven.xml"
    Interpolation(data, method="linear").drive(path, {"rate": "k"}, filepath=driven)
    r = roadrunner.RoadRunner(str(driven))
    assert r["k"] == pytest.approx(0.25)
    r["f"] = 1.5
    assert r["k"] == pytest.approx(0.625)


def test_drive_document_in_place(tmp_path: Path) -> None:
    """A document is changed and returned, not copied."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = libsbml.readSBMLFromFile(str(path))
    assert _interpolation("f").drive(doc) is doc
    assert doc.getModel().getAssignmentRuleByVariable("f") is not None


def test_drive_sbml_string(tmp_path: Path) -> None:
    """An SBML string is read."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive(path.read_text())
    assert doc.getModel().getAssignmentRuleByVariable("f") is not None


def test_drive_level_2(tmp_path: Path) -> None:
    """A Level 2 model is driven and keeps its level."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml", level=2, version=4)
    doc = _interpolation("f").drive(path)
    assert (doc.getLevel(), doc.getVersion()) == (2, 4)
    assert doc.getNumErrors(libsbml.LIBSBML_SEV_ERROR) == 0


def test_initial_assignment_is_removed(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An initial assignment of a target is removed, with a log line."""
    model = uptake_model()
    model.assignments = [InitialAssignment("f", "2 * k")]
    path = write_model(model, tmp_path / "uptake.xml")
    with caplog.at_level("INFO"):
        driven = _interpolation("f").drive(path).getModel()
    assert driven.getInitialAssignmentBySymbol("f") is None
    assert "initial assignment of 'f'" in caplog.text


@pytest.mark.parametrize(
    "change, match",
    [
        (lambda m: m.rules.append(AssignmentRule("f", "2 * k")), "an assignment rule"),
        (lambda m: m.rate_rules.append(RateRule("f", "0.1")), "a rate rule"),
        (
            lambda m: m.algebraic_rules.append(AlgebraicRule("f - 2 * k")),
            "an algebraic rule",
        ),
        (
            lambda m: m.events.append(
                Event("E1", trigger="time > 1", assignments={"f": 3.0})
            ),
            "an event assignment",
        ),
    ],
)
def test_determined_target_raises(tmp_path: Path, change: object, match: str) -> None:
    """A target the model determines already is refused."""
    model = uptake_model()
    model.parameters[1].constant = False
    change(model)  # type: ignore[operator]
    path = write_model(model, tmp_path / "uptake.xml")
    with pytest.raises(ValueError, match=match):
        _interpolation("f").drive(path)


@pytest.mark.parametrize(
    "data, targets, match",
    [
        (TIMECOURSE[["time", "f"]], {"g": "f"}, "no column 'g'"),
        (TIMECOURSE[["time", "f"]], {"time": "f"}, "is x"),
        (TIMECOURSE[["time", "f"]], {"f": "missing"}, "'missing' is not an element"),
        (TIMECOURSE[["time", "f"]], {"f": "UPTAKE"}, "is a reaction"),
        (TIMECOURSE[["time", "f", "glc_ext"]], {"f": "k", "glc_ext": "k"}, "two columns"),
        (TIMECOURSE.rename(columns={"time": "t"})[["t", "f"]], None, "'t'"),
    ],
)
def test_invalid_targets_raise(
    tmp_path: Path, data: pd.DataFrame, targets: dict[str, str] | None, match: str
) -> None:
    """Unknown columns, unknown or undrivable targets, a missing x are refused."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    with pytest.raises(ValueError, match=match):
        Interpolation(data, method="linear").drive(path, targets)


def test_drive_twice_raises_and_leaves_document(tmp_path: Path) -> None:
    """Driving the driven target again names its rule and changes nothing."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive(path)
    before = libsbml.writeSBMLToString(doc)
    with pytest.raises(ValueError, match="an assignment rule"):
        _interpolation("glc_ext", "f").drive(doc)
    assert libsbml.writeSBMLToString(doc) == before
```

Check the names of the factory before running: `AlgebraicRule`, `RateRule`, `Event`, `InitialAssignment` and the `Model` fields `rules`, `rate_rules`, `algebraic_rules`, `assignments`, `events` (`rg -n "class (AlgebraicRule|RateRule|Event|InitialAssignment)\b|^\s+(rules|rate_rules|algebraic_rules|assignments|events):" src/sbmlutils/factory`); adapt the four lambdas and the `Event` arguments to them.

- [ ] **Step 3: Run the tests to verify they fail**

Run: `.venv/bin/pytest -q -x tests/interpolation/test_drive.py`
Expected: FAIL, `AttributeError: 'Interpolation' object has no attribute 'drive'`.

- [ ] **Step 4: Implement**

Add to `_driving.py` (imports: `from collections.abc import Mapping, Sequence`, `from pathlib import Path`, `from typing import TYPE_CHECKING`, `from sbmlutils.io.sbml import read_sbml, write_sbml`, `from sbmlutils.validation import ValidationOptions, check, validate_doc`, and under `TYPE_CHECKING` `from sbmlutils.data.interpolation import Interpolator`):

```python
#: an element a column can drive
type Target = libsbml.Parameter | libsbml.Species | libsbml.Compartment

#: the validation of a driven model, the numbers of a formula carry no units
_OPTIONS = ValidationOptions(units_consistency=False)


def resolve_targets(
    interpolators: Sequence[Interpolator],
    xid: str,
    targets: Mapping[str, str] | None,
) -> dict[str, Interpolator]:
    """Map the id of every driven element to the interpolator of its column.

    Args:
        interpolators: the interpolators of the columns
        xid: the name of x
        targets: column to the id it drives, `None` for every column driving
            the element of its own id

    Raises:
        ValueError: for a column which is not in the data or is x, for two
            columns driving one id, for an id which is not an SBML id
    """
    by_column = {interpolator.yid: interpolator for interpolator in interpolators}
    if targets is None:
        targets = {column: column for column in by_column}
    driven: dict[str, Interpolator] = {}
    for column, target in targets.items():
        if column == xid:
            raise ValueError(f"'{column}' is x of the interpolation, it drives nothing.")
        if column not in by_column:
            raise ValueError(
                f"The data has no column '{column}', its columns are "
                f"{', '.join(repr(c) for c in by_column)}."
            )
        check_sid(target, "Target")
        if target in driven:
            raise ValueError(
                f"'{target}' is driven by two columns, '{driven[target].yid}' and "
                f"'{column}'."
            )
        driven[target] = by_column[column]
    return driven


def read_document(source: Path | str | libsbml.SBMLDocument) -> libsbml.SBMLDocument:
    """The document of a source: a document itself, an SBML string or a path."""
    if isinstance(source, libsbml.SBMLDocument):
        return source
    if isinstance(source, str) and "<sbml" not in source:
        source = Path(source)
    return read_sbml(source)


def _find_target(model: libsbml.Model, sid: str) -> Target:
    """The parameter, species or compartment `sid` of the model.

    Raises:
        ValueError: if the model has no element `sid`, or one of another class
    """
    element: Target | None = (
        model.getParameter(sid) or model.getSpecies(sid) or model.getCompartment(sid)
    )
    if element is not None:
        return element
    other: libsbml.SBase | None = model.getElementBySId(sid)
    if other is None:
        raise ValueError(f"'{sid}' is not an element of the model '{model.getId()}'.")
    raise ValueError(
        f"'{sid}' is a {other.getElementName()}; only a parameter, a species or a "
        f"compartment can be driven."
    )


def _mentions(ast: libsbml.ASTNode | None, sid: str) -> bool:
    """Whether a math names `sid`."""
    if ast is None:
        return False
    if ast.isName() and ast.getName() == sid:
        return True
    return any(_mentions(ast.getChild(k), sid) for k in range(ast.getNumChildren()))


def _determined_by(model: libsbml.Model, sid: str) -> str | None:
    """What of the model determines `sid` already, `None` if nothing does."""
    rule: libsbml.Rule
    for rule in model.getListOfRules():
        if rule.isAlgebraic():
            if _mentions(rule.getMath(), sid):
                return "an algebraic rule"
        elif rule.getVariable() == sid:
            return "an assignment rule" if rule.isAssignment() else "a rate rule"
    event: libsbml.Event
    for event in model.getListOfEvents():
        assignment: libsbml.EventAssignment
        for assignment in event.getListOfEventAssignments():
            if assignment.getVariable() == sid:
                return f"an event assignment of the event '{event.getId()}'"
    return None


def check_model(
    model: libsbml.Model, driven: Mapping[str, Interpolator], xid: str
) -> dict[str, Target]:
    """Check that x exists and the targets can be driven, before anything changes.

    Raises:
        ValueError: for a missing x, a target which is x, is missing, is of
            another class, or which the model determines already
    """
    if xid != "time" and model.getElementBySId(xid) is None:
        raise ValueError(
            f"x of the interpolation, '{xid}', is not an element of the model "
            f"'{model.getId()}'; name the first column 'time' or after the quantity "
            f"of the model it is."
        )
    elements: dict[str, Target] = {}
    for target in driven:
        if target == xid:
            raise ValueError(f"'{target}' is x of the interpolation, it cannot be driven.")
        element = _find_target(model, target)
        determined = _determined_by(model, target)
        if determined is not None:
            raise ValueError(
                f"'{target}' is determined by {determined} of the model already; "
                f"driving it would replace that, remove it first."
            )
        elements[target] = element
    return elements


def write_interpolation(
    model: libsbml.Model, target: str, interpolator: Interpolator
) -> libsbml.AssignmentRule:
    """Write the interpolation of a column as the assignment rule of `target`."""
    rule: libsbml.AssignmentRule = model.createAssignmentRule()
    check(rule.setVariable(target), f"Set the variable '{target}' of an interpolation")
    check(
        rule.setMath(interpolator.ast()),
        f"Set the interpolation of '{interpolator.yid}' on '{target}'",
    )
    return rule


def _make_variable(element: Target) -> None:
    """Make a target non constant, a species a boundary species as well."""
    check(element.setConstant(False), f"Set '{element.getId()}' non constant")
    if isinstance(element, libsbml.Species):
        check(
            element.setBoundaryCondition(True),
            f"Set '{element.getId()}' a boundary species",
        )


def drive(
    source: Path | str | libsbml.SBMLDocument,
    interpolators: Sequence[Interpolator],
    xid: str,
    targets: Mapping[str, str] | None,
    filepath: Path | None,
) -> libsbml.SBMLDocument:
    """Drive the model of a document in place, see `Interpolation.drive`."""
    doc = read_document(source)
    model: libsbml.Model | None = doc.getModel()
    if model is None:
        raise ValueError("The document has no model to drive.")
    driven = resolve_targets(interpolators, xid, targets)
    elements = check_model(model, driven, xid)
    for target, interpolator in driven.items():
        if model.getInitialAssignmentBySymbol(target) is not None:
            model.removeInitialAssignment(target)
            logger.info(
                "The initial assignment of '%s' is removed, the interpolation of "
                "'%s' determines it.",
                target,
                interpolator.yid,
            )
        _make_variable(elements[target])
        write_interpolation(model, target, interpolator)
    validate_doc(doc, options=_OPTIONS)
    if filepath is not None:
        write_sbml(doc, filepath=filepath)
    return doc
```

In `Interpolation` (imports `from collections.abc import Mapping`):

```python
    def drive(
        self,
        source: Path | str | libsbml.SBMLDocument,
        targets: Mapping[str, str] | None = None,
        filepath: Path | None = None,
    ) -> libsbml.SBMLDocument:
        """Drive quantities of a model with the data, in place.

        Every driven element gets the assignment rule of its column. A
        parameter or a compartment becomes non constant, a species a non
        constant boundary species, so it stays a reactant or product; the
        data of a species is its concentration, or its amount if it has only
        substance units. The data is in the units of the element it drives.
        An initial assignment of a driven element is removed. x is `time` or
        the quantity of the model named like the first column.

        Args:
            source: the model, an SBML file, an SBML string or a document,
                which is changed and returned
            targets: the column which drives an element, to the id of the
                element; `None` for every column driving the element of its
                own id
            filepath: the file to write the driven model into, if given

        Returns:
            The document of the driven model, SBML Level and Version unchanged.

        Raises:
            ValueError: for a column which is not in the data, two columns
                driving one element, an element which is not in the model, is
                not a parameter, species or compartment, or is determined by a
                rule or an event assignment already, or an x which is not in
                the model; the document is unchanged then.
        """
        return _driving.drive(source, self.interpolators, self.xid, targets, filepath)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/bin/pytest -q -x tests/interpolation/`
Expected: PASS

- [ ] **Step 6: Lint, type check, commit**

```bash
.venv/bin/ruff check -q src tests && .venv/bin/ruff format -q src tests && uvx ty check
git add src/sbmlutils/data/_driving.py src/sbmlutils/data/interpolation.py tests/interpolation/models.py tests/interpolation/test_drive.py
git commit -m "Drive a model in place with interpolated data (#16)"
```

---

### Task 5: Driving a model through comp

**Files:**
- Modify: `src/sbmlutils/data/_driving.py`, `src/sbmlutils/data/interpolation.py` (method `Interpolation.drive_comp`)
- Create: `tests/interpolation/test_drive_comp.py`

**Interfaces:**
- Consumes: `read_document`, `resolve_targets`, `check_model`, `write_interpolation`, `Target` (Task 4); `uptake_model`, `write_model` (Task 4 tests).
- Produces: `_driving.drive_comp(source, interpolators, xid, targets, filepath, embed) -> libsbml.SBMLDocument`; `Interpolation.drive_comp(self, source: Path | str | libsbml.SBMLDocument, targets: Mapping[str, str] | None = None, filepath: Path | None = None, embed: bool = False) -> libsbml.SBMLDocument`. The top model is `<model id>_driven`, the submodel and the (external) model definition are `<model id>`.

- [ ] **Step 1: Write the failing tests**

`tests/interpolation/test_drive_comp.py`:

```python
"""Driving a model through a comp model with interpolated data."""

from pathlib import Path

import libsbml
import numpy as np
import pandas as pd
import pytest

from sbmlutils.comp import flatten_sbml
from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import InitialAssignment, Model, Port
from tests.interpolation.models import uptake_model, write_model

TIMECOURSE = pd.DataFrame(
    {
        "time": [0.0, 2.0, 4.0, 6.0],
        "glc_ext": [5.0, 8.0, 6.0, 5.0],
        "f": [1.0, 2.0, 0.5, 1.0],
        "ext": [2.0, 2.5, 2.0, 1.5],
    }
)


def _interpolation(*columns: str) -> Interpolation:
    """The linear interpolation of the time course, x and the columns."""
    return Interpolation(TIMECOURSE[["time", *columns]], method="linear")


def _errors(doc: libsbml.SBMLDocument) -> list[str]:
    """The errors of a full consistency check of a document."""
    doc.checkConsistency()
    return [
        doc.getError(k).getMessage()
        for k in range(doc.getNumErrors())
        if doc.getError(k).getSeverity() >= libsbml.LIBSBML_SEV_ERROR
    ]


def test_external_reference(tmp_path: Path) -> None:
    """The original is referenced relative to the comp file and is untouched."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    original = path.read_bytes()
    doc = _interpolation("glc_ext").drive_comp(path, filepath=tmp_path / "driven.xml")
    assert path.read_bytes() == original
    assert (tmp_path / "driven.xml").exists()
    emd = doc.getPlugin("comp").getExternalModelDefinition("uptake")
    assert emd.getSource() == "uptake.xml"
    assert emd.getModelRef() == "uptake"
    top = doc.getModel()
    assert top.getId() == "uptake_driven"
    assert top.getPlugin("comp").getSubmodel("uptake").getModelRef() == "uptake"
    assert _errors(doc) == []


def test_external_reference_in_other_directory(tmp_path: Path) -> None:
    """The source is relative to the directory of the comp file."""
    path = write_model(uptake_model(), tmp_path / "models" / "uptake.xml")
    out = tmp_path / "out" / "driven.xml"
    out.parent.mkdir()
    doc = _interpolation("f").drive_comp(path, filepath=out)
    emd = doc.getPlugin("comp").getExternalModelDefinition("uptake")
    assert emd.getSource() == "../models/uptake.xml"
    flat = flatten_sbml(out, tmp_path / "flat.xml")
    assert flat.getModel().getAssignmentRuleByVariable("f") is not None


def test_absolute_reference_without_filepath(tmp_path: Path) -> None:
    """Without a file the source is absolute and flattens in memory."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive_comp(path)
    emd = doc.getPlugin("comp").getExternalModelDefinition("uptake")
    assert Path(emd.getSource()) == path.resolve()
    assert _errors(doc) == []


def test_embed(tmp_path: Path) -> None:
    """`embed=True` copies the original in, also from a string or a document."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    for source in (path, path.read_text(), libsbml.readSBMLFromFile(str(path))):
        doc = _interpolation("f").drive_comp(source, embed=True)
        plugin = doc.getPlugin("comp")
        assert plugin.getNumExternalModelDefinitions() == 0
        assert plugin.getModelDefinition("uptake").getNumReactions() == 2
        assert _errors(doc) == []


def test_string_without_embed_raises(tmp_path: Path) -> None:
    """A string or a document has no file to reference."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    with pytest.raises(ValueError, match="embed=True"):
        _interpolation("f").drive_comp(path.read_text())


def test_species_target_placeholders(tmp_path: Path) -> None:
    """A species is replaced by a species, its compartment replaced by the original's."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    top = _interpolation("glc_ext").drive_comp(path).getModel()
    species = top.getSpecies("glc_ext")
    assert species.getBoundaryCondition() and not species.getConstant()
    replaced = species.getPlugin("comp").getReplacedElement(0)
    assert (replaced.getSubmodelRef(), replaced.getIdRef()) == ("uptake", "glc_ext")
    compartment = top.getCompartment("ext")
    replaced_by = compartment.getPlugin("comp").getReplacedBy()
    assert (replaced_by.getSubmodelRef(), replaced_by.getIdRef()) == ("uptake", "ext")


def test_reference_through_port(tmp_path: Path) -> None:
    """An element with a port of the original is referenced by its port."""
    model = uptake_model()
    model.parameters[1].port = True
    path = write_model(model, tmp_path / "uptake.xml")
    top = _interpolation("f").drive_comp(path).getModel()
    replaced = top.getParameter("f").getPlugin("comp").getReplacedElement(0)
    assert replaced.getPortRef() == "f_port"


def test_initial_assignment_with_metaid_is_deleted(tmp_path: Path) -> None:
    """An initial assignment with a metaid is deleted from the submodel."""
    model = uptake_model()
    model.assignments = [InitialAssignment("f", "2 * k", metaId="meta_ia_f")]
    path = write_model(model, tmp_path / "uptake.xml")
    doc = _interpolation("f").drive_comp(path)
    submodel = doc.getModel().getPlugin("comp").getSubmodel("uptake")
    assert submodel.getDeletion(0).getMetaIdRef() == "meta_ia_f"
    assert _errors(doc) == []


def test_initial_assignment_without_metaid_raises(tmp_path: Path) -> None:
    """Without a metaid the initial assignment cannot be deleted."""
    model = uptake_model()
    model.assignments = [InitialAssignment("f", "2 * k")]
    path = write_model(model, tmp_path / "uptake.xml")
    doc = libsbml.readSBMLFromFile(str(path))
    doc.getModel().getInitialAssignmentBySymbol("f").unsetMetaId()
    libsbml.writeSBMLToFile(doc, str(path))
    with pytest.raises(ValueError, match="`drive`"):
        _interpolation("f").drive_comp(path)


def test_level_2_raises(tmp_path: Path) -> None:
    """comp is a Level 3 package."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml", level=2, version=4)
    with pytest.raises(ValueError, match="Level 3"):
        _interpolation("f").drive_comp(path)


def test_embedding_hierarchical_model_raises(tmp_path: Path) -> None:
    """A model with comp content is referenced, not embedded."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    driven = tmp_path / "driven.xml"
    _interpolation("f").drive_comp(path, filepath=driven)
    with pytest.raises(ValueError, match="hierarchical"):
        _interpolation("glc_ext").drive_comp(driven, embed=True)


SCENARIOS = {
    "parameter": (TIMECOURSE[["time", "f"]], None),
    "species": (TIMECOURSE[["time", "glc_ext"]], None),
    "compartment": (TIMECOURSE[["time", "ext"]], None),
    "species in driven compartment": (TIMECOURSE[["time", "glc_ext", "ext"]], None),
    "model quantity as x": (
        pd.DataFrame({"f": [0.0, 1.0, 2.0], "rate": [0.0, 0.25, 1.0]}),
        {"rate": "k"},
    ),
}


@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("embed", [False, True])
def test_comp_equals_in_place(tmp_path: Path, scenario: str, embed: bool) -> None:
    """The flattened comp model simulates as the model driven in place."""
    roadrunner = pytest.importorskip("roadrunner")
    data, targets = SCENARIOS[scenario]
    interpolation = Interpolation(data, method="linear")
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    in_place = tmp_path / "in_place.xml"
    interpolation.drive(path, targets, filepath=in_place)
    comp = tmp_path / "comp.xml"
    doc = interpolation.drive_comp(path, targets, filepath=comp, embed=embed)
    assert _errors(doc) == []
    flat = tmp_path / "flat.xml"
    flatten_sbml(comp, flat)

    r_in_place = roadrunner.RoadRunner(str(in_place))
    r_flat = roadrunner.RoadRunner(str(flat))
    s_in_place = r_in_place.simulate(0, 6, 13, selections=["time", "glc", "glc_ext"])
    s_flat = r_flat.simulate(
        0, 6, 13, selections=["time", "uptake__glc", "glc_ext"]
    )
    np.testing.assert_allclose(s_flat, s_in_place, rtol=1e-6, atol=1e-9)
```

`glc_ext` keeps its id in the flattened model only when it is a target or the compartment placeholder keeps its species; in the scenarios where `glc_ext` is not driven its flattened id is `uptake__glc_ext`. Select per scenario: write the selections as `["time", "uptake__glc", flat_id("glc_ext")]` with

```python
def _flat_id(flat: libsbml.Model, sid: str) -> str:
    """The id of an element of the original in the flattened model."""
    return sid if flat.getElementBySId(sid) is not None else f"uptake__{sid}"
```

read from `libsbml.readSBMLFromFile(str(flat)).getModel()`; use it for both ids.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest -q -x tests/interpolation/test_drive_comp.py`
Expected: FAIL, `AttributeError: 'Interpolation' object has no attribute 'drive_comp'`.

- [ ] **Step 3: Implement**

Add to `_driving.py` (import `os`):

```python
#: the units of a model which the top model of a comp document takes over
_MODEL_UNITS = (
    "TimeUnits",
    "SubstanceUnits",
    "ExtentUnits",
    "VolumeUnits",
    "AreaUnits",
    "LengthUnits",
)


def _source_path(source: Path | str | libsbml.SBMLDocument) -> Path | None:
    """The file of a source, `None` for a document or an SBML string."""
    if isinstance(source, Path):
        return source.resolve()
    if isinstance(source, str) and "<sbml" not in source:
        return Path(source).resolve()
    return None


def _is_hierarchical(doc: libsbml.SBMLDocument) -> bool:
    """Whether the document has comp content: model definitions or submodels."""
    doc_plugin: libsbml.CompSBMLDocumentPlugin | None = doc.getPlugin("comp")
    model_plugin: libsbml.CompModelPlugin | None = doc.getModel().getPlugin("comp")
    return bool(
        (
            doc_plugin is not None
            and doc_plugin.getNumModelDefinitions()
            + doc_plugin.getNumExternalModelDefinitions()
            > 0
        )
        or (model_plugin is not None and model_plugin.getNumSubmodels() > 0)
    )


def _deletions(model: libsbml.Model, driven: Mapping[str, Interpolator]) -> list[str]:
    """The metaids of the initial assignments of the targets, to delete.

    Raises:
        ValueError: for an initial assignment without a metaid
    """
    metaids: list[str] = []
    for target in driven:
        assignment: libsbml.InitialAssignment | None = (
            model.getInitialAssignmentBySymbol(target)
        )
        if assignment is None:
            continue
        if not assignment.isSetMetaId():
            raise ValueError(
                f"'{target}' has an initial assignment without a metaid, which a "
                f"comp model cannot delete from the original; give it a metaid or "
                f"drive the model in place with `drive`."
            )
        metaids.append(assignment.getMetaId())
    return metaids


def _comp_document(original: libsbml.SBMLDocument, embed: bool) -> libsbml.SBMLDocument:
    """An empty comp document, with the packages of the original when it embeds it."""
    version = 2 if original.getVersion() == 2 else 1
    doc = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, version, "comp", 1))
    check(doc.setPackageRequired("comp", True), "Set comp required")
    if embed:
        for k in range(original.getNumPlugins()):
            plugin: libsbml.SBasePlugin = original.getPlugin(k)
            name = plugin.getPackageName()
            if name == "comp":
                continue
            check(
                doc.enablePackage(plugin.getURI(), plugin.getPrefix(), True),
                f"Enable the package '{name}'",
            )
            check(
                doc.setPackageRequired(name, original.getPackageRequired(name)),
                f"Set the package '{name}' required",
            )
    return doc


def _reference(model: libsbml.Model, sid: str) -> tuple[str, str]:
    """How the comp model names an element of the original: its port, else its id."""
    plugin: libsbml.CompModelPlugin | None = model.getPlugin("comp")
    if plugin is not None:
        port: libsbml.Port
        for port in plugin.getListOfPorts():
            if port.isSetIdRef() and port.getIdRef() == sid:
                return "portRef", port.getId()
    return "idRef", sid


def _set_reference(
    sbase_ref: libsbml.SBaseRef, submodel: str, reference: tuple[str, str]
) -> None:
    """Point a replacement or a deletion at an element of the submodel."""
    check(sbase_ref.setSubmodelRef(submodel), f"Set the submodel '{submodel}'")
    kind, value = reference
    status = (
        sbase_ref.setPortRef(value) if kind == "portRef" else sbase_ref.setIdRef(value)
    )
    check(status, f"Set the {kind} '{value}'")


def _placeholder(top: libsbml.Model, element: Target) -> Target:
    """An element of the top model of the class of `element`, with its units."""
    sid = element.getId()
    placeholder: Target
    if isinstance(element, libsbml.Species):
        species: libsbml.Species = top.createSpecies()
        check(species.setCompartment(element.getCompartment()), "Set compartment")
        check(
            species.setHasOnlySubstanceUnits(element.getHasOnlySubstanceUnits()),
            "Set hasOnlySubstanceUnits",
        )
        check(species.setBoundaryCondition(True), "Set boundaryCondition")
        if element.isSetSubstanceUnits():
            check(species.setSubstanceUnits(element.getSubstanceUnits()), "Set units")
        placeholder = species
    elif isinstance(element, libsbml.Compartment):
        compartment: libsbml.Compartment = top.createCompartment()
        if element.isSetSpatialDimensions():
            check(
                compartment.setSpatialDimensions(
                    element.getSpatialDimensionsAsDouble()
                ),
                "Set spatialDimensions",
            )
        if element.isSetSize():
            check(compartment.setSize(element.getSize()), "Set size")
        if element.isSetUnits():
            check(compartment.setUnits(element.getUnits()), "Set units")
        placeholder = compartment
    else:
        parameter: libsbml.Parameter = top.createParameter()
        if element.isSetUnits():
            check(parameter.setUnits(element.getUnits()), "Set units")
        placeholder = parameter
    check(placeholder.setId(sid), f"Set the id '{sid}'")
    check(placeholder.setConstant(False), f"Set '{sid}' non constant")
    return placeholder


def _copy_units(top: libsbml.Model, model: libsbml.Model) -> None:
    """Take over the model units and the unit definitions the top model uses."""
    used: set[str] = set()
    for name in _MODEL_UNITS:
        if getattr(model, f"isSet{name}")():
            unit: str = getattr(model, f"get{name}")()
            check(getattr(top, f"set{name}")(unit), f"Set the model {name}")
            used.add(unit)
    for parameter in top.getListOfParameters():
        used.add(parameter.getUnits())
    for species in top.getListOfSpecies():
        used.add(species.getSubstanceUnits())
    for compartment in top.getListOfCompartments():
        used.add(compartment.getUnits())
    for uid in sorted(used - {""}):
        definition: libsbml.UnitDefinition | None = model.getUnitDefinition(uid)
        if definition is not None:
            check(top.addUnitDefinition(definition), f"Copy the unit '{uid}'")


def drive_comp(
    source: Path | str | libsbml.SBMLDocument,
    interpolators: Sequence[Interpolator],
    xid: str,
    targets: Mapping[str, str] | None,
    filepath: Path | None,
    embed: bool,
) -> libsbml.SBMLDocument:
    """Drive a model through a comp model, see `Interpolation.drive_comp`."""
    original = read_document(source)
    if original.getLevel() != 3:
        raise ValueError(
            f"The model is SBML Level {original.getLevel()} Version "
            f"{original.getVersion()}; the comp package is SBML Level 3, convert the "
            f"model to Level 3 first or drive it in place with `drive`."
        )
    model: libsbml.Model | None = original.getModel()
    if model is None:
        raise ValueError("The document has no model to drive.")
    source_path = _source_path(source)
    if not embed and source_path is None:
        raise ValueError(
            "An SBML string or a document is no file a comp model can reference; "
            "write it to a file or pass embed=True."
        )
    if embed and _is_hierarchical(original):
        raise ValueError(
            "A hierarchical model (with submodels or model definitions) cannot be "
            "embedded; reference it from its file, embed=False."
        )
    driven = resolve_targets(interpolators, xid, targets)
    elements = check_model(model, driven, xid)
    deletions = _deletions(model, driven)

    mid = model.getId() or "model"
    doc = _comp_document(original, embed)
    doc_plugin: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    if embed:
        definition = libsbml.ModelDefinition(model)
        check(definition.setId(mid), f"Set the id of the model definition '{mid}'")
        check(doc_plugin.addModelDefinition(definition), "Embed the original")
    else:
        assert source_path is not None
        emd: libsbml.ExternalModelDefinition = (
            doc_plugin.createExternalModelDefinition()
        )
        if filepath is not None:
            out = Path(filepath).resolve()
            reference = Path(os.path.relpath(source_path, out.parent)).as_posix()
            # libsbml resolves `comp:source` against the location of the document
            doc.setLocationURI(f"file:{out}")
        else:
            reference = source_path.as_posix()
        check(emd.setId(mid), f"Set the id '{mid}'")
        check(emd.setSource(reference), f"Set the source '{reference}'")
        if model.isSetId():
            check(emd.setModelRef(model.getId()), "Set the modelRef")

    top: libsbml.Model = doc.createModel()
    check(top.setId(f"{mid}_driven"), "Set the id of the top model")
    top_plugin: libsbml.CompModelPlugin = top.getPlugin("comp")
    submodel: libsbml.Submodel = top_plugin.createSubmodel()
    check(submodel.setId(mid), f"Set the submodel '{mid}'")
    check(submodel.setModelRef(mid), f"Set the modelRef '{mid}'")
    for metaid in deletions:
        deletion: libsbml.Deletion = submodel.createDeletion()
        check(deletion.setMetaIdRef(metaid), f"Delete the initial assignment '{metaid}'")

    # the targets replace the elements of the original, compartments first,
    # so that a driven compartment is the compartment of a driven species
    for target in sorted(
        driven, key=lambda t: not isinstance(elements[t], libsbml.Compartment)
    ):
        placeholder = _placeholder(top, elements[target])
        replaced: libsbml.ReplacedElement = placeholder.getPlugin(
            "comp"
        ).createReplacedElement()
        _set_reference(replaced, mid, _reference(model, target))
        write_interpolation(top, target, driven[target])
    # the compartment of a driven species, and x, read the original
    readers = [
        s.getCompartment() for s in top.getListOfSpecies()
    ] + ([xid] if xid != "time" else [])
    for sid in readers:
        if top.getElementBySId(sid) is not None:
            continue
        compartment = model.getCompartment(sid)
        reader: libsbml.SBase
        if compartment is not None:
            reader = _placeholder(top, compartment)
            check(reader.setConstant(compartment.getConstant()), "Set constant")
        else:
            reader = top.createParameter()
            check(reader.setId(sid), f"Set the id '{sid}'")
            check(reader.setConstant(False), f"Set '{sid}' non constant")
        replaced_by: libsbml.ReplacedBy = reader.getPlugin("comp").createReplacedBy()
        _set_reference(replaced_by, mid, _reference(model, sid))
    _copy_units(top, model)

    validate_doc(doc, options=_OPTIONS)
    if filepath is not None:
        write_sbml(doc, filepath=Path(filepath))
    return doc
```

Notes for the implementer:
- A placeholder compartment which *reads* the original (`replacedBy`) keeps the constant attribute of the original, a driven one is non constant.
- If `doc.getPlugin("comp")` or `placeholder.getPlugin("comp")` returns `None` for a placeholder created before the comp namespace is known, create the top model after `_comp_document` (as above) and check that the plugin exists; a missing plugin is a bug, raise `RuntimeError`.
- If flattening reports duplicated unit definitions, keep `_copy_units` but skip a definition whose id the original defines identically and rely on the flattening; let the test `test_comp_equals_in_place` decide, with a model that has units (add one scenario with `create_model(..., units=...)` only if the plain models pass and units are untested).

In `Interpolation`:

```python
    def drive_comp(
        self,
        source: Path | str | libsbml.SBMLDocument,
        targets: Mapping[str, str] | None = None,
        filepath: Path | None = None,
        embed: bool = False,
    ) -> libsbml.SBMLDocument:
        """Drive quantities of a model with the data through a comp model.

        The comp document has the original as the submodel `<model id>` of
        the top model `<model id>_driven`, which holds the interpolation. A
        driven element is replaced by an element of its class in the top
        model, which the assignment rule of its column determines; a species
        keeps its compartment, which reads the compartment of the original,
        and x other than `time` reads the quantity of the original. After
        flattening the elements of the original are named `<model id>__<id>`,
        the driven elements and x keep their ids, and the model simulates as
        the one of `drive`. The data is in the units of the element it
        drives, the top model takes over the units of the original.

        Args:
            source: the model, an SBML Level 3 file, or with `embed=True` also
                an SBML string or a document; it is never changed
            targets: the column which drives an element, to the id of the
                element; `None` for every column driving the element of its
                own id
            filepath: the file to write the comp model into, if given; the
                reference to the original is relative to its directory
            embed: copy the original into the comp document as a model
                definition instead of referencing its file

        Returns:
            The comp document.

        Raises:
            ValueError: as `drive`, and for an original which is not SBML
                Level 3, a string or a document without `embed=True`, a
                hierarchical original with `embed=True`, or an initial
                assignment of a driven element without a metaid.
        """
        return _driving.drive_comp(
            source, self.interpolators, self.xid, targets, filepath, embed
        )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest -q -x tests/interpolation/`
Expected: PASS. If a comp document reports an error, print `_errors(doc)`, fix the cause in `_driving.py` (never the expectation), and rerun.

- [ ] **Step 5: Lint, type check, commit**

```bash
.venv/bin/ruff check -q src tests && .venv/bin/ruff format -q src tests && uvx ty check
git add src/sbmlutils/data/_driving.py src/sbmlutils/data/interpolation.py tests/interpolation/test_drive_comp.py
git commit -m "Drive a model through a comp model with interpolated data (#16)"
```

---

### Task 6: Interpolations in a model definition of the factory

**Files:**
- Modify: `src/sbmlutils/data/interpolation.py` (method `Interpolation.assignment_rules`)
- Create: `tests/interpolation/test_assignment_rules.py`

**Interfaces:**
- Consumes: `_driving.resolve_targets` (Task 4), `Interpolator.formula()` (Task 1).
- Produces: `Interpolation.assignment_rules(self, targets: Mapping[str, str] | None = None) -> list[AssignmentRule]`.

- [ ] **Step 1: Write the failing tests**

```python
"""Interpolations in a model definition of the factory."""

from pathlib import Path

import pandas as pd
import pytest

from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import AssignmentRule
from tests.interpolation.models import uptake_model, write_model

DATA = pd.DataFrame({"time": [0.0, 2.0, 4.0], "f_data": [1.0, 1.0 / 3.0, 2.0]})


def test_assignment_rules_of_mapping() -> None:
    """One rule per driven element, the formula of its column."""
    interpolation = Interpolation(DATA, method="linear")
    rules = interpolation.assignment_rules({"f_data": "f"})
    assert [type(rule) for rule in rules] == [AssignmentRule]
    assert rules[0].variable == "f"
    assert rules[0].value == interpolation.interpolators[0].formula()
    assert repr(1.0 / 3.0) in str(rules[0].value)


def test_assignment_rules_in_model(tmp_path: Path) -> None:
    """A model definition takes the rules and simulates the data."""
    roadrunner = pytest.importorskip("roadrunner")
    model = uptake_model()
    model.parameters[1].constant = False
    model.rules = Interpolation(DATA, method="linear").assignment_rules(
        {"f_data": "f"}
    )
    path = write_model(model, tmp_path / "uptake.xml")
    r = roadrunner.RoadRunner(str(path))
    s = r.simulate(0, 4, 3, selections=["time", "f"])
    assert list(s["f"]) == pytest.approx([1.0, 1.0 / 3.0, 2.0])


def test_assignment_rules_column_not_sid_raises() -> None:
    """Without targets a column name has to be an SBML id."""
    data = DATA.rename(columns={"f_data": "f [1/min]"})
    with pytest.raises(ValueError, match="not an SBML id"):
        Interpolation(data).assignment_rules()
```

Check the attribute names of the factory `AssignmentRule` (`variable`, `value`) with `rg -n "self\.(variable|value)" src/sbmlutils/factory/core_elements.py` and adapt.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/pytest -q -x tests/interpolation/test_assignment_rules.py`
Expected: FAIL, `AttributeError: 'Interpolation' object has no attribute 'assignment_rules'`.

- [ ] **Step 3: Implement**

```python
    def assignment_rules(
        self, targets: Mapping[str, str] | None = None
    ) -> list[AssignmentRule]:
        """The interpolation as assignment rules of a model definition.

        A model definition of `sbmlutils.factory` takes them with
        `model.rules += interpolation.assignment_rules(...)`; it declares the
        driven elements itself, non constant and with their units.

        Args:
            targets: the column which drives an element, to the id of the
                element; `None` for every column driving the element of its
                own id

        Returns:
            One `AssignmentRule` per driven element.

        Raises:
            ValueError: for a column which is not in the data, two columns
                driving one element or a target which is not an SBML id.
        """
        driven = _driving.resolve_targets(self.interpolators, self.xid, targets)
        return [
            AssignmentRule(target, interpolator.formula())
            for target, interpolator in driven.items()
        ]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest -q -x tests/interpolation/`
Expected: PASS

- [ ] **Step 5: Lint, type check, commit**

```bash
.venv/bin/ruff check -q src tests && .venv/bin/ruff format -q src tests && uvx ty check
git add src/sbmlutils/data/interpolation.py tests/interpolation/test_assignment_rules.py
git commit -m "Interpolations as assignment rules of a model definition (#16)"
```

---

### Task 7: Examples of driving a model with data

**Files:**
- Create: `examples/interpolation/driving.py`, `examples/interpolation/glucose_timecourse.tsv`
- Modify: `examples/interpolation/pancreas.py`, `tests/examples/test_example_scripts.py`

**Interfaces:**
- Consumes: `Interpolation.from_tsv`, `drive`, `drive_comp`, `sbmlutils.comp.flatten_sbml`.
- Produces: `examples.interpolation.driving.driving_example(directory: Path) -> Figure`; `examples.interpolation.pancreas.interpolate_data(...)` keeps its signature.

- [ ] **Step 1: Add the example to the tested scripts (failing test)**

In `tests/examples/test_example_scripts.py` add `"examples.interpolation.driving"` to `SCRIPTS` (sorted) and to the set of modules which need roadrunner.

Run: `.venv/bin/pytest -q -x tests/examples/test_example_scripts.py -k driving`
Expected: FAIL, `No module named examples.interpolation.driving`.

- [ ] **Step 2: Write the data and the example**

`examples/interpolation/glucose_timecourse.tsv` (tab separated):

```text
time	glc_ext
0	5.0
10	5.3
20	7.4
30	9.1
45	8.7
60	7.8
90	6.4
120	5.7
180	5.2
240	5.0
```

`examples/interpolation/driving.py`:

```python
"""Drive a model with measured data, in place and through comp.

A model of glucose uptake has the external glucose `glc_ext` as a species. The
measured plasma glucose of `glucose_timecourse.tsv` drives it: once in place,
which changes the model, and once through a comp model, which leaves the model
untouched and holds the data on top of it. Both are simulated with roadrunner
and simulate the same.

Run it from the root of the repository:

```bash
python -m examples.interpolation.driving
```

The models and the figure are written into the current working directory.
"""

import logging
from pathlib import Path

import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Axes, Figure

from sbmlutils.comp import flatten_sbml
from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import (
    Compartment,
    Model,
    Parameter,
    Reaction,
    Species,
    create_model,
)
from sbmlutils.validation import ValidationOptions

logger = logging.getLogger(__name__)

#: the measured data, next to this module
DATA_PATH: Path = Path(__file__).parent / "glucose_timecourse.tsv"

#: glucose uptake from the plasma into the liver and its use there
model = Model(
    "uptake",
    name="glucose uptake",
    compartments=[Compartment("plasma", 1.0), Compartment("liver", 0.5)],
    species=[
        Species("glc_ext", initialConcentration=5.0, compartment="plasma"),
        Species("glc", initialConcentration=5.0, compartment="liver"),
    ],
    parameters=[Parameter("Vmax", 2.0), Parameter("Km", 5.0), Parameter("k_use", 0.2)],
    reactions=[
        Reaction("GLCIM", "glc_ext -> glc", formula="Vmax * glc_ext / (Km + glc_ext)"),
        Reaction("GLCUSE", "glc -> ", formula="k_use * glc"),
    ],
)


def driving_example(directory: Path) -> Figure:
    """Drive the uptake model with the measured glucose, in place and via comp.

    Args:
        directory: where the models are written

    Returns:
        The figure of the data and both simulations; nothing is shown.
    """
    model_path = directory / "uptake.xml"
    create_model(
        model, filepath=model_path, validation_options=ValidationOptions(units_consistency=False)
    )
    interpolation = Interpolation.from_tsv(DATA_PATH, method="cubic spline")

    # (A) in place: the model itself is changed
    in_place = directory / "uptake_driven.xml"
    interpolation.drive(model_path, filepath=in_place)

    # (B) comp: a model on top of the untouched original, flattened to simulate
    comp = directory / "uptake_driven_comp.xml"
    interpolation.drive_comp(model_path, filepath=comp)
    flat = directory / "uptake_driven_flat.xml"
    flatten_sbml(comp, flat)

    data = interpolation.data
    f: Figure
    ax: Axes
    f, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(data["time"], data["glc_ext"], "o", color="black", label="glc_ext data")
    for path, glc, style, label in [
        (in_place, "[glc]", "-", "in place"),
        (flat, "[uptake__glc]", "--", "comp"),
    ]:
        r = roadrunner.RoadRunner(str(path))
        s = r.simulate(0, 240, 241, selections=["time", "[glc_ext]", glc])
        ax.plot(s["time"], s["[glc_ext]"], style, color="tab:blue", label=f"glc_ext {label}")
        ax.plot(s["time"], s[glc], style, color="tab:red", label=f"glc {label}")
    ax.set_xlabel("time [min]")
    ax.set_ylabel("glucose [mM]")
    ax.set_title("Glucose uptake driven by measured plasma glucose")
    ax.legend()
    return f


if __name__ == "__main__":
    from sbmlutils import log

    log.enable_rich_logging()

    figure = driving_example(Path.cwd())
    figure_path = Path.cwd() / "driving.png"
    figure.savefig(figure_path, bbox_inches="tight", dpi=150)
    logger.info("Figure written to '%s'", figure_path)
```

- [ ] **Step 3: Rework `pancreas.py` around `drive`**

Replace `interpolate_data` so that it builds a model with the parameters `xid_model` (constant) and `yid_model` (non constant), drives `yid_model` with `interpolation.drive(model_path, filepath=driven)` per method, scans `xid_model` with roadrunner (`r[xid_model] = value; r[yid_model]` read after `r.resetAll()` is not needed, the assignment rule is evaluated on reading) and plots every method once (one line per method, drop the duplicated dashed line). Keep the `__main__` block and the figure name `interpolation_pancreas.png`; the commented out second call is removed. The model is written with `create_model` into a `tempfile.TemporaryDirectory()`.

- [ ] **Step 4: Run the examples**

Run: `.venv/bin/pytest -q -x tests/examples/test_example_scripts.py -k interpolation`
Expected: PASS. Then run `python -m examples.interpolation.driving` in the scratchpad directory and look at `driving.png`: both simulations lie on top of each other, `glc_ext` goes through the data points, the curves are labelled.

- [ ] **Step 5: Lint, type check, commit**

```bash
.venv/bin/ruff check -q examples tests && .venv/bin/ruff format -q examples tests && uvx ty check
git add examples/interpolation tests/examples/test_example_scripts.py
git commit -m "Examples: drive a model with measured data, in place and via comp (#16)"
```

---

### Task 8: The guide, its tested code, CLAUDE.md and release notes

**Files:**
- Modify: `docs/interpolation.md`, `CLAUDE.md`
- Create: `tests/interpolation/test_interpolation_docs.py`, `release-notes/0.16.0.md`

**Interfaces:**
- Consumes: the whole public API of Tasks 1 to 6.

- [ ] **Step 1: Write the test of the guide**

```python
"""The python code blocks of the guide `docs/interpolation.md` run."""

import re
from pathlib import Path

import pytest

GUIDE = Path(__file__).parent.parent.parent / "docs" / "interpolation.md"


def test_guide_code_blocks_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The blocks run in order, in one namespace, in a temporary directory."""
    pytest.importorskip("roadrunner")
    blocks = re.findall(r"```python\n(.*?)```", GUIDE.read_text(), flags=re.DOTALL)
    assert len(blocks) >= 6
    monkeypatch.chdir(tmp_path)
    namespace: dict[str, object] = {}
    for block in blocks:
        exec(compile(block, str(GUIDE), "exec"), namespace)  # noqa: S102
```

Run: `.venv/bin/pytest -q -x tests/interpolation/test_interpolation_docs.py`
Expected: FAIL (`assert 4 >= 6`, or a block uses the removed API).

- [ ] **Step 2: Rewrite the guide**

`docs/interpolation.md`, every paragraph one line, sections in this order, each code block complete and run by the test in order:

1. `# Interpolation`: data drives a model; the three ways (standalone, in place, comp) and the factory, one sentence each.
2. `## From a data frame`: the existing data frame block, writing the standalone model; the first column is x (`time` or a quantity of the model), every other column a parameter with a port and an assignment rule; L3V2.
3. `## From a file`: a block which writes `data` with `data.to_csv("data.csv", index=False)` and reads it with `Interpolation.from_csv("data.csv", method="linear")`; `from_tsv`.
4. `## The methods`: the table of the methods (as today), then: all go through the data points, outside the data the first value is held before and the last value after it (all methods); the checks which raise a `ValueError` (fewer than 2 columns, column names which are not strings or repeat, a first column which is not an SBML id, a column which is not numeric, a missing or infinite value, x which repeats, fewer than 2 points or 3 for the spline); unsorted data is sorted with a warning.
5. `## Driving a model in place`: a block creating the uptake model of `examples/interpolation/driving.py` with `create_model("uptake.xml")`, a block with the time course data frame (`time`, `glc_ext`) and `interpolation.drive("uptake.xml", filepath=Path("uptake_driven.xml"))`, a block simulating it with roadrunner (`[glc_ext]` follows the data). Then the contract as a list: what can be driven (parameter, species, compartment) and what becomes of it; the data in the units of the target; a species in concentration or amount by `hasOnlySubstanceUnits`; `targets` for other column names; x a quantity of the model (a block: `pd.DataFrame({"Km": [...], "Vmax": [...]})` driving `Vmax` by `Km`); what raises (a rule or event assignment on the target, a missing x, two columns for one target) and that an initial assignment is removed.
6. `## Driving a model through comp`: a block with `interpolation.drive_comp("uptake.xml", filepath=Path("uptake_driven_comp.xml"))` and `flatten_sbml` and a roadrunner simulation of the flat model; the structure (top model `uptake_driven`, submodel `uptake`, placeholders of the class of the target, x replaced by the original's x, ports used when declared), the ids after flattening (`uptake__glc`, the driven ids unchanged), the relative reference and `embed=True`, Level 3 only, the initial assignment with metaid deleted.
7. `## In a model definition`: a block with a factory model declaring `Parameter("f", 1.0, constant=False)` and `model.rules += interpolation.assignment_rules({"f_data": "f"})`, written with `create_model`.
8. `## Examples`: `python -m examples.interpolation.interpolation`, `python -m examples.interpolation.driving`, `python -m examples.interpolation.pancreas`; each writes its figure into the working directory.

- [ ] **Step 3: Run the guide test**

Run: `.venv/bin/pytest -q -x tests/interpolation/test_interpolation_docs.py`
Expected: PASS. Build the documentation: `.venv/bin/zensical build --clean 2>&1 | grep -iE "warn|error"` prints nothing.

- [ ] **Step 4: CLAUDE.md and release notes**

Replace the paragraph `**`data/interpolation.py`**` of `CLAUDE.md` by:

```markdown
**`data/interpolation.py`, `data/_driving.py` - data driving a model.** `Interpolation` turns a table of data points into assignment rules which evaluate a constant, linear or natural cubic spline interpolation of every column against the first (x: `time` or a quantity of the model), holding the first and the last value outside the data. The rules make a standalone model (L3V2, written through the factory, every interpolated parameter with a port), drive a parameter, species or compartment of an existing model in place (`drive`) or through a comp model whose top model holds the rules and replaces the targets of the untouched original by placeholders of their class (`drive_comp`, comp requires a replacement of the class of what it replaces except for a parameter), or go into a model definition (`assignment_rules`). `_driving.py` checks the targets before anything changes, so a refused call leaves the document as it was.
```

`release-notes/0.16.0.md`:

```markdown
# Release notes for sbmlutils 0.16.0
![sbmlutils](https://github.com/matthiaskoenig/sbmlutils/raw/develop/docs/images/sbmlutils-logo-60.png)

We are pleased to release the next version of sbmlutils including the following changes. Measured data drives a model: an interpolation of the data replaces quantities of an existing model in place, through a comp model which leaves the original untouched, or in a model definition (#16).

## New features
- `Interpolation.drive` drives a parameter, species or compartment of an existing model with the interpolated data, in place; x is the time or a quantity of the model (#16)
- `Interpolation.drive_comp` drives a model through a comp model which references the original, or embeds it with `embed=True`; flattened it simulates as the model driven in place (#16)
- `Interpolation.assignment_rules` gives the interpolation as assignment rules of a model definition (#16)

## Breaking changes
- linear and cubic spline interpolation hold the first value before and the last value after the data, instead of `0.0` (#16)
- data which cannot be interpolated raises a `ValueError` instead of a warning: fewer than 2 columns or data points (3 for the cubic spline), column names which are not strings or repeat, a first column which is not an SBML id, a column which is not numeric, a missing or infinite value, x which repeats (#16)
- `Interpolation.add_interpolator_to_model` is removed, `drive` replaces it; `Interpolation.create_interpolators` is the property `Interpolation.interpolators`; the attributes `doc` and `model` of an `Interpolation` are removed (#16)
- the standalone model of an interpolation is SBML L3V2 with a port on every interpolated parameter and on x (#16)

## Documentation
- the guide [Interpolation](https://matthiaskoenig.github.io/sbmlutils/interpolation/) covers driving a model in place, via comp and in a model definition, its code is run by the tests; the example `examples.interpolation.driving` drives a model of glucose uptake with measured plasma glucose, `examples.interpolation.pancreas` drives a dose response (#16)
```

- [ ] **Step 5: Full verification and commit**

```bash
.venv/bin/pytest -q -x
.venv/bin/ruff check -q --extend-exclude .ode_tmp && .venv/bin/ruff format --check -q --extend-exclude .ode_tmp && uvx ty check
git add docs/interpolation.md tests/interpolation/test_interpolation_docs.py CLAUDE.md release-notes/0.16.0.md
git commit -m "Guide of driving a model with data, tested; release notes (#16)"
```
