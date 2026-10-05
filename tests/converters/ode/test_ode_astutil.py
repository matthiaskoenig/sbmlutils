"""Test the math helpers of the ODE export."""

import libsbml
import pytest

from sbmlutils.converters.ode.astutil import (
    drop_zero_terms,
    is_number,
    name,
    negated,
    number,
    signed_sum,
    walk,
)


def parse(text: str) -> libsbml.ASTNode:
    """Math of an infix formula."""
    ast = libsbml.parseL3Formula(text)
    assert ast is not None, libsbml.getLastParseL3Error()
    return ast


def formula(ast: libsbml.ASTNode) -> str:
    """Infix formula of the math, as libsbml writes it."""
    return str(libsbml.formulaToL3String(ast))


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2", "-2"),
        ("-x", "x"),
        ("b - 1", "1 - b"),
        ("2 * J", "-2 * J"),
        ("f * J", "-f * J"),
        ("J / c", "-J / c"),
        ("min(a, b)", "-min(a, b)"),
        ("x", "-x"),
    ],
)
def test_negated(text: str, expected: str) -> None:
    """A negation carries the sign on a number, a difference or a first factor."""
    assert formula(negated(parse(text))) == expected


def test_signed_sum() -> None:
    """The terms are written with their signs, the zero terms are dropped."""
    terms = [
        (-1, name("J0")),
        (1, parse("2 * J1")),
        (1, number(0.0)),
        (1, name("J2")),
        (-1, parse("f * J3")),
        (-1, name("J4")),
    ]
    assert formula(signed_sum(terms)) == "-J0 + 2 * J1 + J2 - f * J3 - J4"
    assert formula(signed_sum([(1, number(0.0))])) == "0"
    assert formula(signed_sum([(-1, parse("2 * J"))])) == "-2 * J"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a + 0", "a"),
        ("0 + a - 0", "a"),
        ("0 - a", "-a"),
        ("a + -b", "a - b"),
        ("k * (a + 0)", "k * a"),
        ("0 + 0", "0"),
        ("a * 0", "a * 0"),
    ],
)
def test_drop_zero_terms(text: str, expected: str) -> None:
    """The zero terms of every sum are dropped, a product keeps its factors."""
    assert formula(drop_zero_terms(parse(text))) == expected


def test_is_number_and_walk() -> None:
    """A number is recognized by its value, the walk visits every node."""
    assert is_number(parse("0"), 0.0)
    assert is_number(parse("2.5"))
    assert not is_number(parse("x"))
    assert [n.getName() for n in walk(parse("a + b * c")) if n.isName()] == [
        "a",
        "b",
        "c",
    ]
