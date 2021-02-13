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

# TODO: render jinja example HTML

"""
from pathlib import Path

from sympy.printing.mathml import mathml, print_mathml, MathMLPresentationPrinter, \
    MathMLContentPrinter
from sympy.printing.latex import latex

import logging
import libsbml
from sympy import sympify


def formula_to_astnode(formula: str) -> libsbml.ASTNode:
    """Parses astnode from formula"""
    astnode = libsbml.parseL3Formula(formula)
    if not astnode:
        logging.error("Formula could not be parsed: '{}'".format(formula))
        logging.error(libsbml.getLastParseL3Error())
    return astnode


def parse_mathml_str(mathml_str: str):
    astnode = libsbml.readMathMLFromString(mathml_str)  # type: libsbml.ASTNode
    return parse_astnode(astnode)


def parse_formula(formula: str):
    astnode = formula_to_astnode(formula)
    return parse_astnode(astnode)


def parse_astnode(astnode: libsbml.ASTNode):
    """
    An AST node in libSBML is a recursive tree structure; each node has a type,
    a pointer to a value, and a list of children nodes. Each ASTNode node may
    have none, one, two, or more children depending on its type. There are
    node types to represent numbers (with subtypes to distinguish integer,
    real, and rational numbers), names (e.g., constants or variables),
    simple mathematical operators, logical or relational operators and
    functions.

    see also: http://sbml.org/Software/libSBML/docs/python-api/libsbml-math.html

    :param mathml:
    :return:
    """
    formula = libsbml.formulaToL3String(astnode)

    # iterate over ASTNode and figure out variables
    # variables = _get_variables(astnode)

    # create sympy expression
    expr = expr_from_formula(formula)

    # print(formula, expr)
    return expr


def expr_from_formula(formula: str):
    """Parses sympy expression from given formula string."""

    # [2] create sympy expressions with variables and formula
    # necessary to map the expression trees
    # create symbols
    formula = _replace_piecewise(formula)
    formula = formula.replace("&&", "&")
    formula = formula.replace("||", "|")
    expr = sympify(formula)

    return expr


def _replace_piecewise(formula):
    """Replaces libsbml piecewise with sympy piecewise."""
    while True:
        index = formula.find("piecewise(")
        if index == -1:
            break

        # process piecewise
        search_idx = index + 9

        # init counters
        bracket_open = 0
        pieces = []
        piece_chars = []

        while search_idx < len(formula):
            c = formula[search_idx]
            if c == ",":
                if bracket_open == 1:
                    pieces.append("".join(piece_chars).strip())
                    piece_chars = []
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
        new_str = f"Piecewise({','.join(sympy_pieces)})"
        formula = formula.replace(formula[index : search_idx + 1], new_str)

    return formula


def astnode_to_mathml(formula, printer="content", **settings):
    """Conversion of formula to presentation/content MathML.

    This does not use ASTNode serialization, but parsing of the
    corresponding formula due to differences in MathML!
    """
    expr = expr_from_formula(formula=formula)
    return expr_to_mathml(expr=expr, printer=printer, **settings)


def formula_to_mathml(formula, printer="content", **settings):
    expr = expr_from_formula(formula=formula)
    return expr_to_mathml(expr=expr, printer=printer, **settings)


def expr_to_mathml(expr, printer="content", **settings):
    if printer == 'presentation':
        s = MathMLPresentationPrinter(settings)
    else:
        s = MathMLContentPrinter(settings)
    xml = s._print(sympify(expr))
    s.apply_patch()
    pretty_xml = xml.toprettyxml()
    s.restore_patch()
    return pretty_xml


def cmathml_to_pmathml(sbml_mathml: str, **settings):
    expr = parse_mathml_str(sbml_mathml)
    return expr_to_mathml(expr, printer="presentation", **settings)


def cmathml_to_latex(sbml_mathml: str, **settings):
    expr = parse_mathml_str(sbml_mathml)
    return latex(expr, mul_symbol="dot")

def formula_to_latex(formula: str, **settings):
    expr = expr_from_formula(formula)
    return latex(expr, mul_symbol="dot")

if __name__ == "__main__":
    formula = "3**5 / x * glc"

    print('-' * 80)
    print(formula_to_mathml(formula, printer="content"))
    print('-' * 80)
    print(formula_to_mathml(formula, printer="presentation"))

    base_dir = Path(__file__).parent / "resources"
    mathml_path = base_dir / "content_mathml.xml"
    with open(mathml_path, "r") as f_mathml:
        cmathml = f_mathml.read()
        pmathml = cmathml_to_pmathml(cmathml)
        print(pmathml)
        print("-" * 80)
        print(cmathml_to_latex(cmathml))

    formula = "GK_Vmax * GK_gc_free * (atp/(GK_k_atp + atp)) * f_gly * (power(glc,GK_n)/(power(glc,GK_n) + power(GK_k_glc, GK_n)))"
    print("-" * 80)
    print(formula_to_latex(formula))

