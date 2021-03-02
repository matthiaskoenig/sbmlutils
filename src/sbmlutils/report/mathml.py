"""Sympy based content to presentation MathML conversion.

A common problem in rendering MathML is that the content MathML is difficult to read.
The presentation MathML has a much better rendering and improves understandability.
This module uses stylesheets for the conversion of content MathMl -> presention MathML.

This is currently just a proof of principle.
Content MathML would improve readability of reports.

MathML is currently rendered with MathJax http://docs.mathjax.org/en/latest/
in the report. This should be updated using sympy for converstion to latex
or presentation mathml

astnode -> content MathML -> expr -> latex
formula (annotation) -> expr -> latex

see also: https://docs.sympy.org/dev/modules/printing.html#module-sympy.printing.mathml
"""
import logging
from typing import Any, List, Optional, Set

import libsbml
from sympy import Symbol, sympify
from sympy.printing.latex import latex
from sympy.printing.mathml import MathMLContentPrinter, MathMLPresentationPrinter


logger = logging.getLogger(__name__)


def formula_to_astnode(
    formula: str, model: Optional[libsbml.Model] = None
) -> libsbml.ASTNode:
    """Convert formula string to ASTNode.

    :param formula: SBML formula string
    :param model: libsbml.Model
    :return: libsbml.ASTNode
    """
    if model:
        astnode = libsbml.parseL3FormulaWithModel(formula, model)
    else:
        astnode = libsbml.parseL3Formula(formula)
    if not astnode:
        logging.error(f"Formula could not be parsed: '{formula}'")
        logging.error(libsbml.getLastParseL3Error())
        raise ValueError(
            f"Formula could not be parsed: '{formula}'.\n"
            f"{libsbml.getLastParseL3Error()}"
        )
    return astnode


def cmathml_to_astnode(cmathml: str) -> libsbml.ASTNode:
    """Convert Content MathML string to ASTNode.

    :param cmathml: SBML Content MathML string
    :return: libsbml.ASTNode
    """
    return libsbml.readMathMLFromString(cmathml)


def astnode_to_expression(
    astnode: libsbml.ASTNode, model: Optional[libsbml.Model] = None
) -> Any:
    """Convert AstNode to sympy expression.

    An AST node in libSBML is a recursive tree structure; each node has a type,
    a pointer to a value, and a list of children nodes. Each ASTNode node may
    have none, one, two, or more children depending on its type. There are
    node types to represent numbers (with subtypes to distinguish integer,
    real, and rational numbers), names (e.g., constants or variables),
    simple mathematical operators, logical or relational operators and
    functions.

    see also: http://sbml.org/Software/libSBML/docs/python-api/libsbml-math.html

    :param model:
    :param astnode: libsbml.ASTNode
    :return: sympy expression
    """
    formula = libsbml.formulaToL3String(astnode)
    return formula_to_expression(formula, model=model)


# python 3 reserved keywords (and sympy lambda)
restricted_words = [
    "and",
    "as",
    "assert",
    "break",
    "class",
    "continue",
    "def",
    "del",
    "elif",
    "else",
    "except",
    "finally",
    "false",
    "for",
    "from",
    "global",
    "if",
    "import",
    "in",
    "is",
    "lambda",
    "nonlocal",
    "none",
    "not",
    "or",
    "pass",
    "raise",
    "return",
    "True",
    "try",
    "with",
    "while",
    "yield",
] + ["gamma", "log", "rf"]


def formula_to_expression(formula: str, model: Optional[libsbml.Model] = None) -> Any:
    """Parse sympy expression from given formula string.

    :param model:
    :param formula: SBML formula string
    :return: sympy expression
    """
    # round trip to remove unnecessary inline dimensions
    ast_node = formula_to_astnode(formula, model=model)
    variables = _get_variables(ast_node)

    settings = libsbml.L3ParserSettings()
    settings.setParseUnits(False)
    formula = libsbml.formulaToL3StringWithSettings(ast_node, settings=settings)

    # create sympy expressions with variables and formula
    formula = _replace_piecewise(formula)
    formula = formula.replace("&&", "&")
    formula = formula.replace("||", "|")
    # handle special lambda syntax sympy and restricted eval symbols
    for word in restricted_words:
        formula = formula.replace(word, f"_{word}")

    try:
        expr = sympify(
            formula,
            locals={v: Symbol(f"{v}") for v in variables},
        )
    except Exception as e:
        logger.error(f"Formula could not be sympified: '{formula}'")
        print("formula", formula)
        print("variables", variables)
        raise e

    return expr


def _get_variables(astnode: libsbml.ASTNode, variables: Set[str] = None) -> Set[str]:
    """Get variables from ASTNode."""
    if variables is None:
        variables: Set[str] = set()  # type: ignore

    num_children = astnode.getNumChildren()
    if num_children == 0:
        if astnode.isName():
            name = astnode.getName()
            variables.add(name)  # type: ignore
    else:
        for k in range(num_children):
            child: libsbml.ASTNode = astnode.getChild(k)
            _get_variables(child, variables=variables)

    return variables  # type: ignore


