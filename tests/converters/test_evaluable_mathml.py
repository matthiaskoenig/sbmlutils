"""Tests for the conversion of MathML to formula strings."""

import libsbml

from sbmlutils.converters.mathml import evaluableMathML


def test_evaluable_mathml_keeps_input_ast() -> None:
    """Replacing variables must not modify the ASTNode of the caller."""
    ast = libsbml.parseL3Formula("x + 1")
    assert evaluableMathML(ast, variables={"x": 5}) == "5 + 1"
    assert libsbml.formulaToL3String(ast) == "x + 1"
