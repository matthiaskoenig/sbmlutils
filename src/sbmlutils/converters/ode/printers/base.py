"""The engine of the math printers: SBML math as an expression of a target language.

`MathPrinter` walks the libsbml AST and owns the traversal, the precedence of the
expressions and their parentheses. A dialect, i.e. a subclass for one target
language, supplies tables and small hooks:

- `FUNCTIONS`: the functions which are a function of the dialect with the same
  arguments, e.g. `AST_FUNCTION_SIN` is `np.sin` in python. A function in this table
  is written as a call, before any hook of the engine.
- `CONSTANTS`: the constants, `time` and `avogadro`, e.g. `np.pi` for
  `AST_CONSTANT_PI`. A constant which is not in this table is not supported, except
  `avogadro`, which is then written as its number.
- `RELATIONS`, `PLUS`, `MINUS`, `TIMES`, `ARGUMENT_SEPARATOR`: the operators.
- `number`, `integer`: the literals.
- the hooks of the constructs whose structure differs between the languages:
  `negate`, `divide`, `rational`, `power`, `piecewise`, `rem`, `quotient`, `log`,
  `root`, `factorial`, `reciprocal` (sec, csc, cot, sech, csch, coth),
  `of_reciprocal` (arcsec, arccsc, arccot, arcsech, arccsch, arccoth), `minmax`,
  `logic_and`, `logic_or`, `logic_xor`, `logic_not`, `logic_implies`, `relation`
  and `bool_to_number`, plus `call` and `parenthesize` for the shape of a call and
  of a parenthesized expression.

A hook never sees the AST. It receives its operands already printed, each as a
`Printed` with its code and its precedence, and builds its expression with `wrap`
(an operand in parentheses if it binds weaker than its place requires), `infix` and
`call`. So a dialect can write a division as a fraction or a power with the exponent
in braces without touching the traversal. A hook which is not overridden raises
`NotImplementedError`, as does a hook for a construct its dialect cannot express
(its message is the reason); the engine turns it into an `UnsupportedMathError`
which names the math and the printer.

Booleans are numbers in SBML. A relation or a logical operator is printed in its
boolean form; where it is used as a number, the engine passes it through
`bool_to_number`. The operands of a logical operator and the conditions of a
`piecewise` are printed as conditions, everything else as numbers;
`print_condition` prints the top level as a condition (e.g. an event trigger).

Identifiers come only from the `symbols` mapping, which holds the expression of
every name and of every function definition; an identifier without a mapping raises,
so an id of the model is never written raw.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import IntEnum
from itertools import pairwise
from typing import ClassVar, NamedTuple

import libsbml

SymbolMap = Mapping[str, str]
"""Expression of each identifier of the math, e.g. `{"k1": "p[0]"}`."""


class Precedence(IntEnum):
    """Precedence of the expressions, from the weakest to the tightest binding.

    An operand is put in parentheses if its precedence is lower than its place
    requires. The order is the order of python, which the other languages share
    for the constructs the engine writes as operators.
    """

    CONDITIONAL = 1
    OR = 2
    AND = 3
    NOT = 4
    COMPARISON = 5
    XOR = 6
    SUM = 7
    PRODUCT = 8
    UNARY = 9
    POWER = 10
    ATOM = 11


class Printed(NamedTuple):
    """An expression of the target language and its precedence."""

    code: str
    precedence: int


class UnsupportedMathError(NotImplementedError):
    """Math which a printer cannot write.

    Raised by the engine with a message which names the math and the printer, for a
    construct the dialect cannot express and for an identifier without a symbol.
    """


@dataclass(frozen=True)
class _Context:
    """The symbols and the place of the math being printed.

    Attributes:
        symbols: expression of each identifier
        condition: the math is used as a condition, not as a number
    """

    symbols: SymbolMap
    condition: bool

    def as_number(self) -> _Context:
        """The context of an operand which is a number."""
        return replace(self, condition=False) if self.condition else self

    def as_condition(self) -> _Context:
        """The context of an operand which is a condition."""
        return self if self.condition else replace(self, condition=True)


# functions which are the reciprocal of a function, sec(x) = 1/cos(x)
_RECIPROCALS = frozenset(
    {
        libsbml.AST_FUNCTION_SEC,
        libsbml.AST_FUNCTION_CSC,
        libsbml.AST_FUNCTION_COT,
        libsbml.AST_FUNCTION_SECH,
        libsbml.AST_FUNCTION_CSCH,
        libsbml.AST_FUNCTION_COTH,
    }
)

# functions which are a function of the reciprocal, arcsec(x) = arccos(1/x)
_OF_RECIPROCALS = frozenset(
    {
        libsbml.AST_FUNCTION_ARCSEC,
        libsbml.AST_FUNCTION_ARCCSC,
        libsbml.AST_FUNCTION_ARCCOT,
        libsbml.AST_FUNCTION_ARCSECH,
        libsbml.AST_FUNCTION_ARCCSCH,
        libsbml.AST_FUNCTION_ARCCOTH,
    }
)

_RELATIONS = frozenset(
    {
        libsbml.AST_RELATIONAL_EQ,
        libsbml.AST_RELATIONAL_NEQ,
        libsbml.AST_RELATIONAL_GT,
        libsbml.AST_RELATIONAL_GEQ,
        libsbml.AST_RELATIONAL_LT,
        libsbml.AST_RELATIONAL_LEQ,
    }
)


def _is_number(ast: libsbml.ASTNode, value: float) -> bool:
    """Check that the math is the given number, written as an integer or a real."""
    ast_type = ast.getType()
    if ast_type == libsbml.AST_INTEGER:
        return ast.getInteger() == value
    if ast_type in {libsbml.AST_REAL, libsbml.AST_REAL_E}:
        return ast.getReal() == value
    return False


class MathPrinter:
    """Printer of SBML math as an expression of a target language.

    The base class prints the arithmetic of SBML core (numbers, identifiers, calls
    of function definitions, sums, differences, products and quotients); every
    other construct needs a table entry or a hook of the dialect.

    Attributes:
        name: name of the dialect, used in the messages of the errors
        FUNCTIONS: function of the dialect of each function of SBML which is a call
            with the same arguments
        CONSTANTS: expression of each constant, of `time` and of `avogadro`
        RELATIONS: operator of each relation
        PLUS: operator of a sum, with its spaces
        MINUS: operator of a difference, with its spaces
        TIMES: operator of a product, with its spaces
        DIVIDE: operator of a quotient, with its spaces, used by `divide`
        ARGUMENT_SEPARATOR: separator of the arguments of a call
    """

    name: ClassVar[str] = "math"
    FUNCTIONS: ClassVar[Mapping[int, str]] = {}
    CONSTANTS: ClassVar[Mapping[int, str]] = {}
    RELATIONS: ClassVar[Mapping[int, str]] = {
        libsbml.AST_RELATIONAL_EQ: "==",
        libsbml.AST_RELATIONAL_NEQ: "!=",
        libsbml.AST_RELATIONAL_GT: ">",
        libsbml.AST_RELATIONAL_GEQ: ">=",
        libsbml.AST_RELATIONAL_LT: "<",
        libsbml.AST_RELATIONAL_LEQ: "<=",
    }
    PLUS: ClassVar[str] = " + "
    MINUS: ClassVar[str] = " - "
    TIMES: ClassVar[str] = " * "
    DIVIDE: ClassVar[str] = " / "
    ARGUMENT_SEPARATOR: ClassVar[str] = ", "

    def print(self, ast: libsbml.ASTNode, symbols: SymbolMap) -> str:
        """Print math which is used as a number.

        Args:
            ast: the math
            symbols: expression of each identifier, names and function definitions

        Returns:
            the expression

        Raises:
            UnsupportedMathError: for an identifier without an entry in `symbols` and
                for a construct the dialect cannot express
        """
        return self._print(ast, _Context(symbols=symbols, condition=False)).code

    def print_condition(self, ast: libsbml.ASTNode, symbols: SymbolMap) -> str:
        """Print math which is used as a condition, e.g. the trigger of an event.

        Args:
            ast: the math
            symbols: expression of each identifier, names and function definitions

        Returns:
            the expression, a boolean of the dialect

        Raises:
            UnsupportedMathError: for an identifier without an entry in `symbols` and
                for a construct the dialect cannot express
        """
        return self._print(ast, _Context(symbols=symbols, condition=True)).code

    # --- building blocks of the hooks ---------------------------------------------

    def parenthesize(self, code: str) -> str:
        """Put an expression in parentheses.

        Args:
            code: the expression

        Returns:
            the expression in parentheses
        """
        return f"({code})"

    def wrap(self, operand: Printed, precedence: int) -> str:
        """Code of an operand, in parentheses if it binds weaker than its place.

        Args:
            operand: the printed operand
            precedence: the lowest precedence the place takes without parentheses

        Returns:
            the code of the operand
        """
        if operand.precedence >= precedence:
            return operand.code
        return self.parenthesize(operand.code)

    def infix(
        self, operands: Sequence[Printed], operator: str, precedence: int
    ) -> Printed:
        """Left associative operation on the operands, `a - b - c` is `(a - b) - c`.

        Args:
            operands: the printed operands, at least one
            operator: the operator with its spaces
            precedence: the precedence of the operation

        Returns:
            the printed operation
        """
        first, *others = operands
        code = operator.join(
            [self.wrap(first, precedence)]
            + [self.wrap(operand, precedence + 1) for operand in others]
        )
        return Printed(code, precedence)

    def call(self, function: str, arguments: Sequence[Printed]) -> Printed:
        """Call of a function.

        Args:
            function: the function of the dialect
            arguments: the printed arguments

        Returns:
            the printed call
        """
        code = self.ARGUMENT_SEPARATOR.join(argument.code for argument in arguments)
        return Printed(f"{function}({code})", Precedence.ATOM)

    # --- literals -----------------------------------------------------------------

    def integer(self, value: int) -> str:
        """Literal of an integer.

        Args:
            value: the integer

        Returns:
            the literal
        """
        return str(value)

    def number(self, value: float) -> str:
        """Literal of a real number, infinity and not a number included.

        The base class writes the finite numbers only.

        Args:
            value: the number

        Returns:
            the literal
        """
        if not math.isfinite(value):
            raise NotImplementedError(f"The number {value} has no literal.")
        return repr(float(value))

    # --- hooks of the arithmetic --------------------------------------------------

    def negate(self, operand: Printed) -> Printed:
        """Unary minus, which binds weaker than a power on its right, `-a^2`.

        Args:
            operand: the printed operand

        Returns:
            the printed negation
        """
        return Printed(f"-{self.wrap(operand, Precedence.POWER)}", Precedence.UNARY)

    def divide(self, numerator: Printed, denominator: Printed) -> Printed:
        """Quotient of two numbers.

        Args:
            numerator: the printed numerator
            denominator: the printed denominator

        Returns:
            the printed quotient
        """
        return self.infix([numerator, denominator], self.DIVIDE, Precedence.PRODUCT)

    def rational(self, numerator: int, denominator: int) -> Printed:
        """Rational number, the quotient of two integers.

        Args:
            numerator: the numerator
            denominator: the denominator

        Returns:
            the printed rational number
        """
        return self.divide(self._integer(numerator), self._integer(denominator))

    def power(self, base: Printed, exponent: Printed) -> Printed:
        """Power, right associative, `a^b^c` is `a^(b^c)`.

        Args:
            base: the printed base
            exponent: the printed exponent

        Returns:
            the printed power
        """
        raise NotImplementedError

    def piecewise(
        self, pieces: Sequence[tuple[Printed, Printed]], otherwise: Printed | None
    ) -> Printed:
        """Piecewise function, the value of the first piece whose condition holds.

        Args:
            pieces: the printed value and condition of each piece
            otherwise: the printed value if no condition holds, `None` if it is
                missing (the value is undefined)

        Returns:
            the printed piecewise function
        """
        raise NotImplementedError

    def rem(self, dividend: Printed, divisor: Printed) -> Printed:
        """Remainder of the division, with the sign of the dividend.

        Args:
            dividend: the printed dividend
            divisor: the printed divisor

        Returns:
            the printed remainder
        """
        raise NotImplementedError

    def quotient(self, dividend: Printed, divisor: Printed) -> Printed:
        """Integer part of the quotient, truncated towards zero.

        Args:
            dividend: the printed dividend
            divisor: the printed divisor

        Returns:
            the printed integer quotient
        """
        raise NotImplementedError

    def log(self, base: Printed | None, value: Printed) -> Printed:
        """Logarithm to a base.

        Args:
            base: the printed base, `None` for the base 10
            value: the printed argument

        Returns:
            the printed logarithm
        """
        raise NotImplementedError

    def root(self, degree: Printed | None, value: Printed) -> Printed:
        """Root of a degree.

        Args:
            degree: the printed degree, `None` for the square root
            value: the printed argument

        Returns:
            the printed root
        """
        raise NotImplementedError

    def factorial(self, value: Printed) -> Printed:
        """Factorial.

        Args:
            value: the printed argument

        Returns:
            the printed factorial
        """
        raise NotImplementedError

    def reciprocal(self, function: int, value: Printed) -> Printed:
        """Function which is the reciprocal of a function, `sec(x) = 1/cos(x)`.

        Args:
            function: the libsbml type of the function, e.g. `AST_FUNCTION_SEC`
            value: the printed argument

        Returns:
            the printed function
        """
        raise NotImplementedError

    def of_reciprocal(self, function: int, value: Printed) -> Printed:
        """Function which is a function of the reciprocal, `arcsec(x) = arccos(1/x)`.

        Args:
            function: the libsbml type of the function, e.g. `AST_FUNCTION_ARCSEC`
            value: the printed argument

        Returns:
            the printed function
        """
        raise NotImplementedError

    def minmax(self, function: int, arguments: Sequence[Printed]) -> Printed:
        """Maximum or minimum of the arguments.

        Args:
            function: `AST_FUNCTION_MAX` or `AST_FUNCTION_MIN`
            arguments: the printed arguments, at least one

        Returns:
            the printed maximum or minimum
        """
        raise NotImplementedError

    # --- hooks of the logic -------------------------------------------------------

    def relation(self, relation: int, left: Printed, right: Printed) -> Printed:
        """Relation of two numbers, a condition.

        Args:
            relation: the libsbml type of the relation, e.g. `AST_RELATIONAL_LT`
            left: the printed left operand
            right: the printed right operand

        Returns:
            the printed relation
        """
        if relation not in self.RELATIONS:
            raise NotImplementedError
        operand = Precedence.COMPARISON + 1
        code = (
            f"{self.wrap(left, operand)} {self.RELATIONS[relation]} "
            f"{self.wrap(right, operand)}"
        )
        return Printed(code, Precedence.COMPARISON)

    def logic_and(self, operands: Sequence[Printed]) -> Printed:
        """Conjunction of conditions.

        Args:
            operands: the printed conditions, at least two

        Returns:
            the printed condition
        """
        raise NotImplementedError

    def logic_or(self, operands: Sequence[Printed]) -> Printed:
        """Disjunction of conditions.

        Args:
            operands: the printed conditions, at least two

        Returns:
            the printed condition
        """
        raise NotImplementedError

    def logic_xor(self, operands: Sequence[Printed]) -> Printed:
        """Exclusive disjunction of conditions, true for an odd number of them.

        Args:
            operands: the printed conditions, at least two

        Returns:
            the printed condition
        """
        raise NotImplementedError

    def logic_not(self, operand: Printed) -> Printed:
        """Negation of a condition.

        Args:
            operand: the printed condition

        Returns:
            the printed condition
        """
        raise NotImplementedError

    def logic_implies(self, premise: Printed, conclusion: Printed) -> Printed:
        """Implication of two conditions.

        Args:
            premise: the printed premise
            conclusion: the printed conclusion

        Returns:
            the printed condition
        """
        raise NotImplementedError

    def bool_to_number(self, condition: Printed) -> Printed:
        """A condition used as a number, 1 if it holds, else 0.

        The base class writes the condition as it is, for a dialect whose booleans
        are numbers.

        Args:
            condition: the printed condition

        Returns:
            the printed number
        """
        return condition

    # --- traversal ----------------------------------------------------------------

    def _print(self, ast: libsbml.ASTNode, ctx: _Context) -> Printed:
        """Print math in a context.

        Args:
            ast: the math
            ctx: the symbols and the place of the math

        Returns:
            the printed math

        Raises:
            UnsupportedMathError: for an identifier without a symbol and for a
                construct the dialect cannot express
        """
        try:
            return self._dispatch(ast, ctx)
        except UnsupportedMathError:
            raise
        except NotImplementedError as error:
            formula = libsbml.formulaToL3String(ast)
            message = (
                f"The math '{formula}' is not supported by the {self.name} printer."
            )
            if str(error):
                message = f"{message} {error}"
            raise UnsupportedMathError(message) from None

    def _dispatch(self, ast: libsbml.ASTNode, ctx: _Context) -> Printed:
        """Print math by the type of its node, see `_print`."""
        ast_type: int = ast.getType()
        children: list[libsbml.ASTNode] = [
            ast.getChild(k) for k in range(ast.getNumChildren())
        ]
        if ast_type in self.CONSTANTS:
            return Printed(self.CONSTANTS[ast_type], Precedence.ATOM)
        if ast_type in self.FUNCTIONS:
            return self.call(self.FUNCTIONS[ast_type], self._numbers(children, ctx))

        match ast_type:
            # numbers and identifiers
            case libsbml.AST_INTEGER:
                return self._integer(ast.getInteger())
            case libsbml.AST_REAL | libsbml.AST_REAL_E | libsbml.AST_NAME_AVOGADRO:
                return self._literal(self.number(ast.getReal()))
            case libsbml.AST_RATIONAL:
                return self.rational(ast.getNumerator(), ast.getDenominator())
            case libsbml.AST_NAME:
                return Printed(self._symbol(ast.getName(), ctx), Precedence.ATOM)
            case libsbml.AST_FUNCTION:
                function = self._symbol(ast.getName(), ctx)
                return self.call(function, self._numbers(children, ctx))

            # arithmetic
            case libsbml.AST_PLUS | libsbml.AST_TIMES:
                is_sum = ast_type == libsbml.AST_PLUS
                if not children:
                    return self._integer(0 if is_sum else 1)
                if len(children) == 1:
                    return self._print(children[0], ctx.as_number())
                operator, precedence = (
                    (self.PLUS, Precedence.SUM)
                    if is_sum
                    else (self.TIMES, Precedence.PRODUCT)
                )
                return self.infix(self._numbers(children, ctx), operator, precedence)
            case libsbml.AST_MINUS:
                operands = self._numbers(children, ctx)
                if len(operands) == 1:
                    return self.negate(operands[0])
                self._check_arity(operands, 2, None)
                return self.infix(operands, self.MINUS, Precedence.SUM)
            case libsbml.AST_DIVIDE:
                numerator, denominator = self._numbers(children, ctx, 2)
                return self.divide(numerator, denominator)
            case libsbml.AST_POWER | libsbml.AST_FUNCTION_POWER:
                base, exponent = self._numbers(children, ctx, 2)
                return self.power(base, exponent)

            # functions
            case libsbml.AST_FUNCTION_LOG | libsbml.AST_FUNCTION_ROOT:
                # the base (degree) is the first child, 10 (2) if it is missing
                default = 10 if ast_type == libsbml.AST_FUNCTION_LOG else 2
                self._check_arity(children, 1, 2)
                qualifier: Printed | None = None
                if len(children) == 2 and not _is_number(children[0], default):
                    qualifier = self._print(children[0], ctx.as_number())
                value = self._print(children[-1], ctx.as_number())
                if ast_type == libsbml.AST_FUNCTION_LOG:
                    return self.log(qualifier, value)
                return self.root(qualifier, value)
            case libsbml.AST_FUNCTION_FACTORIAL:
                (value,) = self._numbers(children, ctx, 1)
                return self.factorial(value)
            case libsbml.AST_FUNCTION_REM:
                dividend, divisor = self._numbers(children, ctx, 2)
                return self.rem(dividend, divisor)
            case libsbml.AST_FUNCTION_QUOTIENT:
                dividend, divisor = self._numbers(children, ctx, 2)
                return self.quotient(dividend, divisor)
            case libsbml.AST_FUNCTION_MAX | libsbml.AST_FUNCTION_MIN:
                arguments = self._numbers(children, ctx)
                self._check_arity(arguments, 1, None)
                return self.minmax(ast_type, arguments)
            case _ if ast_type in _RECIPROCALS:
                (value,) = self._numbers(children, ctx, 1)
                return self.reciprocal(ast_type, value)
            case _ if ast_type in _OF_RECIPROCALS:
                (value,) = self._numbers(children, ctx, 1)
                return self.of_reciprocal(ast_type, value)

            # logic and relations
            case (
                libsbml.AST_LOGICAL_AND
                | libsbml.AST_LOGICAL_OR
                | libsbml.AST_LOGICAL_XOR
            ):
                if not children:
                    # the empty conjunction holds, the empty disjunctions do not
                    is_and = ast_type == libsbml.AST_LOGICAL_AND
                    return self._constant(
                        libsbml.AST_CONSTANT_TRUE
                        if is_and
                        else libsbml.AST_CONSTANT_FALSE
                    )
                conditions = self._conditions(children, ctx)
                if len(conditions) == 1:
                    return self._boolean(conditions[0], ctx)
                if ast_type == libsbml.AST_LOGICAL_AND:
                    return self._boolean(self.logic_and(conditions), ctx)
                if ast_type == libsbml.AST_LOGICAL_OR:
                    return self._boolean(self.logic_or(conditions), ctx)
                return self._boolean(self.logic_xor(conditions), ctx)
            case libsbml.AST_LOGICAL_NOT:
                (condition,) = self._conditions(children, ctx, 1)
                return self._boolean(self.logic_not(condition), ctx)
            case libsbml.AST_LOGICAL_IMPLIES:
                premise, conclusion = self._conditions(children, ctx, 2)
                return self._boolean(self.logic_implies(premise, conclusion), ctx)
            case _ if ast_type in _RELATIONS:
                if len(children) < 2:
                    # a relation of a single number holds
                    return self._constant(libsbml.AST_CONSTANT_TRUE)
                # a relation of more than two numbers holds for each pair in turn,
                # a < b < c is a < b and b < c
                operands = self._numbers(children, ctx)
                relations = [
                    self.relation(ast_type, left, right)
                    for left, right in pairwise(operands)
                ]
                if len(relations) == 1:
                    return self._boolean(relations[0], ctx)
                return self._boolean(self.logic_and(relations), ctx)

            # piecewise(value1, condition1, value2, condition2, ..., otherwise)
            case libsbml.AST_FUNCTION_PIECEWISE:
                pieces = [
                    (
                        self._print(value, ctx),
                        self._print(condition, ctx.as_condition()),
                    )
                    for value, condition in zip(
                        children[0::2], children[1::2], strict=False
                    )
                ]
                otherwise = (
                    self._print(children[-1], ctx) if len(children) % 2 else None
                )
                return self.piecewise(pieces, otherwise)

        raise NotImplementedError

    # --- helpers of the traversal -------------------------------------------------

    def _integer(self, value: int) -> Printed:
        """Printed integer."""
        return self._literal(self.integer(value))

    def _literal(self, code: str) -> Printed:
        """Printed literal, a negative literal is a unary minus."""
        return Printed(
            code, Precedence.UNARY if code.startswith("-") else Precedence.ATOM
        )

    def _constant(self, constant: int) -> Printed:
        """Printed constant of the `CONSTANTS`."""
        if constant not in self.CONSTANTS:
            raise NotImplementedError
        return Printed(self.CONSTANTS[constant], Precedence.ATOM)

    def _symbol(self, sid: str, ctx: _Context) -> str:
        """Expression of an identifier, which must be in the symbols."""
        if sid not in ctx.symbols:
            raise UnsupportedMathError(
                f"The identifier {sid!r} has no symbol and is not supported by the "
                f"{self.name} printer (e.g. a local parameter or a function "
                f"definition which is not part of the symbols)."
            )
        return ctx.symbols[sid]

    def _boolean(self, condition: Printed, ctx: _Context) -> Printed:
        """A printed condition in its context, a number unless it is a condition."""
        return condition if ctx.condition else self.bool_to_number(condition)

    def _numbers(
        self,
        children: Sequence[libsbml.ASTNode],
        ctx: _Context,
        arity: int | None = None,
    ) -> list[Printed]:
        """Print the children as numbers, of the given number if it is set."""
        if arity is not None:
            self._check_arity(children, arity, arity)
        number = ctx.as_number()
        return [self._print(child, number) for child in children]

    def _conditions(
        self,
        children: Sequence[libsbml.ASTNode],
        ctx: _Context,
        arity: int | None = None,
    ) -> list[Printed]:
        """Print the children as conditions, of the given number if it is set."""
        if arity is not None:
            self._check_arity(children, arity, arity)
        condition = ctx.as_condition()
        return [self._print(child, condition) for child in children]

    @staticmethod
    def _check_arity(
        children: Sequence[object], minimum: int, maximum: int | None
    ) -> None:
        """Check the number of the children of a node.

        Raises:
            NotImplementedError: if it is less than the minimum or more than the maximum
        """
        if len(children) < minimum or (maximum is not None and len(children) > maximum):
            raise NotImplementedError(
                f"It has {len(children)} arguments, which is not the number of "
                f"arguments of the construct."
            )
