"""The julia dialect of the math printer.

The expressions use `Base` and `SpecialFunctions` (for `gamma`), the time is `t`.
Every number is a `Float64` literal, an integer of SBML included: the integer
arithmetic of julia overflows and a power of integers throws for a negative
exponent, so `2^-1` is written as `2.0 ^ (-1.0)`. A condition is a `Bool`, which is
a `Float64` where it is used as a number. A `piecewise` is a conditional expression
`c ? x : y`, which evaluates only the value of the piece which applies.
"""

import math
from collections.abc import Mapping, Sequence
from typing import ClassVar

import libsbml

from sbmlutils.converters.ode.printers.base import MathPrinter, Precedence, Printed


class JuliaPrinter(MathPrinter):
    """Printer of SBML math as a julia expression."""

    name: ClassVar[str] = "julia"
    FUNCTIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ABS: "abs",
        libsbml.AST_FUNCTION_ARCCOS: "acos",
        libsbml.AST_FUNCTION_ARCCOSH: "acosh",
        libsbml.AST_FUNCTION_ARCCOT: "acot",
        libsbml.AST_FUNCTION_ARCCOTH: "acoth",
        libsbml.AST_FUNCTION_ARCCSC: "acsc",
        libsbml.AST_FUNCTION_ARCCSCH: "acsch",
        libsbml.AST_FUNCTION_ARCSEC: "asec",
        libsbml.AST_FUNCTION_ARCSECH: "asech",
        libsbml.AST_FUNCTION_ARCSIN: "asin",
        libsbml.AST_FUNCTION_ARCSINH: "asinh",
        libsbml.AST_FUNCTION_ARCTAN: "atan",
        libsbml.AST_FUNCTION_ARCTANH: "atanh",
        libsbml.AST_FUNCTION_CEILING: "ceil",
        libsbml.AST_FUNCTION_COS: "cos",
        libsbml.AST_FUNCTION_COSH: "cosh",
        libsbml.AST_FUNCTION_COT: "cot",
        libsbml.AST_FUNCTION_COTH: "coth",
        libsbml.AST_FUNCTION_CSC: "csc",
        libsbml.AST_FUNCTION_CSCH: "csch",
        libsbml.AST_FUNCTION_EXP: "exp",
        libsbml.AST_FUNCTION_FLOOR: "floor",
        libsbml.AST_FUNCTION_LN: "log",
        libsbml.AST_FUNCTION_MAX: "max",
        libsbml.AST_FUNCTION_MIN: "min",
        libsbml.AST_FUNCTION_SEC: "sec",
        libsbml.AST_FUNCTION_SECH: "sech",
        libsbml.AST_FUNCTION_SIN: "sin",
        libsbml.AST_FUNCTION_SINH: "sinh",
        libsbml.AST_FUNCTION_TAN: "tan",
        libsbml.AST_FUNCTION_TANH: "tanh",
    }
    CONSTANTS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_CONSTANT_E: "exp(1.0)",
        libsbml.AST_CONSTANT_PI: "pi",
        libsbml.AST_CONSTANT_TRUE: "true",
        libsbml.AST_CONSTANT_FALSE: "false",
        libsbml.AST_NAME_TIME: "t",
    }

    def integer(self, value: int) -> str:
        """`Float64` literal of an integer, `2.0`."""
        return self.number(float(value))

    def number(self, value: float) -> str:
        """`Float64` literal as julia writes it, `1.0e-5`, `Inf` and `NaN`."""
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Inf" if value > 0 else "-Inf"
        mantissa, _, exponent = repr(float(value)).partition("e")
        if not exponent:
            return mantissa
        if "." not in mantissa:
            mantissa = f"{mantissa}.0"
        return f"{mantissa}e{int(exponent)}"

    def power(self, base: Printed, exponent: Printed) -> Printed:
        """`a ^ b`, a negative exponent in parentheses, `a ^ (-b)`."""
        code = f"{self.wrap(base, Precedence.ATOM)} ^ {self.wrap(exponent, Precedence.POWER)}"
        return Printed(code, Precedence.POWER)

    def piecewise(
        self, pieces: Sequence[tuple[Printed, Printed]], otherwise: Printed | None
    ) -> Printed:
        """`c ? x : y`, nested in the `y`, `NaN` without an otherwise."""
        piece = Precedence.CONDITIONAL + 1
        code = (
            self.wrap(otherwise, Precedence.CONDITIONAL)
            if otherwise is not None
            else self.number(math.nan)
        )
        for value, condition in reversed(pieces):
            code = f"{self.wrap(condition, piece)} ? {self.wrap(value, piece)} : {code}"
        return Printed(code, Precedence.CONDITIONAL)

    def rem(self, dividend: Printed, divisor: Printed) -> Printed:
        """`rem(a, b)`, which has the sign of the dividend."""
        return self.call("rem", [dividend, divisor])

    def quotient(self, dividend: Printed, divisor: Printed) -> Printed:
        """`trunc(a / b)`, the quotient of roadrunner.

        `div(a, b)` of julia is the exact truncated quotient, `div(1.0, 0.1)` is
        `9.0`, while roadrunner and the other dialects truncate the rounded
        quotient, `10.0`.
        """
        return self.call("trunc", [self.divide(dividend, divisor)])

    def log(self, base: Printed | None, value: Printed) -> Printed:
        """`log10(x)` or `log(b, x)`."""
        if base is None:
            return self.call("log10", [value])
        return self.call("log", [base, value])

    def root(self, degree: Printed | None, value: Printed) -> Printed:
        """`sqrt(x)` or `x ^ (1.0 / n)`."""
        if degree is None:
            return self.call("sqrt", [value])
        return self.power(value, self.divide(self._one(), degree))

    def factorial(self, value: Printed) -> Printed:
        """`gamma(x + 1.0)` of `SpecialFunctions`, which extends it to the reals."""
        return self.call(
            "gamma", [self.infix([value, self._one()], self.PLUS, Precedence.SUM)]
        )

    def logic_and(self, operands: Sequence[Printed]) -> Printed:
        """`a && b`."""
        return self.infix(operands, " && ", Precedence.AND)

    def logic_or(self, operands: Sequence[Printed]) -> Printed:
        """`a || b`."""
        return self.infix(operands, " || ", Precedence.OR)

    def logic_xor(self, operands: Sequence[Printed]) -> Printed:
        """`xor(a, b, c)`."""
        return self.call("xor", operands)

    def logic_not(self, operand: Printed) -> Printed:
        """`!(a)`, `!` binds tighter than a relation."""
        return Printed(f"!{self.wrap(operand, Precedence.UNARY)}", Precedence.NOT)

    def logic_implies(self, premise: Printed, conclusion: Printed) -> Printed:
        """`!a || b`."""
        return self.logic_or([self.logic_not(premise), conclusion])

    def bool_to_number(self, condition: Printed) -> Printed:
        """`Float64(c)`, so that a condition is a number in arithmetic."""
        return self.call("Float64", [condition])
