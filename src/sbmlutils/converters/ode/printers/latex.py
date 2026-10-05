r"""The LaTeX dialect of the math printer.

The math is typeset for the math mode of LaTeX with `amsmath` (for `cases`, `\text`
and `\operatorname`): a product is `a \cdot b`, a quotient `\frac{a}{b}`, the
parentheses are `\mathopen{}\left( \right)`, which grow with their content. A function of SBML which LaTeX has no command for
is an `\operatorname`, e.g. `\operatorname{arcsinh}`. See `document` for the
notation the dialects of a document share.
"""

import math
from collections.abc import Mapping, Sequence
from typing import ClassVar

import libsbml

from sbmlutils.converters.ode.printers.base import Precedence, Printed
from sbmlutils.converters.ode.printers.document import DocumentPrinter


class LatexPrinter(DocumentPrinter):
    """Printer of SBML math as LaTeX."""

    name: ClassVar[str] = "latex"
    FUNCTIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_FUNCTION_ARCCOS: r"\arccos",
        libsbml.AST_FUNCTION_ARCCOSH: r"\operatorname{arccosh}",
        libsbml.AST_FUNCTION_ARCCOT: r"\operatorname{arccot}",
        libsbml.AST_FUNCTION_ARCCOTH: r"\operatorname{arccoth}",
        libsbml.AST_FUNCTION_ARCCSC: r"\operatorname{arccsc}",
        libsbml.AST_FUNCTION_ARCCSCH: r"\operatorname{arccsch}",
        libsbml.AST_FUNCTION_ARCSEC: r"\operatorname{arcsec}",
        libsbml.AST_FUNCTION_ARCSECH: r"\operatorname{arcsech}",
        libsbml.AST_FUNCTION_ARCSIN: r"\arcsin",
        libsbml.AST_FUNCTION_ARCSINH: r"\operatorname{arcsinh}",
        libsbml.AST_FUNCTION_ARCTAN: r"\arctan",
        libsbml.AST_FUNCTION_ARCTANH: r"\operatorname{arctanh}",
        libsbml.AST_FUNCTION_COS: r"\cos",
        libsbml.AST_FUNCTION_COSH: r"\cosh",
        libsbml.AST_FUNCTION_COT: r"\cot",
        libsbml.AST_FUNCTION_COTH: r"\coth",
        libsbml.AST_FUNCTION_CSC: r"\csc",
        libsbml.AST_FUNCTION_CSCH: r"\operatorname{csch}",
        libsbml.AST_FUNCTION_EXP: r"\exp",
        libsbml.AST_FUNCTION_LN: r"\ln",
        libsbml.AST_FUNCTION_MAX: r"\max",
        libsbml.AST_FUNCTION_MIN: r"\min",
        libsbml.AST_FUNCTION_SEC: r"\sec",
        libsbml.AST_FUNCTION_SECH: r"\operatorname{sech}",
        libsbml.AST_FUNCTION_SIN: r"\sin",
        libsbml.AST_FUNCTION_SINH: r"\sinh",
        libsbml.AST_FUNCTION_TAN: r"\tan",
        libsbml.AST_FUNCTION_TANH: r"\tanh",
    }
    DELIMITED: ClassVar[Mapping[int, tuple[str, str]]] = {
        libsbml.AST_FUNCTION_ABS: (r"\mathopen{}\left| ", r" \right|"),
        libsbml.AST_FUNCTION_CEILING: (r"\mathopen{}\left\lceil ", r" \right\rceil"),
        libsbml.AST_FUNCTION_FLOOR: (r"\mathopen{}\left\lfloor ", r" \right\rfloor"),
    }
    CONSTANTS: ClassVar[Mapping[int, str]] = {
        # upright, as ISO 80000-2 writes it, so that it is not read as a symbol `e`
        libsbml.AST_CONSTANT_E: r"\mathrm{e}",
        libsbml.AST_CONSTANT_PI: r"\pi",
        libsbml.AST_CONSTANT_TRUE: r"\mathrm{true}",
        libsbml.AST_CONSTANT_FALSE: r"\mathrm{false}",
        libsbml.AST_NAME_TIME: "t",
        libsbml.AST_NAME_AVOGADRO: r"N_{\mathrm{A}}",
    }
    RELATIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_RELATIONAL_EQ: "=",
        libsbml.AST_RELATIONAL_NEQ: r"\neq",
        libsbml.AST_RELATIONAL_GT: ">",
        libsbml.AST_RELATIONAL_GEQ: r"\geq",
        libsbml.AST_RELATIONAL_LT: "<",
        libsbml.AST_RELATIONAL_LEQ: r"\leq",
    }
    TIMES: ClassVar[str] = r" \cdot "
    SCIENTIFIC_TIMES: ClassVar[str] = r" \times "
    INFINITY: ClassVar[str] = r"\infty"
    NAN: ClassVar[str] = r"\mathrm{NaN}"
    LOGIC_AND: ClassVar[str] = r" \land "
    LOGIC_OR: ClassVar[str] = r" \lor "
    LOGIC_XOR: ClassVar[str] = r" \oplus "
    LOGIC_IMPLIES: ClassVar[str] = r" \Rightarrow "
    LOGIC_NOT: ClassVar[str] = r"\lnot "
    IVERSON: ClassVar[tuple[str, str]] = (r"\mathopen{}\left[", r"\right]")

    def parenthesize(self, code: str) -> str:
        r"""`\mathopen{}\left(x\right)`, which grows with its content.

        `\left(` is spaced as an inner formula, with a thin space after a function or
        a sign, `\ln (x)`, `- (a + b)`; after `\mathopen{}` it is not.
        """
        return rf"\mathopen{{}}\left({code}\right)"

    def divide(self, numerator: Printed, denominator: Printed) -> Printed:
        r"""`\frac{a}{b}`, which is in parentheses only as the base of a power."""
        return Printed(
            rf"\frac{{{numerator.code}}}{{{denominator.code}}}", Precedence.POWER
        )

    def power(self, base: Printed, exponent: Printed) -> Printed:
        """`a^{b}`, the base in parentheses unless it is an atom."""
        code = f"{self.wrap(base, Precedence.ATOM)}^{{{exponent.code}}}"
        return Printed(code, Precedence.POWER)

    def piecewise(
        self, pieces: Sequence[tuple[Printed, Printed]], otherwise: Printed | None
    ) -> Printed:
        r"""`cases` environment, `\mathrm{NaN}` otherwise if it has no otherwise."""
        rows = [
            rf"{value.code} & \text{{if }} {condition.code}"
            for value, condition in pieces
        ]
        value = otherwise.code if otherwise is not None else self.number(math.nan)
        rows.append(rf"{value} & \text{{otherwise}}")
        code = r"\begin{cases} " + r" \\ ".join(rows) + r" \end{cases}"
        return Printed(code, Precedence.CONDITIONAL)

    def rem(self, dividend: Printed, divisor: Printed) -> Printed:
        r"""`\operatorname{rem}\left(a, b\right)`."""
        return self.call(r"\operatorname{rem}", [dividend, divisor])

    def quotient(self, dividend: Printed, divisor: Printed) -> Printed:
        r"""`\operatorname{quotient}\left(a, b\right)`."""
        return self.call(r"\operatorname{quotient}", [dividend, divisor])

    def log(self, base: Printed | None, value: Printed) -> Printed:
        r"""`\log_{b}\left(x\right)`, `\log_{10}` without a base."""
        subscript = base.code if base is not None else self.integer(10)
        return self.call(rf"\log_{{{subscript}}}", [value])

    def root(self, degree: Printed | None, value: Printed) -> Printed:
        r"""`\sqrt{x}` or `\sqrt[n]{x}`, in parentheses as the base of a power."""
        if degree is None:
            return Printed(rf"\sqrt{{{value.code}}}", Precedence.POWER)
        index = degree.code
        if "]" in index:
            # a bracket would end the optional argument
            index = f"{{{index}}}"
        return Printed(rf"\sqrt[{index}]{{{value.code}}}", Precedence.POWER)
