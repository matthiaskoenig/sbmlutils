"""Text of a model written into code and documents.

Every name, unit and other free text is written through `single_line`, which removes
all line breaks, so that the text of a model can never leave the comment it is
written into and become code. The text of a document is escaped for its markup, so
that it is written as it is and never read as markup: `tex_text` for LaTeX,
`typst_text` for typst and `markdown_text` for markdown. The ids written into code are checked to be SIds (`ValueError`
otherwise), which libsbml does not guarantee: it reads a document with an invalid id
and only reports an error.
"""

import re
import unicodedata

import libsbml


def single_line(value: object) -> str:
    r"""Make text safe inside a single-line comment of every target language.

    Every line break (`\n`, `\r`, the unicode line and paragraph separators) and
    every other control character is replaced by a space, so that the text ends
    where the line ends.

    Args:
        value: text to write, rendered with `str`

    Returns:
        the text on a single line
    """
    return "".join(
        " " if unicodedata.category(char) in {"Cc", "Zl", "Zp"} else char
        for char in str(value)
    )


_TEX_SPECIAL = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "^": r"\textasciicircum{}",
    "_": r"\_",
    "%": r"\%",
    "~": r"\textasciitilde{}",
    # the OT1 encoding of the default fonts has no glyphs of these, `<` would be `¡`
    "<": r"\textless{}",
    ">": r"\textgreater{}",
    "|": r"\textbar{}",
}

# The greek letters, which the fonts of LaTeX hold in math only. A letter which
# looks like a latin one has no command, `Α` is `A`.
_GREEK = {
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "ζ": "zeta",
    "η": "eta",
    "θ": "theta",
    "ι": "iota",
    "κ": "kappa",
    "λ": "lambda",
    "μ": "mu",
    "ν": "nu",
    "ξ": "xi",
    "ο": "o",
    "π": "pi",
    "ρ": "rho",
    "ς": "varsigma",
    "σ": "sigma",
    "τ": "tau",
    "υ": "upsilon",
    "φ": "phi",
    "χ": "chi",
    "ψ": "psi",
    "ω": "omega",
    "Γ": "Gamma",
    "Δ": "Delta",
    "Θ": "Theta",
    "Λ": "Lambda",
    "Ξ": "Xi",
    "Π": "Pi",
    "Σ": "Sigma",
    "Υ": "Upsilon",
    "Φ": "Phi",
    "Ψ": "Psi",
    "Ω": "Omega",
    "Α": "A",
    "Β": "B",
    "Ε": "E",
    "Ζ": "Z",
    "Η": "H",
    "Ι": "I",
    "Κ": "K",
    "Μ": "M",
    "Ν": "N",
    "Ο": "O",
    "Ρ": "P",
    "Τ": "T",
    "Χ": "X",
}

# the symbols of science which the text fonts of LaTeX do not hold
_TEX_SYMBOLS = {
    "µ": r"\ensuremath{\mu}",
    "→": r"\ensuremath{\rightarrow}",
    "←": r"\ensuremath{\leftarrow}",
    "↔": r"\ensuremath{\leftrightarrow}",
    "⇌": r"\ensuremath{\rightleftharpoons}",
    "≤": r"\ensuremath{\leq}",
    "≥": r"\ensuremath{\geq}",
    "≠": r"\ensuremath{\neq}",
    "≈": r"\ensuremath{\approx}",
    "∞": r"\ensuremath{\infty}",
    "−": r"\ensuremath{-}",
}

_TEX = {
    **_TEX_SPECIAL,
    **{
        char: rf"\ensuremath{{\{name}}}" if len(name) > 1 else name
        for char, name in _GREEK.items()
    },
    **_TEX_SYMBOLS,
}


def tex_text(value: object) -> str:
    r"""Make text safe inside a latex `\text{}` or a paragraph, on a single line.

    The special characters of LaTeX are escaped, `<`, `>` and `|` written as their
    commands, and the greek letters and the symbols of science which the text fonts
    of LaTeX do not hold are written as math, `τ` is `\ensuremath{\tau}`, so that
    the text compiles with pdflatex, xelatex and lualatex alike.

    Args:
        value: text to write, rendered with `str`

    Returns:
        the text on a single line with the latex special characters escaped
    """
    return "".join(_TEX.get(char, char) for char in single_line(value))


