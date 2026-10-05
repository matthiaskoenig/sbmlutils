"""Test the text helpers of the ODE export."""

import libsbml
import pytest

from sbmlutils.converters.ode.text import (
    check_math_sids,
    check_sid,
    markdown_text,
    single_line,
    tex_text,
    typst_text,
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
        ("<a|b>", r"\textless{}a\textbar{}b\textgreater{}"),
        ("τ = 2 µs", r"\ensuremath{\tau} = 2 \ensuremath{\mu}s"),
        ("Ωο", r"\ensuremath{\Omega}o"),
        ("x ≤ y → z", r"x \ensuremath{\leq} y \ensuremath{\rightarrow} z"),
        ("äöü ©", "äöü ©"),
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


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a $x$ #b _c_", r"a \$x\$ \#b \_c\_"),
        ("<script>", r"\<script\>"),
        ("a\\b", r"a\\b"),
        ("@ref [x] `y` ~ *e*", r"\@ref \[x\] \`y\` \~ \*e\*"),
        # a comment, a dash and a soft hyphen, a single `/` and `-` stay
        ("http://x // c", r"http:\//x \// c"),
        ("a--b a---b a-?b", r"a\--b a\-\--b a\-?b"),
        ("a - b mol/s", "a - b mol/s"),
        # a list, a numbered list, a heading and a term at the start only
        ("- a - b", r"\- a - b"),
        ("+ a + b", r"\+ a + b"),
        ("= h = i", r"\= h = i"),
        ("/ t: x", r"\/ t: x"),
        ("1. first", r"1\. first"),
        ("123. first", r"123\. first"),
        ("in 2. place", "in 2. place"),
        ("a | b", "a | b"),
        ("a\nb", "a b"),
    ],
)
def test_typst_text(text: str, expected: str) -> None:
    """The characters of typst markup are escaped, line breaks removed."""
    assert typst_text(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("a | d", r"a \| d"),
        ("<script>", "&lt;script&gt;"),
        ("a & b", "a &amp; b"),
        ("&lt;", "&amp;lt;"),
        ("*a* _b_ `c` ~s~", r"\*a\* \_b\_ \`c\` \~s\~"),
        ("$x$ [l](u) ![i]", r"\$x\$ \[l\](u) !\[i\]"),
        ("a\\b", r"a\\b"),
        # a heading, a list and a numbered list at the start only
        ("# h #1", r"\# h #1"),
        ("- l - m", r"\- l - m"),
        ("+ n + o", r"\+ n + o"),
        ("1. first", r"1\. first"),
        ("12) first", r"12\) first"),
        ("in 2. place", "in 2. place"),
        ("a\nb", "a b"),
    ],
)
def test_markdown_text(text: str, expected: str) -> None:
    """The characters of markdown are escaped, `&`, `<` and `>` are entities."""
    assert markdown_text(text) == expected
