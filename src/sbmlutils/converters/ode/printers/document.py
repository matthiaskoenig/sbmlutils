"""The base of the dialects which typeset math for a document, LaTeX and typst.

A document shows the math to a reader, so it is written as a textbook writes it and
not as a program does:

- a product is `a · b` and a quotient a fraction, which needs no parentheses around
  its numerator and its denominator; the base of a power is in parentheses unless it
  is an atom, `(a/b)^2`, `(sin(x))^2`, `(√x)^2`, `|x|^2`;
- a negative operand after an operator is in parentheses, `a · (-b)`, `a + (-b)`;
- a number is written without a trailing `.0` and with a power of ten instead of an
  exponent, `2`, `1.5 × 10^-5`;
- a `piecewise` is a cases environment, in parentheses where it is the operand of an
  operator, so that what follows it is not read as part of its last piece;
- a condition which is used as a number is an Iverson bracket, `[A > 1]`, which is
  1 if the condition holds and 0 otherwise;
- the operands of a logical operator are in parentheses unless they are a relation
  (except for ⊕), a negation or an atom, so that the reader needs no precedence of
  the logical operators, `(a ∧ b) ∨ c`, `(a > 1) ⊕ b`.

`print_lines` breaks a long sum into lines of a given number of terms, for an
equation of several lines.
"""

import math
from collections.abc import Sequence
from typing import ClassVar

import libsbml

from sbmlutils.converters.ode.printers.base import (
    MathPrinter,
    Precedence,
    Printed,
    SymbolMap,
)


