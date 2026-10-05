"""The R dialect of the math printer.

The expressions use base R only, the time is `t`. The numbers of R are doubles, so
a number is written as plain as it reads, `2`, `0.5`. A condition is a logical of
length one, which is `as.numeric` where it is used as a number. A relation with
`NaN` is `NA` in R, which is neither a condition of `if` nor a number; a relation is
therefore `isTRUE(a > b)`, which is `FALSE` for `NA` as in IEEE 754 (and python
and julia), `a != b` is `!isTRUE(a == b)`, which holds for `NaN`. A `piecewise` is an
`if (c) x else y` expression, which evaluates only the value of the piece which
applies; it takes everything up to its end, so it is in parentheses as an operand.
"""

import math
from collections.abc import Mapping, Sequence
from functools import reduce
from typing import ClassVar

import libsbml

from sbmlutils.converters.ode.printers.base import MathPrinter, Precedence, Printed


class RPrinter(MathPrinter):
    """Printer of SBML math as an R expression."""

    name: ClassVar[str] = "r"
    FUNCTIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ABS: "abs",
        libsbml.AST_FUNCTION_ARCCOS: "acos",
        libsbml.AST_FUNCTION_ARCCOSH: "acosh",
        libsbml.AST_FUNCTION_ARCSIN: "asin",
        libsbml.AST_FUNCTION_ARCSINH: "asinh",
        libsbml.AST_FUNCTION_ARCTAN: "atan",
        libsbml.AST_FUNCTION_ARCTANH: "atanh",
        libsbml.AST_FUNCTION_CEILING: "ceiling",
        libsbml.AST_FUNCTION_COS: "cos",
        libsbml.AST_FUNCTION_COSH: "cosh",
        libsbml.AST_FUNCTION_EXP: "exp",
        libsbml.AST_FUNCTION_FLOOR: "floor",
        libsbml.AST_FUNCTION_LN: "log",
        libsbml.AST_FUNCTION_MAX: "max",
        libsbml.AST_FUNCTION_MIN: "min",
        libsbml.AST_FUNCTION_SIN: "sin",
        libsbml.AST_FUNCTION_SINH: "sinh",
        libsbml.AST_FUNCTION_TAN: "tan",
        libsbml.AST_FUNCTION_TANH: "tanh",
    }
    CONSTANTS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_CONSTANT_E: "exp(1)",
        libsbml.AST_CONSTANT_PI: "pi",
        libsbml.AST_CONSTANT_TRUE: "TRUE",
        libsbml.AST_CONSTANT_FALSE: "FALSE",
        libsbml.AST_NAME_TIME: "t",
    }
    RECIPROCALS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_SEC: "cos",
        libsbml.AST_FUNCTION_CSC: "sin",
        libsbml.AST_FUNCTION_COT: "tan",
        libsbml.AST_FUNCTION_SECH: "cosh",
        libsbml.AST_FUNCTION_CSCH: "sinh",
        libsbml.AST_FUNCTION_COTH: "tanh",
    }
    OF_RECIPROCALS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ARCSEC: "acos",
        libsbml.AST_FUNCTION_ARCCSC: "asin",
        libsbml.AST_FUNCTION_ARCCOT: "atan",
        libsbml.AST_FUNCTION_ARCSECH: "acosh",
        libsbml.AST_FUNCTION_ARCCSCH: "asinh",
        libsbml.AST_FUNCTION_ARCCOTH: "atanh",
    }

    def number(self, value: float) -> str:
        """R literal of a double, `2`, `0.5`, `1e-05`, `Inf` and `NaN` included."""
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Inf" if value > 0 else "-Inf"
        return repr(float(value)).removesuffix(".0")

    def power(self, base: Printed, exponent: Printed) -> Printed:
        """`a ^ b`, a negative exponent in parentheses, `a ^ (-b)`."""
        code = f"{self.wrap(base, Precedence.ATOM)} ^ {self.wrap(exponent, Precedence.POWER)}"
        return Printed(code, Precedence.POWER)

    def piecewise(
        self, pieces: Sequence[tuple[Printed, Printed]], otherwise: Printed | None
    ) -> Printed:
        """`if (c) x else y`, nested in the `y`, `NaN` without an otherwise."""
        piece = Precedence.CONDITIONAL + 1
        code = (
            self.wrap(otherwise, Precedence.CONDITIONAL)
            if otherwise is not None
            else self.number(math.nan)
        )
        for value, condition in reversed(pieces):
            code = f"if ({condition.code}) {self.wrap(value, piece)} else {code}"
        return Printed(code, Precedence.CONDITIONAL)

    def rem(self, dividend: Printed, divisor: Printed) -> Printed:
        """`sign(a) * (abs(a) %% abs(b))`, the remainder of `fmod` as roadrunner.

        `%%` of R has the sign of the divisor, so it is applied to the absolute
        values and the sign of the dividend is put back. `a - b * trunc(a / b)`
        is not exact: it is `0` for `rem(1, 0.1)`, whose remainder is `0.1`.
        """
        modulo = Printed(
            f"{self.call('abs', [dividend]).code} %% {self.call('abs', [divisor]).code}",
            Precedence.PRODUCT,
        )
        return self.infix(
            [self.call("sign", [dividend]), modulo], self.TIMES, Precedence.PRODUCT
        )

    def quotient(self, dividend: Printed, divisor: Printed) -> Printed:
        """`trunc(a / b)`."""
        return self.call("trunc", [self.divide(dividend, divisor)])

    def log(self, base: Printed | None, value: Printed) -> Printed:
        """`log10(x)` or `log(x, b)`."""
        if base is None:
            return self.call("log10", [value])
        return self.call("log", [value, base])

    def root(self, degree: Printed | None, value: Printed) -> Printed:
        """`sqrt(x)` or `x ^ (1 / n)`."""
        if degree is None:
            return self.call("sqrt", [value])
        return self.power(value, self.divide(self._one(), degree))

    def factorial(self, value: Printed) -> Printed:
        """`gamma(x + 1)`, the gamma function extends the factorial to the reals."""
        return self.call(
            "gamma",
            [self.infix([value, self._integer(1)], self.PLUS, Precedence.SUM)],
        )

    def relation(self, relation: int, left: Printed, right: Printed) -> Printed:
        """`isTRUE(a > b)`, `!isTRUE(a == b)` for `a != b`, never `NA`."""
        if relation == libsbml.AST_RELATIONAL_NEQ:
            equal = super().relation(libsbml.AST_RELATIONAL_EQ, left, right)
            return self.logic_not(self.call("isTRUE", [equal]))
        return self.call("isTRUE", [super().relation(relation, left, right)])

    def logic_and(self, operands: Sequence[Printed]) -> Printed:
        """`a && b`."""
        return self.infix(operands, " && ", Precedence.AND)

    def logic_or(self, operands: Sequence[Printed]) -> Printed:
        """`a || b`."""
        return self.infix(operands, " || ", Precedence.OR)

    def logic_xor(self, operands: Sequence[Printed]) -> Printed:
        """`xor(xor(a, b), c)`, `xor` of R has two arguments."""
        return reduce(lambda left, right: self.call("xor", [left, right]), operands)

    def logic_not(self, operand: Printed) -> Printed:
        """`!(a)`, in parentheses although `!` binds weaker than a relation."""
        return Printed(f"!{self.wrap(operand, Precedence.UNARY)}", Precedence.NOT)

    def logic_implies(self, premise: Printed, conclusion: Printed) -> Printed:
        """`!a || b`."""
        return self.logic_or([self.logic_not(premise), conclusion])

    def bool_to_number(self, condition: Printed) -> Printed:
        """`as.numeric(c)`, so that a condition is a number in arithmetic."""
        return self.call("as.numeric", [condition])
