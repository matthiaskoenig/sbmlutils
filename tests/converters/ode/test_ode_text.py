"""Test the text helpers of the ODE export."""

import libsbml
import pytest

from sbmlutils.converters.ode.text import (
    check_math_sids,
    check_sid,
    single_line,
    tex_text,
)


@pytest.mark.parametrize(
    "separator", ["\n", "\r", "\r\n", "\u2028", "\u2029", "\u0085", "\t"]
)
def test_single_line(separator: str) -> None:
    """Every line break and control character becomes a space."""
    assert single_line(f"a{separator}b") == "a" + " " * len(separator) + "b"


def test_single_line_renders_with_str() -> None:
    """A value which is no string is rendered with `str`."""
    assert single_line(1.5) == "1.5"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a_b$", r"a\_b\$"),
        ("{x}", r"\{x\}"),
        ("&#%", r"\&\#\%"),
        ("a\\b", r"a\textbackslash{}b"),
        ("^~", r"\textasciicircum{}\textasciitilde{}"),
        ("a\nb", "a b"),
    ],
)
def test_tex_text(text: str, expected: str) -> None:
    """The latex special characters are escaped, line breaks removed."""
    assert tex_text(text) == expected


def test_check_sid() -> None:
    """An SId is returned as it is."""
    assert check_sid("a_1") == "a_1"


@pytest.mark.parametrize("sid", ["1a", "a b", "a\nb", "a-b", ""])
def test_check_sid_rejects(sid: str) -> None:
    """An id which is no SId raises."""
    with pytest.raises(ValueError, match="is not an SId"):
        check_sid(sid)


def test_check_math_sids() -> None:
    """Math whose identifiers are SIds passes."""
    check_math_sids(libsbml.parseL3Formula("a + f(b, time) * 2"))


@pytest.mark.parametrize(("formula", "child"), [("a + b", 1), ("f(a) + 1", 0)])
def test_check_math_sids_rejects(formula: str, child: int) -> None:
    """A name or a function call which is no SId raises."""
    ast = libsbml.parseL3Formula(formula)
    ast.getChild(child).setName("1x")
    with pytest.raises(ValueError, match="'1x'"):
        check_math_sids(ast)