def _replace_piecewise(formula: str) -> str:
    """Replace libsbml piecewise with sympy Piecewise.

    Handles replacement recursively.

    libsbml.piecewise
    | x1, y1, [x2, y2,] [...] [z] |
    A piecewise function: if (y1), x1.  Otherwise, if (y2), x2, etc.  Otherwise, z.

    sympy.Piecewise
    Piecewise( (expr,cond), (expr,cond), … )
    Each argument is a 2-tuple defining an expression and condition
    The conds are evaluated in turn returning the first that is True.
    If any of the evaluated conds are not determined explicitly False, e.g. x < 1,
    the function is returned in symbolic form.
    If the function is evaluated at a place where all conditions are False, nan will
    be returned. Pairs where the cond is explicitly False, will be removed.

    :param formula: SBML formula string
    :return: formula string
    """
    while True:
        index = formula.find("piecewise(")
        if index == -1:
            break

        # process piecewise
        search_idx = index + 9

        # init counters
        bracket_open = 0
        pieces = []
        piece_chars: List[str] = []

        while search_idx < len(formula):
            c = formula[search_idx]
            if c == ",":
                if bracket_open == 1:
                    pieces.append("".join(piece_chars).strip())
                    piece_chars = []
                else:
                    piece_chars.append(c)
            else:
                if c == "(":
                    if bracket_open != 0:
                        piece_chars.append(c)
                    bracket_open += 1
                elif c == ")":
                    if bracket_open != 1:
                        piece_chars.append(c)
                    bracket_open -= 1
                else:
                    piece_chars.append(c)

            if bracket_open == 0:
                pieces.append("".join(piece_chars).strip())
                break

            # next character
            search_idx += 1

        # find end index
        if (len(pieces) % 2) == 1:
            pieces.append("True")  # last condition is True

        sympy_pieces = []
        for k in range(0, int(len(pieces) / 2)):
            sympy_pieces.append(f"({pieces[2*k]}, {pieces[2*k+1]})")

        new_str = f"Piecewise({', '.join(sympy_pieces)})"
        formula = formula.replace(formula[index : search_idx + 1], new_str)

    return formula


def astnode_to_mathml(
    astnode: libsbml.ASTNode, printer: str = "content", **settings: Any
) -> str:
    """Convert formula to presentation/content MathML.

    This does not use ASTNode serialization, but parsing of the
    corresponding formula due to differences in MathML!

    :param printer:
    :param astnode: ASTNode
    :param settings:
    :return: Content or presentation MathML
    """
    expr = astnode_to_expression(astnode)
    return _expression_to_mathml(expr=expr, printer=printer, **settings)


def formula_to_mathml(formula: str, printer: str = "content", **settings: Any) -> str:
    """Convert formula to MathML.

    :param formula: SBML formula string
    :param printer: 'content' or 'presentation'
    :param settings:
    :return: Content or presentation MathML
    """
    expr = formula_to_expression(formula=formula)
    return _expression_to_mathml(expr=expr, printer=printer, **settings)


def _expression_to_mathml(expr: Any, printer: str = "content", **settings: Any) -> str:
    """Convert sympy expression to MathML.

    :param expr: sympy expression
    :param printer: 'content' or 'presentation'
    :param settings:
    :return: Content or presentation MathML
    """
    if printer == "presentation":
        s = MathMLPresentationPrinter(settings)
    else:
        s = MathMLContentPrinter(settings)
    xml = s._print(sympify(expr))
    s.apply_patch()
    pretty_xml = xml.toprettyxml()
    s.restore_patch()
    # hack words back
    for word in restricted_words:
        pretty_xml = pretty_xml.replace(f"_{word}", word)

    return str(pretty_xml)


def cmathml_to_pmathml(
    cmathml: str, model: Optional[libsbml.Model] = None, **settings: Any
) -> str:
    """Convert Content MathML to PresentationMathML.

    :param cmathml: Content MathML
    :param settings:
    :return: Presentation MathML
    """
    astnode = cmathml_to_astnode(cmathml)
    expr = astnode_to_expression(astnode, model=model)
    return _expression_to_mathml(expr, printer="presentation", **settings)


def formula_to_latex(
    formula: str, model: Optional[libsbml.Model] = None, **settings: Any
) -> str:
    """Convert formula to latex.

    :param model:
    :param formula: SBML formula string
    :param settings:
    :return: Latex string
    """
    expr = formula_to_expression(formula, model=model)
    latex_str = latex(expr, mul_symbol="dot", **settings)  # type: ignore
    # hack words back
    for word in restricted_words:
        latex_str = latex_str.replace(f"_{word}", word)
    return str(latex_str)


def astnode_to_latex(
    astnode: libsbml.ASTNode, model: Optional[libsbml.Model] = None, **settings: Any
) -> str:
    """Convert AstNode to Latex.

    :param model:
    :param astnode: libsbml.ASTNode
    :param settings:
    :return: Latex string
    """
    # FIXME: remove redundancy with function above
    expr = astnode_to_expression(astnode, model=model)
    latex_str = latex(expr, mul_symbol="dot", **settings)  # type: ignore
    # hack words back
    for word in restricted_words:
        latex_str = latex_str.replace(f"_{word}", word)
    return str(latex_str)


def cmathml_to_latex(cmathml: str, **settings: Any) -> str:
    """Convert Content MathML to Latex.

    :param cmathml: Content Mathml string
    :param settings:
    :return: Latex string
    """
    astnode = cmathml_to_astnode(cmathml)
    return astnode_to_latex(astnode, **settings)
