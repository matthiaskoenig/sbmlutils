"""The julia dialect of the math printer.

The expressions use `Base`, `NaNMath` and `SpecialFunctions` (for `gamma`), the
time is `t`. A function of `Base` throws a `DomainError` outside its real domain,
`sqrt(-1.0)`, `(-2.0)^0.5`, `log(-1.0)`, `acosh(0.5)`, `sin(Inf)`; there the
expressions use the function of `NaNMath`, which is `NaN` as in SBML. Every number
is a `Float64` literal, an integer of SBML included: the integer arithmetic of julia
overflows, `10^20`, and a power of integers throws for a negative exponent. A
condition is a `Bool`, which is a `Float64` where it is used as a number. A
`piecewise` is a conditional expression `c ? x : y`, which evaluates only the value
of the piece which applies.
"""

import math
from collections.abc import Mapping, Sequence
from typing import ClassVar

import libsbml

from sbmlutils.converters.ode.printers.base import MathPrinter, Precedence, Printed


class JuliaPrinter(MathPrinter):
    """Printer of SBML math as a julia expression."""

    name: ClassVar[str] = "julia"
    MODULES: ClassVar[frozenset[str]] = frozenset({"NaNMath"})
    IMPORTED: ClassVar[Mapping[str, str]] = {"gamma": "SpecialFunctions"}
    FUNCTIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ABS: "abs",
        libsbml.AST_FUNCTION_ARCCOS: "NaNMath.acos",
        libsbml.AST_FUNCTION_ARCCOSH: "NaNMath.acosh",
        libsbml.AST_FUNCTION_ARCSIN: "NaNMath.asin",
        libsbml.AST_FUNCTION_ARCSINH: "asinh",
        libsbml.AST_FUNCTION_ARCTAN: "atan",
        libsbml.AST_FUNCTION_ARCTANH: "NaNMath.atanh",
        libsbml.AST_FUNCTION_CEILING: "ceil",
        libsbml.AST_FUNCTION_COS: "NaNMath.cos",
        libsbml.AST_FUNCTION_COSH: "cosh",
        libsbml.AST_FUNCTION_EXP: "exp",
        libsbml.AST_FUNCTION_FLOOR: "floor",
        libsbml.AST_FUNCTION_LN: "NaNMath.log",
        libsbml.AST_FUNCTION_MAX: "max",
        libsbml.AST_FUNCTION_MIN: "min",
        libsbml.AST_FUNCTION_SIN: "NaNMath.sin",
        libsbml.AST_FUNCTION_SINH: "sinh",
        libsbml.AST_FUNCTION_TAN: "NaNMath.tan",
        libsbml.AST_FUNCTION_TANH: "tanh",
    }
    CONSTANTS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_CONSTANT_E: "exp(1.0)",
        libsbml.AST_CONSTANT_PI: "pi",
        libsbml.AST_CONSTANT_TRUE: "true",
        libsbml.AST_CONSTANT_FALSE: "false",
        libsbml.AST_NAME_TIME: "t",
    }
    RECIPROCALS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_SEC: "NaNMath.cos",
        libsbml.AST_FUNCTION_CSC: "NaNMath.sin",
        libsbml.AST_FUNCTION_COT: "NaNMath.tan",
        libsbml.AST_FUNCTION_SECH: "cosh",
        libsbml.AST_FUNCTION_CSCH: "sinh",
        libsbml.AST_FUNCTION_COTH: "tanh",
    }
    OF_RECIPROCALS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ARCSEC: "NaNMath.acos",
        libsbml.AST_FUNCTION_ARCCSC: "NaNMath.asin",
        libsbml.AST_FUNCTION_ARCCOT: "atan",
        libsbml.AST_FUNCTION_ARCSECH: "NaNMath.acosh",
        libsbml.AST_FUNCTION_ARCCSCH: "asinh",
        libsbml.AST_FUNCTION_ARCCOTH: "NaNMath.atanh",
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
        """`NaNMath.pow(a, b)`, `NaN` for a negative base and a fractional exponent."""
        return self.call("NaNMath.pow", [base, exponent])

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
        """`NaNMath.log10(x)` or `NaNMath.log(x) / NaNMath.log(b)`."""
        if base is None:
            return self.call("NaNMath.log10", [value])
        return self.divide(
            self.call("NaNMath.log", [value]), self.call("NaNMath.log", [base])
        )

    def root(self, degree: Printed | None, value: Printed) -> Printed:
        """`NaNMath.sqrt(x)` or `NaNMath.pow(x, 1.0 / n)`."""
        if degree is None:
            return self.call("NaNMath.sqrt", [value])
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

    def number_to_bool(self, value: Printed) -> Printed:
        """`x != 0.0`, a julia condition is a `Bool`, `NaN` holds as in C."""
        return self.relation(
            libsbml.AST_RELATIONAL_NEQ, value, self.literal(self.number(0.0))
        )

    def bool_to_number(self, condition: Printed) -> Printed:
        """`Float64(c)`, so that a condition is a number in arithmetic."""
        return self.call("Float64", [condition])