# The characters of typst markup which a backslash escapes wherever they are:
# strong, emphasis, code, math, labels, references, content and the non-breaking
# space `~`.
_TYPST_SPECIAL = re.compile(r"[\\#$*_@<>\[\]`~]")
# The characters which are markup only in their place: `-` begins a list at the
# start and the dashes `--` and the soft hyphen `-?`, `+` a numbered list and `=` a
# heading at the start, `/` a term at the start and a comment `//`; a dot after a
# number at the start begins a numbered list, `1.`.
_TYPST_PLACED = re.compile(r"^[-+=/]|-(?=[-?])|/(?=/)")
_TYPST_ENUMERATION = re.compile(r"^(\d+)\.")


def typst_text(value: object) -> str:
    r"""Make text safe in typst markup, on a single line.

    The characters of typst markup are escaped with a backslash, `#b` is `\#b`,
    `$x$` is `\$x\$`, those which are markup only in their place there, a list
    `- a` is `\- a`, a dash `a--b` is `a\--b`, a comment `//` is `\//`, so that the
    text is written as it is and a single `-` or `/` keeps its place in the text.

    Args:
        value: text to write, rendered with `str`

    Returns:
        the escaped text
    """
    text = _TYPST_SPECIAL.sub(r"\\\g<0>", single_line(value))
    text = _TYPST_PLACED.sub(r"\\\g<0>", text)
    return _TYPST_ENUMERATION.sub(r"\1\\.", text)


# The characters of markdown which a backslash escapes wherever they are: emphasis,
# code, links and images, tables, strikethrough and the math of GitHub, `$x$`.
_MARKDOWN_SPECIAL = re.compile(r"[\\`*_\[\]|~$]")
# The characters which are markup only at the start: a heading `#`, a list `-` and
# `+`, a numbered list `1.` and `1)`.
_MARKDOWN_PLACED = re.compile(r"^[#+-]")
_MARKDOWN_ENUMERATION = re.compile(r"^(\d+)([.)])")
_HTML = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def markdown_text(value: object) -> str:
    r"""Make text safe in GitHub flavored markdown, on a single line.

    The characters of markdown are escaped with a backslash, `|` is `\|`, so that
    the text stays in its table cell, those which are markup only at the start
    there, a list `- a` is `\- a`, and `&`, `<` and `>` are HTML entities, so that
    no text becomes HTML, `<script>` is `&lt;script&gt;`.

    Args:
        value: text to write, rendered with `str`

    Returns:
        the escaped text
    """
    text = "".join(_HTML.get(char, char) for char in single_line(value))
    text = _MARKDOWN_SPECIAL.sub(r"\\\g<0>", text)
    text = _MARKDOWN_PLACED.sub(r"\\\g<0>", text)
    return _MARKDOWN_ENUMERATION.sub(r"\1\\\2", text)


def check_sid(sid: str) -> str:
    """Check that an id which is written into code is an SId.

    libsbml reads a document whose ids are not SIds and only reports an error, so
    an id can hold any text, e.g. a line of code.

    Args:
        sid: id to check

    Returns:
        the id

    Raises:
        ValueError: if the id is not an SId
    """
    if not libsbml.SyntaxChecker.isValidSBMLSId(sid):
        raise ValueError(f"The id {sid!r} is not an SId and cannot be written as code.")
    return sid


def check_math_sids(ast: libsbml.ASTNode) -> None:
    """Check that every identifier in the math is an SId.

    The identifiers are the names and the calls of function definitions.

    Args:
        ast: the math

    Raises:
        ValueError: if an identifier is not an SId
    """
    if ast.getType() in {libsbml.AST_NAME, libsbml.AST_FUNCTION}:
        check_sid(ast.getName())
    for k in range(ast.getNumChildren()):
        check_math_sids(ast.getChild(k))
