"""Create files for interpolation of datasets.

https://github.com/allyhume/SBMLDataTools
https://github.com/allyhume/SBMLDataTools.git

TODO: fix composition with existing models
TODO: support coupling with existing models via comp
The functionality is very useful, but only if this can be applied to existing
models in a simple manner.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path

import libsbml
import numpy as np
import pandas as pd

from sbmlutils.io.sbml import write_sbml
from sbmlutils.validation import ValidationOptions, check, validate_doc

logger = logging.getLogger(__name__)


notes = libsbml.XMLNode.convertStringToXMLNode(
    """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Data interpolator</h1>
    <h2>Description</h2>
    <p>This is a SBML submodel for interpolation of spreadsheet data.</p>

    <div class="dc:publisher">This file has been produced by
      <a href="https://livermetabolism.com/contact.html" title="Matthias Koenig" target="_blank">Matthias Koenig</a>.
      </div>

    <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2016-2020 sbmlutils.</div>
      <div class="dc:license">
      <p>Redistribution and use of any part of this model, with or without modification, are permitted provided that
      the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions
              and the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of
              conditions and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>
        This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
             the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.</p>
      </div>
    </body>
"""
)


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
    """Create SBML model which interpolates the given data.

    The second to last components are interpolated against the first component.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        method: InterpolationMethod | str = InterpolationMethod.LINEAR,
    ):
        """Initialize Interpolation.

        Raises:
            ValueError: If the method is not an interpolation method.
        """
        self.doc: libsbml.SBMLDocument | None = None
        self.model: libsbml.Model | None = None
        self.data: pd.DataFrame = data
        self.method: InterpolationMethod = InterpolationMethod(method)
        self.interpolators: list[Interpolator] = []

        self.validate_data()

    def validate_data(self) -> None:
        """Validate the input data.

        * The data is expected to have at least 2 columns.
        * The data is expected to have at least three data rows.
        * The first column should be in ascending order.

        :return:
        :rtype:
        """
        # more than 1 column required
        if len(self.data.columns) < 2:
            logger.warning(
                "Interpolation data has <2 columns. At least 2 columns required."
            )

        # at least 3 rows required
        if len(self.data) < 3:
            logger.warning("Interpolation data <3 rows. At least 3 rows required.")

        # first column has to be ascending (times)
        def is_sorted(df: pd.DataFrame, colname: str) -> bool:
            return bool(pd.Index(df[colname]).is_monotonic_increasing)

        if not is_sorted(self.data, colname=self.data.columns[0]):
            logger.warning("First column should contain ascending values.")
            self.data = self.data.sort_values(by=self.data.columns[0]).reset_index(
                drop=True
            )

    @staticmethod
    def from_csv(
        csv_file: Path | str, method: str = "linear", sep: str = ","
    ) -> Interpolation:
        """Interpolation object from csv file."""
        data: pd.DataFrame = pd.read_csv(csv_file, sep=sep)
        return Interpolation(data=data, method=method)

    @staticmethod
    def from_tsv(tsv_file: Path | str, method: str = "linear") -> Interpolation:
        """Interpolate object from tsv file."""
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
        """Create the SBMLDocument.

        Returns:
            The document with the interpolation model.
        """
        doc, model = self._init_sbml_model()
        self.interpolators = Interpolation.create_interpolators(self.data, self.method)
        for interpolator in self.interpolators:
            Interpolation.add_interpolator_to_model(interpolator, model)

        # validation of SBML document
        validate_doc(doc, options=ValidationOptions(units_consistency=False))
        return doc

    def _init_sbml_model(self) -> tuple[libsbml.SBMLDocument, libsbml.Model]:
        """Create and initialize the SBML model.

        Returns:
            The document and its model.
        """
        # FIXME: support arbitrary levels and versions
        sbmlns = libsbml.SBMLNamespaces(3, 1)
        sbmlns.addPackageNamespace("comp", 1)
        doc: libsbml.SBMLDocument = libsbml.SBMLDocument(sbmlns)
        doc.setPackageRequired("comp", True)
        self.doc = doc
        model: libsbml.Model = doc.createModel()

        model.setNotes(notes)
        # the method can contain spaces ("cubic spline"), which an SId does not allow
        model_id = f"Interpolation_{self.method}".replace(" ", "_")
        check(model.setId(model_id), f"set model id '{model_id}'")
        model.setName(f"Interpolation_{self.method}")
        self.model = model
        return doc, model

    @staticmethod
    def create_interpolators(
        data: pd.DataFrame, method: InterpolationMethod | str
    ) -> list[Interpolator]:
        """Create all interpolators for the given data set.

        The columns 1, ... (Ncol-1) are interpolated against
        column 0.
        """
        interpolators: list[Interpolator] = []
        columns = data.columns
        x = data[columns[0]]
        for k in range(1, len(columns)):
            interpolator = Interpolator(x=x, y=data[columns[k]], method=method)
            interpolators.append(interpolator)
        return interpolators

    @staticmethod
    def add_interpolator_to_model(
        interpolator: Interpolator, model: libsbml.Model
    ) -> None:
        """Add interpolator to model.

        The parameters, formulas and rules have to be added to the SBML model.

        :param interpolator:
        :param model: Model
        :return:
        """
        # FIXME: use the sbmlutils structure for addition

        # add xid if needed
        xid = interpolator.xid
        xobj = model.getElementBySId(xid)
        # the time of the simulation is the csymbol, it must not be shadowed by a parameter
        if not xobj and xid != "time":
            px: libsbml.Parameter = model.createParameter()
            px.setId(xid)
            px.setName(xid)
            px.setConstant(True)
            px.setValue(interpolator.x.values[0])

        # create parameter
        pid = interpolator.yid

        # if parameter exists remove it
        if model.getParameter(pid):
            logger.warning("Model contains parameter: %s. Parameter is removed.", pid)
            model.removeParameter(pid)

        # if assignment rule exists remove it
        for rule in model.getListOfRules():
            if rule.isAssignment() and rule.getVariable() == pid:
                model.removeRule(rule)
                break

        p = model.createParameter()
        p.setId(pid)
        p.setName(pid)
        p.setConstant(False)

        # create rule
        rule = model.createAssignmentRule()
        rule.setVariable(pid)
        formula = interpolator.formula()
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            logger.warning(libsbml.getLastParseL3Error())
        else:
            rule.setMath(ast_node)

            # TODO: add ports for connection with other model
