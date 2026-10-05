"""The python dialect of the math printer.

The expressions use `numpy` as `np` and `math`, the time is `t`. A condition is a
python `bool` (a numpy bool is no number, the sum of two numpy bools is their logical
or), which is a `float` where it is used as a number. A `piecewise` is a conditional
expression, which evaluates only the value of the piece which applies.
"""

import math
from collections.abc import Mapping, Sequence
from typing import ClassVar

import libsbml

from sbmlutils.converters.ode.printers.base import MathPrinter, Precedence, Printed


class PythonPrinter(MathPrinter):
    """Printer of SBML math as a python expression with numpy."""

    name: ClassVar[str] = "python"
    MODULES: ClassVar[frozenset[str]] = frozenset({"np", "math"})
    FUNCTIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ABS: "np.abs",
        libsbml.AST_FUNCTION_ARCCOS: "np.arccos",
        libsbml.AST_FUNCTION_ARCCOSH: "np.arccosh",
        libsbml.AST_FUNCTION_ARCSIN: "np.arcsin",
        libsbml.AST_FUNCTION_ARCSINH: "np.arcsinh",
        libsbml.AST_FUNCTION_ARCTAN: "np.arctan",
        libsbml.AST_FUNCTION_ARCTANH: "np.arctanh",
        libsbml.AST_FUNCTION_CEILING: "np.ceil",
        libsbml.AST_FUNCTION_COS: "np.cos",
        libsbml.AST_FUNCTION_COSH: "np.cosh",
        libsbml.AST_FUNCTION_EXP: "np.exp",
        libsbml.AST_FUNCTION_FLOOR: "np.floor",
        libsbml.AST_FUNCTION_LN: "np.log",
        libsbml.AST_FUNCTION_MAX: "max",
        libsbml.AST_FUNCTION_MIN: "min",
        libsbml.AST_FUNCTION_SIN: "np.sin",
        libsbml.AST_FUNCTION_SINH: "np.sinh",
        libsbml.AST_FUNCTION_TAN: "np.tan",
        libsbml.AST_FUNCTION_TANH: "np.tanh",
    }
    CONSTANTS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_CONSTANT_E: "np.e",
        libsbml.AST_CONSTANT_PI: "np.pi",
        libsbml.AST_CONSTANT_TRUE: "True",
        libsbml.AST_CONSTANT_FALSE: "False",
        libsbml.AST_NAME_TIME: "t",
    }

    # the function whose reciprocal a function is, sec(x) = 1/cos(x)
    RECIPROCALS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_SEC: "np.cos",
        libsbml.AST_FUNCTION_CSC: "np.sin",
        libsbml.AST_FUNCTION_COT: "np.tan",
        libsbml.AST_FUNCTION_SECH: "np.cosh",
        libsbml.AST_FUNCTION_CSCH: "np.sinh",
        libsbml.AST_FUNCTION_COTH: "np.tanh",
    }

    # the function of the reciprocal a function is, arcsec(x) = arccos(1/x)
    OF_RECIPROCALS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ARCSEC: "np.arccos",
        libsbml.AST_FUNCTION_ARCCSC: "np.arcsin",
        libsbml.AST_FUNCTION_ARCCOT: "np.arctan",
        libsbml.AST_FUNCTION_ARCSECH: "np.arccosh",
        libsbml.AST_FUNCTION_ARCCSCH: "np.arcsinh",
        libsbml.AST_FUNCTION_ARCCOTH: "np.arctanh",
    }

    def number(self, value: float) -> str:
        """Python literal of a float, `np.inf` and `np.nan` included."""
        if math.isnan(value):
            return "np.nan"
        if math.isinf(value):
            return "np.inf" if value > 0 else "-np.inf"
        return repr(float(value))

    def power(self, base: Printed, exponent: Printed) -> Printed:
        """`a ** b`, which binds tighter than a unary minus on its left.

        The operands of the generated code are numpy scalars, whose power is `nan`
        for a negative base and a fractional exponent and `inf` for `0 ** -1`, as
        in SBML; a power of python numbers alone (of literals) is a complex number
        or raises there.
        """
        code = f"{self.wrap(base, Precedence.ATOM)} ** {self.wrap(exponent, Precedence.UNARY)}"
        return Printed(code, Precedence.POWER)

    def piecewise(
        self, pieces: Sequence[tuple[Printed, Printed]], otherwise: Printed | None
    ) -> Printed:
        """`x if c else y`, nested in the `else`, `np.nan` without an otherwise."""
        piece = Precedence.CONDITIONAL + 1
        code = (
            self.wrap(otherwise, Precedence.CONDITIONAL)
            if otherwise is not None
            else self.number(math.nan)
        )
        for value, condition in reversed(pieces):
            code = f"{self.wrap(value, piece)} if {self.wrap(condition, piece)} else {code}"
        return Printed(code, Precedence.CONDITIONAL)

    def rem(self, dividend: Printed, divisor: Printed) -> Printed:
        """`np.fmod`, which has the sign of the dividend."""
        return self.call("np.fmod", [dividend, divisor])

    def quotient(self, dividend: Printed, divisor: Printed) -> Printed:
        """`np.trunc(a / b)`."""
        return self.call("np.trunc", [self.divide(dividend, divisor)])

    def log(self, base: Printed | None, value: Printed) -> Printed:
        """`np.log10(x)` or `np.log(x) / np.log(b)`."""
        if base is None:
            return self.call("np.log10", [value])
        return self.divide(self.call("np.log", [value]), self.call("np.log", [base]))

    def root(self, degree: Printed | None, value: Printed) -> Printed:
        """`np.sqrt(x)` or `x ** (1.0 / n)`."""
        if degree is None:
            return self.call("np.sqrt", [value])
        return self.power(value, self.divide(self._one(), degree))

    def factorial(self, value: Printed) -> Printed:
        """`math.gamma(x + 1)`, the gamma function extends the factorial to the reals."""
        return self.call(
            "math.gamma",
            [self.infix([value, self._integer(1)], self.PLUS, Precedence.SUM)],
        )

    def logic_and(self, operands: Sequence[Printed]) -> Printed:
        """`a and b`."""
        return self.infix(operands, " and ", Precedence.AND)

    def logic_or(self, operands: Sequence[Printed]) -> Printed:
        """`a or b`."""
        return self.infix(operands, " or ", Precedence.OR)

    def logic_xor(self, operands: Sequence[Printed]) -> Printed:
        """`bool(a) ^ bool(b)`, the exclusive or of python bools."""
        code = " ^ ".join(f"bool({operand.code})" for operand in operands)
        return Printed(code, Precedence.XOR)

    def logic_not(self, operand: Printed) -> Printed:
        """`not a`."""
        return Printed(f"not {self.wrap(operand, Precedence.NOT)}", Precedence.NOT)

    def logic_implies(self, premise: Printed, conclusion: Printed) -> Printed:
        """`not a or b`."""
        return self.logic_or([self.logic_not(premise), conclusion])

    def bool_to_number(self, condition: Printed) -> Printed:
        """`float(c)`, so that a condition is a number in arithmetic."""
        return self.call("float", [condition])
