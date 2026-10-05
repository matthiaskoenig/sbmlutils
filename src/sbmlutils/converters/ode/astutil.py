"""Building and reading the libsbml math of the ODE export.

The analysis builds the math of the system from nodes it owns. A node which is added
to another one is owned by it (libsbml disowns the python object), so a node is added
to one parent only and a node of another math is deep copied first.

The math is built to be read: a sum is written with the signs of its terms, `a - b`
rather than `a + -b`, its first term without a sign if it is positive, a negative
product carries the sign on its first factor, `-2 * J` and `-f * J`, and terms which
are the number 0 are dropped (`signed_sum`, `drop_zero_terms`).
"""

import math
from collections.abc import Iterator, Sequence

import libsbml

__all__ = [
    "drop_zero_terms",
    "is_number",
    "name",
    "negated",
    "node",
    "number",
    "product",
    "signed_sum",
    "walk",
]

_NUMBERS = frozenset({libsbml.AST_INTEGER, libsbml.AST_REAL, libsbml.AST_REAL_E})


def node(ast_type: int, *children: libsbml.ASTNode) -> libsbml.ASTNode:
    """A node of the math with the given children, which it takes ownership of."""
    ast = libsbml.ASTNode(ast_type)
    for child in children:
        ast.addChild(child)
    return ast


def name(sid: str) -> libsbml.ASTNode:
    """The name of an id."""
    ast = libsbml.ASTNode(libsbml.AST_NAME)
    ast.setName(sid)
    return ast


def number(value: float | None) -> libsbml.ASTNode:
    """A real number, `NaN` for a value which is not set."""
    ast = libsbml.ASTNode(libsbml.AST_REAL)
    ast.setValue(math.nan if value is None else float(value))
    return ast


def is_number(ast: libsbml.ASTNode, value: float | None = None) -> bool:
    """Check that the math is a number, the given one if a value is given."""
    if ast.getType() not in _NUMBERS:
        return False
    return value is None or ast.getValue() == value


def walk(ast: libsbml.ASTNode) -> Iterator[libsbml.ASTNode]:
    """Every node of the math in prefix order, a node before its children."""
    stack = [ast]
    while stack:
        current = stack.pop()
        yield current
        count = current.getNumChildren()
        stack.extend(current.getChild(k) for k in reversed(range(count)))


def _children(ast: libsbml.ASTNode) -> list[libsbml.ASTNode]:
    """Copies of the children of a node."""
    return [ast.getChild(k).deepCopy() for k in range(ast.getNumChildren())]


def negated(ast: libsbml.ASTNode) -> libsbml.ASTNode:
    """The negation of the math, which it takes ownership of.

    A number changes its sign, `-x` is `x`, `a - b` is `b - a`, a product or quotient
    negates its first factor, `-2 * J`, `-f * J`, anything else is `-x`.
    """
    ast_type = ast.getType()
    children = _children(ast)
    if ast_type in _NUMBERS:
        return number(-ast.getValue())
    if ast_type == libsbml.AST_MINUS and len(children) == 1:
        return children[0]
    if ast_type == libsbml.AST_MINUS and len(children) == 2:
        return node(libsbml.AST_MINUS, children[1], children[0])
    if ast_type in {libsbml.AST_TIMES, libsbml.AST_DIVIDE} and len(children) > 1:
        return node(ast_type, negated(children[0]), *children[1:])
    return node(libsbml.AST_MINUS, ast)


def product(factors: Sequence[libsbml.ASTNode]) -> libsbml.ASTNode:
    """The product of the factors, the factor itself if it is the only one."""
    return factors[0] if len(factors) == 1 else node(libsbml.AST_TIMES, *factors)


def signed_sum(terms: Sequence[tuple[int, libsbml.ASTNode]]) -> libsbml.ASTNode:
    """The sum of signed terms, written with their signs.

    A positive term is added, a negative one subtracted, the first one is negated if
    it is negative; a term which is the number 0 is dropped, the sum of no term is 0.
    The positive terms which follow each other are one n-ary sum, so the depth of the
    math grows with the changes of sign only.

    Args:
        terms: the sign (`1` or `-1`) and the magnitude of each term, which the sum
            takes ownership of

    Returns:
        the sum
    """
    kept = [(sign, term) for sign, term in terms if not is_number(term, 0.0)]
    if not kept:
        return number(0.0)
    sign, first = kept[0]
    total = first if sign > 0 else negated(first)
    open_sum = False
    for sign, term in kept[1:]:
        if sign > 0 and open_sum:
            total.addChild(term)
        elif sign > 0:
            total, open_sum = node(libsbml.AST_PLUS, total, term), True
        else:
            total, open_sum = node(libsbml.AST_MINUS, total, term), False
    return total


def drop_zero_terms(ast: libsbml.ASTNode) -> libsbml.ASTNode:
    """The math with the terms of its sums which are the number 0 dropped.

    Every sum and difference is rewritten by `signed_sum`, e.g. after a `rateOf` of
    a constant was replaced by 0.

    Args:
        ast: the math, which it takes ownership of

    Returns:
        the math without zero terms
    """
    ast_type = ast.getType()
    children = [drop_zero_terms(child) for child in _children(ast)]
    signs: list[int] = []
    if ast_type == libsbml.AST_PLUS and children:
        signs = [1] * len(children)
    elif ast_type == libsbml.AST_MINUS and len(children) in {1, 2}:
        signs = [1, -1] if len(children) == 2 else [-1]
    if signs:
        terms = []
        for sign, child in zip(signs, children, strict=True):
            # a negation is a negative term, `a + -b` is `a - b`
            negation = child.getType() == libsbml.AST_MINUS
            if negation and child.getNumChildren() == 1:
                sign, child = -sign, child.getChild(0).deepCopy()
            terms.append((sign, child))
        return signed_sum(terms)
    for k, child in enumerate(children):
        ast.replaceChild(k, child, True)
    return ast