class DocumentPrinter(MathPrinter):
    """Printer of SBML math typeset for a document, the base of LaTeX and typst.

    Attributes:
        SCIENTIFIC_TIMES: operator between the mantissa and the power of ten of a
            number, with its spaces
        INFINITY: infinity
        NAN: not a number
        LOGIC_AND: operator of a conjunction, with its spaces
        LOGIC_OR: operator of a disjunction, with its spaces
        LOGIC_XOR: operator of an exclusive disjunction, with its spaces
        LOGIC_IMPLIES: operator of an implication, with its spaces
        LOGIC_NOT: operator of a negation, with its space
        IVERSON: left and right bracket of a condition used as a number
    """

    SCIENTIFIC_TIMES: ClassVar[str]
    INFINITY: ClassVar[str]
    NAN: ClassVar[str]
    LOGIC_AND: ClassVar[str]
    LOGIC_OR: ClassVar[str]
    LOGIC_XOR: ClassVar[str]
    LOGIC_IMPLIES: ClassVar[str]
    LOGIC_NOT: ClassVar[str]
    IVERSON: ClassVar[tuple[str, str]]

    def print_lines(
        self, ast: libsbml.ASTNode, symbols: SymbolMap, width: int = 4
    ) -> list[str]:
        """Print math which is used as a number in lines of at most `width` terms.

        The terms are those of `terms`, with the nested sums flattened, so that
        `a - (b - c)` is `a - b + c`. A line after the first begins with the sign
        of its first term, `+ e + f`. Math which is no sum is a single line.

        Args:
            ast: the math
            symbols: expression of each identifier, names and function definitions
            width: the largest number of terms of a line, at least one

        Returns:
            the lines; a line after the first which begins a cell of an alignment
            needs an empty atom before it, so that its sign is spaced as a binary
            operator: `{}` in LaTeX (the `align` of amsmath writes it), `""` in typst

        Raises:
            ValueError: if the width is less than one
            UnsupportedMathError: for an identifier without an entry in `symbols` and
                for a construct the dialect cannot express
        """
        if width < 1:
            raise ValueError(f"The width of a line is at least one term, not {width}.")
        terms = self.terms(ast, symbols)
        if len(terms) == 1 and not terms[0].negative:
            return [terms[0].printed.code]
        codes: list[str] = []
        for k, (negative, term) in enumerate(terms):
            if k == 0:
                first = self.negate(term) if negative else term
                codes.append(self.wrap(first, Precedence.SUM))
            else:
                sign = (self.MINUS if negative else self.PLUS).lstrip()
                codes.append(
                    f"{sign}{self.wrap(self._unsigned(term), Precedence.PRODUCT)}"
                )
        return [
            " ".join(codes[start : start + width])
            for start in range(0, len(codes), width)
        ]

    # --- building blocks ----------------------------------------------------------

    def _unsigned(self, operand: Printed) -> Printed:
        """An operand after an operator or a sign, in parentheses if it is negative.

        Args:
            operand: the printed operand

        Returns:
            the operand, `(-b)` for a negative one, so that `a + (-b)` is not `a + -b`
        """
        if operand.precedence == Precedence.UNARY:
            return Printed(self.parenthesize(operand.code), Precedence.ATOM)
        return operand

    def call(self, function: str, arguments: Sequence[Printed]) -> Printed:
        """`f(a, b)`, in parentheses as the base of a power, `(sin(x))^2`."""
        return super().call(function, arguments)._replace(precedence=Precedence.POWER)

    def infix(
        self, operands: Sequence[Printed], operator: str, precedence: int
    ) -> Printed:
        """Left associative operation, `a · (-b)`: a negative operand in parentheses."""
        first, *others = operands
        unsigned = [self._unsigned(operand) for operand in others]
        return super().infix([first, *unsigned], operator, precedence)

    # --- literals -----------------------------------------------------------------

    def literal(self, code: str) -> Printed:
        """Precedence of a literal of `number`, `10^-5` is a power, `2 × 10^-5` a product."""
        if code.startswith("-"):
            return Printed(code, Precedence.UNARY)
        if self.SCIENTIFIC_TIMES in code:
            return Printed(code, Precedence.PRODUCT)
        if "^" in code:
            return Printed(code, Precedence.POWER)
        return Printed(code, Precedence.ATOM)

    def number(self, value: float) -> str:
        """Number as a textbook writes it, `2`, `0.1`, `10^-5`, `1.5 × 10^-5`."""
        if math.isnan(value):
            return self.NAN
        if math.isinf(value):
            return self.INFINITY if value > 0 else f"-{self.INFINITY}"
        mantissa, _, exponent = repr(float(value)).partition("e")
        mantissa = mantissa.removesuffix(".0")
        if not exponent:
            return mantissa
        ten = self.power(self._integer(10), self._integer(int(exponent)))
        if mantissa in {"1", "-1"}:
            # 10^-5 rather than 1 × 10^-5
            sign = "-" if mantissa.startswith("-") else ""
            return f"{sign}{ten.code}"
        return f"{mantissa}{self.SCIENTIFIC_TIMES}{ten.code}"

    # --- hooks of the arithmetic --------------------------------------------------

    def negate(self, operand: Printed) -> Printed:
        """`-a`, `-a · b`, the operand in parentheses if it is weaker or negative."""
        code = f"-{self.wrap(self._unsigned(operand), Precedence.PRODUCT)}"
        return Printed(code, Precedence.UNARY)

    def factorial(self, value: Printed) -> Printed:
        """`x!`, the argument in parentheses unless it is an atom."""
        return Printed(f"{self.wrap(value, Precedence.ATOM)}!", Precedence.POWER)

    # --- hooks of the logic -------------------------------------------------------

    def _logic(
        self,
        operands: Sequence[Printed],
        operator: str,
        precedence: int,
        relations: bool = True,
    ) -> Printed:
        """Logical operation, `(a ∨ b) ∧ c > 1`.

        Args:
            operands: the printed conditions
            operator: the operator with its spaces
            precedence: the precedence of the operation
            relations: a relation is an operand without parentheses

        Returns:
            the printed condition, an operand other than an atom, a negation or a
            relation in parentheses
        """
        bare = {Precedence.ATOM, Precedence.NOT}
        if relations:
            bare.add(Precedence.COMPARISON)
        code = operator.join(
            operand.code
            if operand.precedence in bare
            else self.parenthesize(operand.code)
            for operand in operands
        )
        return Printed(code, precedence)

    def logic_and(self, operands: Sequence[Printed]) -> Printed:
        """`a ∧ b`."""
        return self._logic(operands, self.LOGIC_AND, Precedence.AND)

    def logic_or(self, operands: Sequence[Printed]) -> Printed:
        """`a ∨ b`."""
        return self._logic(operands, self.LOGIC_OR, Precedence.OR)

    def logic_xor(self, operands: Sequence[Printed]) -> Printed:
        """`(a > 1) ⊕ b`, as weak as a disjunction.

        A relation is in parentheses: ⊕ is no common operator of logic, and is not
        read as weaker than a relation.
        """
        return self._logic(operands, self.LOGIC_XOR, Precedence.OR, relations=False)

    def logic_implies(self, premise: Printed, conclusion: Printed) -> Printed:
        """`a ⇒ b`, as weak as a disjunction."""
        return self._logic([premise, conclusion], self.LOGIC_IMPLIES, Precedence.OR)

    def logic_not(self, operand: Printed) -> Printed:
        """`¬¬a`, `¬(a > 1)`: an operand in parentheses unless an atom or a negation."""
        code = operand.code
        if operand.precedence not in {Precedence.NOT, Precedence.ATOM}:
            code = self.parenthesize(code)
        return Printed(f"{self.LOGIC_NOT}{code}", Precedence.NOT)

    def bool_to_number(self, condition: Printed) -> Printed:
        """Iverson bracket `[c]`, which is 1 if the condition holds, else 0."""
        left, right = self.IVERSON
        return Printed(f"{left}{condition.code}{right}", Precedence.ATOM)
