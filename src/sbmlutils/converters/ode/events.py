"""The continuous root function of the trigger of an event.

An integrator finds an event as the root of a continuous function whose sign is the
truth value of the trigger: positive where the trigger holds, negative where it does
not. A relation is a difference, `a > b` is `a - b`; a conjunction holds where all of
its operands hold, which is where their minimum is positive, a disjunction where
their maximum is. Strict and non-strict relations have the same root function, they
differ only at the root itself, which the integrator resolves by the direction of
the crossing.
"""

import itertools

import libsbml

from sbmlutils.converters.ode.astutil import negated, node, number

__all__ = ["trigger_root"]

# the relations which hold where the left operand minus the right one is positive,
# and those where it is negative
_GREATER = frozenset({libsbml.AST_RELATIONAL_GT, libsbml.AST_RELATIONAL_GEQ})
_LESS = frozenset({libsbml.AST_RELATIONAL_LT, libsbml.AST_RELATIONAL_LEQ})
_NUMBERS = frozenset(
    {libsbml.AST_INTEGER, libsbml.AST_REAL, libsbml.AST_REAL_E, libsbml.AST_RATIONAL}
)


def _extreme(ast_type: int, roots: list[libsbml.ASTNode]) -> libsbml.ASTNode:
    """The minimum or maximum of root functions, the root itself if it is the only one."""
    return roots[0] if len(roots) == 1 else node(ast_type, *roots)


def trigger_root(trigger: libsbml.ASTNode) -> libsbml.ASTNode:
    """The root function of a trigger, positive where the trigger holds.

    - `a > b`, `a >= b` is `a - b`; `a < b`, `a <= b` is `b - a`; a relation of more
      than two operands, `a < b < c`, is the minimum of the root functions of its
      pairs;
    - `x && y` is the minimum, `x || y` the maximum of the root functions of the
      operands, `!x` is the negation of the root function of `x`;
    - `xor(x, y)` is `max(min(x, -y), min(-x, y))`, `implies(x, y)` is `max(-x, y)`;
    - `true` is `1`, `false` is `-1`, a number is true unless it is 0; `and()` is
      true, `or()` and `xor()` are false.

    Args:
        trigger: the math of the trigger, which is not changed

    Returns:
        the root function

    Raises:
        NotImplementedError: if the trigger has no continuous root function: an
            equality or inequality, which holds at a single point, or a boolean
            which is neither a relation, a logical operator nor a constant, e.g. a
            boolean variable or a `piecewise`
    """
    ast_type = trigger.getType()
    operands = [trigger.getChild(k) for k in range(trigger.getNumChildren())]
    if ast_type in _GREATER or ast_type in _LESS:
        if len(operands) < 2:
            raise NotImplementedError("A relation of a single operand.")
        roots = []
        for left, right in itertools.pairwise(operands):
            larger, smaller = (left, right) if ast_type in _GREATER else (right, left)
            difference = node(libsbml.AST_MINUS, larger.deepCopy(), smaller.deepCopy())
            roots.append(difference)
        return _extreme(libsbml.AST_FUNCTION_MIN, roots)
    if ast_type in _NUMBERS:
        # a number is true unless it is 0
        return number(-1.0 if trigger.getValue() == 0 else 1.0)
    if ast_type == libsbml.AST_CONSTANT_TRUE:
        return number(1.0)
    if ast_type == libsbml.AST_CONSTANT_FALSE:
        return number(-1.0)
    if ast_type == libsbml.AST_LOGICAL_AND:
        roots = [trigger_root(operand) for operand in operands] or [number(1.0)]
        return _extreme(libsbml.AST_FUNCTION_MIN, roots)
    if ast_type == libsbml.AST_LOGICAL_OR:
        roots = [trigger_root(operand) for operand in operands] or [number(-1.0)]
        return _extreme(libsbml.AST_FUNCTION_MAX, roots)
    if ast_type == libsbml.AST_LOGICAL_NOT and len(operands) == 1:
        return negated(trigger_root(operands[0]))
    if ast_type == libsbml.AST_LOGICAL_XOR:
        # xor(x, y) holds where exactly one holds, xor(x, y, z) is xor(xor(x, y), z)
        roots = [trigger_root(operand) for operand in operands] or [number(-1.0)]
        root = roots[0]
        for other in roots[1:]:
            root = node(
                libsbml.AST_FUNCTION_MAX,
                node(
                    libsbml.AST_FUNCTION_MIN,
                    root.deepCopy(),
                    negated(other.deepCopy()),
                ),
                node(libsbml.AST_FUNCTION_MIN, negated(root), other),
            )
        return root
    if ast_type == libsbml.AST_LOGICAL_IMPLIES and len(operands) == 2:
        x, y = operands
        return node(libsbml.AST_FUNCTION_MAX, negated(trigger_root(x)), trigger_root(y))
    raise NotImplementedError(
        f"The trigger '{libsbml.formulaToL3String(trigger)}' has no continuous root "
        f"function."
    )
