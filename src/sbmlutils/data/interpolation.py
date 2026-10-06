"""Interpolation of data points, as a model of its own or driving a model.

A table of data points becomes assignment rules which evaluate a constant,
linear or natural cubic spline interpolation of every column against the
first. The rules make a standalone model (`Interpolation.write_sbml_to_file`),
drive the quantities of an existing model in place (`Interpolation.drive`) or
through a comp model which leaves the original untouched
(`Interpolation.drive_comp`), or go into a model definition of the factory
(`Interpolation.assignment_rules`). See the guide `docs/interpolation.md`.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path

import libsbml
import numpy as np
import pandas as pd

from sbmlutils.data import _driving
from sbmlutils.factory import AssignmentRule, Document, Model, Package, Parameter
from sbmlutils.io.sbml import write_sbml
from sbmlutils.validation import ValidationOptions, validate_doc

logger = logging.getLogger(__name__)


class InterpolationMethod(StrEnum):
    """Available interpolation methods.

    The members are strings, so the plain value (`"linear"`) is accepted and
    compares equal wherever a method is expected.
    """

    CONSTANT = "constant"
    LINEAR = "linear"
    CUBIC_SPLINE = "cubic spline"


# aliases of the methods, kept for backwards compatibility
INTERPOLATION_CONSTANT = InterpolationMethod.CONSTANT
INTERPOLATION_LINEAR = InterpolationMethod.LINEAR
INTERPOLATION_CUBIC_SPLINE = InterpolationMethod.CUBIC_SPLINE


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

    def __str__(self) -> str:
        """Convert to string."""
        return (
            "--------------------------\n"
            f"Interpolator<{self.method}>\n"
            "--------------------------\n"
            f"{self.x}\n"
            f"{self.y}\n"
            f"formula:\n {self.formula()}\n"
        )

    @property
    def xid(self) -> str:
        """X id."""
        return str(self.x.name)

    @property
    def yid(self) -> str:
        """Y id."""
        return str(self.y.name)

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
        # a negative number is a number, not the unary minus of a positive one
        settings = libsbml.L3ParserSettings()
        settings.setParseCollapseMinus(True)
        ast: libsbml.ASTNode | None = libsbml.parseL3FormulaWithSettings(
            self.formula(), settings
        )
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

    @staticmethod
    def _natural_spline_coeffs(
        X: pd.Series, Y: pd.Series
    ) -> list[tuple[float, float, float, float]]:
        """Calculate natural spline coefficients.

        Calculation of coefficients for
            di*(x - xi)^3 + ci*(x - xi)^2 + bi*(x - xi) + ai
        for x in [xi, xi+1]

        Natural splines use a fixed second derivative, such that S''(x0)=S''(xn)=0,
        whereas clamped splines use fixed bounding conditions for S(x) at x0 and xn.

        A trig-diagonal matrix is constructed which can be efficiently solved.

        Equations and derivation from:
        https://jayemmcee.wordpress.com/cubic-splines/
        http://pastebin.com/EUs31Hvh

        :return:
        :rtype:
        """
        np1 = len(X)
        n = np1 - 1
        a = Y.reset_index(drop=True)
        X = X.reset_index(drop=True)
        b = [0.0] * n
        d = [0.0] * n
        h = [X[i + 1] - X[i] for i in range(n)]
        alpha = [0.0] * n
        for i in range(1, n):
            alpha[i] = 3 / h[i] * (a[i + 1] - a[i]) - 3 / h[i - 1] * (a[i] - a[i - 1])
        c = [0.0] * np1
        L = [0.0] * np1
        u = [0.0] * np1
        z = [0.0] * np1
        L[0] = 1.0
        u[0] = z[0] = 0.0
        for i in range(1, n):
            L[i] = 2 * (X[i + 1] - X[i - 1]) - h[i - 1] * u[i - 1]
            u[i] = h[i] / L[i]
            z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / L[i]
        L[n] = 1.0
        z[n] = c[n] = 0.0
        for j in range(n - 1, -1, -1):
            c[j] = z[j] - u[j] * c[j + 1]
            b[j] = (a[j + 1] - a[j]) / h[j] - (h[j] * (c[j + 1] + 2 * c[j])) / 3
            d[j] = (c[j + 1] - c[j]) / (3 * h[j])
        # store coefficients
        coeffs: list[tuple[float, float, float, float]] = [
            (a[i], b[i], c[i], d[i]) for i in range(n)
        ]
        return coeffs


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

    # --- SBML & Interpolation --------------------

    def write_sbml_to_file(self, sbml_out: Path) -> None:
        """Write the SBML file.

        :param sbml_out: Path to SBML file
        :return:
        """
        write_sbml(doc=self._create_sbml(), filepath=sbml_out)

    def write_sbml_to_string(self) -> str | None:
        """Write the SBML file.

        :return: SBML str
        """
        return write_sbml(self._create_sbml(), filepath=None)

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
