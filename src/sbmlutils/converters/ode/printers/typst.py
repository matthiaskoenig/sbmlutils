"""The typst dialect of the math printer.

The math is typeset for the math mode of typst, `$ ... $`: a product is `a dot b`, a
quotient the fraction `(a)/(b)`, whose parentheses typst removes, so that every
numerator and denominator is in parentheses and a fraction never takes less than its
operand. A function of SBML which typst has no operator for is an `op`, e.g.
`op("arcsinh")(x)`. The logical operators are the symbols `and`, `or`, `xor`,
`not` and `=>` (∧, ∨, ⊕, ¬, ⇒), as in LaTeX. See `document` for the notation the
dialects of a document share.
"""

import math
from collections.abc import Mapping, Sequence
from typing import ClassVar

import libsbml

from sbmlutils.converters.ode.printers.base import Precedence, Printed
from sbmlutils.converters.ode.printers.document import DocumentPrinter


class TypstPrinter(DocumentPrinter):
    """Printer of SBML math as typst."""

    name: ClassVar[str] = "typst"
    FUNCTIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ARCCOS: "arccos",
        libsbml.AST_FUNCTION_ARCCOSH: 'op("arccosh")',
        libsbml.AST_FUNCTION_ARCCOT: 'op("arccot")',
        libsbml.AST_FUNCTION_ARCCOTH: 'op("arccoth")',
        libsbml.AST_FUNCTION_ARCCSC: 'op("arccsc")',
        libsbml.AST_FUNCTION_ARCCSCH: 'op("arccsch")',
        libsbml.AST_FUNCTION_ARCSEC: 'op("arcsec")',
        libsbml.AST_FUNCTION_ARCSECH: 'op("arcsech")',
        libsbml.AST_FUNCTION_ARCSIN: "arcsin",
        libsbml.AST_FUNCTION_ARCSINH: 'op("arcsinh")',
        libsbml.AST_FUNCTION_ARCTAN: "arctan",
        libsbml.AST_FUNCTION_ARCTANH: 'op("arctanh")',
        libsbml.AST_FUNCTION_COS: "cos",
        libsbml.AST_FUNCTION_COSH: "cosh",
        libsbml.AST_FUNCTION_COT: "cot",
        libsbml.AST_FUNCTION_COTH: "coth",
        libsbml.AST_FUNCTION_CSC: "csc",
        libsbml.AST_FUNCTION_CSCH: "csch",
        libsbml.AST_FUNCTION_EXP: "exp",
        libsbml.AST_FUNCTION_LN: "ln",
        libsbml.AST_FUNCTION_MAX: "max",
        libsbml.AST_FUNCTION_MIN: "min",
        libsbml.AST_FUNCTION_SEC: "sec",
        libsbml.AST_FUNCTION_SECH: "sech",
        libsbml.AST_FUNCTION_SIN: "sin",
        libsbml.AST_FUNCTION_SINH: "sinh",
        libsbml.AST_FUNCTION_TAN: "tan",
        libsbml.AST_FUNCTION_TANH: "tanh",
    }
    DELIMITED: ClassVar[Mapping[int, tuple[str, str]]] = {
        libsbml.AST_FUNCTION_ABS: ("abs(", ")"),
        libsbml.AST_FUNCTION_CEILING: ("ceil(", ")"),
        libsbml.AST_FUNCTION_FLOOR: ("floor(", ")"),
    }
    CONSTANTS: ClassVar[Mapping[int, str]] = {
        # upright, as ISO 80000-2 writes it, so that it is not read as a symbol `e`
        libsbml.AST_CONSTANT_E: "upright(e)",
        libsbml.AST_CONSTANT_PI: "pi",
        libsbml.AST_CONSTANT_TRUE: '"true"',
        libsbml.AST_CONSTANT_FALSE: '"false"',
        libsbml.AST_NAME_TIME: "t",
        libsbml.AST_NAME_AVOGADRO: 'N_"A"',
    }
    RELATIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_RELATIONAL_EQ: "=",
        libsbml.AST_RELATIONAL_NEQ: "!=",
        libsbml.AST_RELATIONAL_GT: ">",
        libsbml.AST_RELATIONAL_GEQ: ">=",
        libsbml.AST_RELATIONAL_LT: "<",
        libsbml.AST_RELATIONAL_LEQ: "<=",
    }
    TIMES: ClassVar[str] = " dot "
    SCIENTIFIC_TIMES: ClassVar[str] = " times "
    INFINITY: ClassVar[str] = "infinity"
    NAN: ClassVar[str] = '"NaN"'
    LOGIC_AND: ClassVar[str] = " and "
    LOGIC_OR: ClassVar[str] = " or "
    LOGIC_XOR: ClassVar[str] = " xor "
    LOGIC_IMPLIES: ClassVar[str] = " => "
    LOGIC_NOT: ClassVar[str] = "not "
    IVERSON: ClassVar[tuple[str, str]] = ("[", "]")

    def divide(self, numerator: Printed, denominator: Printed) -> Printed:
        """`(a)/(b)`, which is in parentheses only as the base of a power."""
        return Printed(f"({numerator.code})/({denominator.code})", Precedence.POWER)

    def power(self, base: Printed, exponent: Printed) -> Printed:
        """`a^(b)`, the base in parentheses unless it is an atom."""
        code = f"{self.wrap(base, Precedence.ATOM)}^({exponent.code})"
        return Printed(code, Precedence.POWER)

    def piecewise(
        self, pieces: Sequence[tuple[Printed, Printed]], otherwise: Printed | None
    ) -> Printed:
        """`cases(...)`, `"NaN"` otherwise if it has no otherwise.

        The columns are a `quad` apart, as in the `cases` of LaTeX.
        """
        rows = [
            f'{value.code} & quad "if" {condition.code}' for value, condition in pieces
        ]
        value = otherwise.code if otherwise is not None else self.number(math.nan)
        rows.append(f'{value} & quad "otherwise"')
        return Printed(f"cases({', '.join(rows)})", Precedence.CONDITIONAL)

    def rem(self, dividend: Printed, divisor: Printed) -> Printed:
        """`op("rem")(a, b)`."""
        return self.call('op("rem")', [dividend, divisor])

    def quotient(self, dividend: Printed, divisor: Printed) -> Printed:
        """`op("quotient")(a, b)`."""
        return self.call('op("quotient")', [dividend, divisor])

    def log(self, base: Printed | None, value: Printed) -> Printed:
        """`log_(b) (x)`, `log_(10)` without a base."""
        subscript = base.code if base is not None else self.integer(10)
        return Printed(f"log_({subscript}) ({value.code})", Precedence.POWER)

    def root(self, degree: Printed | None, value: Printed) -> Printed:
        """`sqrt(x)` or `root(n, x)`."""
        if degree is None:
            return self.call("sqrt", [value])
        return self.call("root", [degree, value])
