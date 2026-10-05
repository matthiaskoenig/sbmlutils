"""Text of a model written into code and documents.

Every name, unit and other free text is written through `single_line`, which removes
all line breaks, so that the text of a model can never leave the comment it is
written into and become code; `tex_text` additionally escapes the latex special
characters. The ids written into code are checked to be SIds (`ValueError`
otherwise), which libsbml does not guarantee: it reads a document with an invalid id
and only reports an error.
"""

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
}


def tex_text(value: object) -> str:
    r"""Make text safe inside a latex `\text{}` on a single line.

    Args:
        value: text to write, rendered with `str`

    Returns:
        the text on a single line with the latex special characters escaped
    """
    return "".join(_TEX_SPECIAL.get(char, char) for char in single_line(value))


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
