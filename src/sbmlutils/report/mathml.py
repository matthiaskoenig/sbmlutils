"""Rendering of formulas and Content MathML.

A common problem in rendering MathML is that the content MathML is difficult to read.
The presentation MathML has a much better rendering and improves understandability.
This module uses stylesheets for the conversion of content MathMl -> presentation
MathML.

see also: https://docs.sympy.org/dev/modules/printing.html#module-sympy.printing.mathml
"""

import re
from functools import lru_cache
from typing import Optional, Set

import libsbml
import lxml.etree as ET

from sbmlutils import RESOURCES_DIR, log


logger = log.get_logger(__name__)

xslt_cmml2pmml = ET.parse(str(RESOURCES_DIR / "xslt" / "ctopff.xsl"))
xslt_pmml2tex = ET.parse(str(RESOURCES_DIR / "xslt" / "xsltml" / "mmltex.xsl"))


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
        logger.error(f"Formula could not be parsed: '{formula}'")
        logger.error(libsbml.getLastParseL3Error())
        raise ValueError(
            f"Formula could not be parsed: '{formula}'.\n"
            f"{libsbml.getLastParseL3Error()}"
        )
    return astnode


def formula_to_latex(formula: str, model: Optional[libsbml.Model] = None) -> str:
    """Convert formula string to latex."""
    astnode = formula_to_astnode(formula, model)
    return astnode_to_latex(astnode)


def cmathml_to_astnode(cmathml: str) -> libsbml.ASTNode:
    """Convert Content MathML string to ASTNode.

    :param cmathml: SBML Content MathML string
    :return: libsbml.ASTNode
    """
    return libsbml.readMathMLFromString(cmathml)


def astnode_to_latex(astnode: libsbml.ASTNode) -> str:
    """Convert ASTNode to Latex using XSLT transformation."""
    cmml_str: str = libsbml.writeMathMLToString(astnode)
    cmml_str = cmml_str.replace('<?xml version="1.0" encoding="UTF-8"?>', "")

    return cmathml_to_latex(cmml_str)


@lru_cache(maxsize=10000)
def cmathml_to_latex(cmml_str: str) -> str:
    """Content MathML to latex conversion using XSLT transformation."""

    # content MathML -> presentation MathML
    cmml_dom = ET.fromstring(cmml_str)
    transform1 = ET.XSLT(xslt_cmml2pmml)
    pmml_dom = transform1(cmml_dom)

    # content MathML -> latex
    transform2 = ET.XSLT(xslt_pmml2tex)
    tex_str = str(transform2(pmml_dom))

    # remove equation symbols
    tex_str = tex_str.replace("$", "")

    # fix piecewise
    tex_str = tex_str.replace(r"\hfill", "")
    tex_str = tex_str.replace(r"\multicolumn{2}{c}", "")
    tex_str = tex_str.replace(r"\left(\{\begin{array}{ccc}", r"\begin{cases} ")
    tex_str = tex_str.replace(r"\end{array}\right)", r"\end{cases}")
    tex_str = tex_str.replace(r"\{\begin{array}{ccc}", r"\begin{cases} ")
    tex_str = tex_str.replace(r"\end{array}", r"\end{cases}")

    # fix lambda function
    tex_str = tex_str.replace(r"}\mathit", r"}, \mathit")
    tex_str = tex_str.replace(r"\lambda ", r"\lambda(")
    tex_str = tex_str.replace(r"}.", "}) =")

    # cleanup symbols
    tex_str = _fix_mathit_symbols(tex_str)

    # print(tex_str)
    # pmml_bytes = ET.tostring(pmml_dom, pretty_print=True)
    # pmml_str = pmml_bytes.decode("UTF-8")

    return tex_str


# symbols replaced in latex
greek_symbols = [
    "alpha",
    "beta",
    "gamma",
    "Gamma" "delta",
    "Delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "Lambda",  # no lowercase due to function definition
    "mu",
    "nu",
    "omicron",
    "pi" "rho",
    "sigma",
    "tau",
    "upsilon",
    "Upsilon",
    "phi",
    "Phi",
    "chi",
    "psi",
    "Psi",
    "omega",
    "Omega",
]


def symbol_to_latex(symbol: str) -> str:
    """Convert symbol to latex by packing in mathit and escaping underscores."""
    symbol = symbol.replace(r"_", r"\_")
    symbol = r"\mathit{" + symbol + "}"
    return _fix_mathit_symbols(symbol)


def _fix_mathit_symbols(tex_str: str) -> str:
    """Heuristic replacements for better latex rendering.

    Single underscores are set down.
    Greek symbols are rendered (with exception of small lambda).
    """
    # fix single underscores in variable names
    #  \mathit{group1\_group2} -> \mathit{group1_{group2}}
    matches = re.findall(r"\\mathit{([a-zA-Z0-9]+)\\_([a-zA-Z0-9]+)}", tex_str)
    if matches:
        for m in matches:
            tex_str = tex_str.replace(
                r"\mathit{" + m[0] + r"\_" + m[1] + "}",
                r"\mathit{" + m[0] + r"_{" + m[1] + "}}",
            )

    # replace greek symbols
    for symbol in greek_symbols:
        tex_str = tex_str.replace(
            r"\mathit{" + symbol + "}", r"\mathit{" + f"\{symbol}" + "}"  # noqa: W605
        )

    return tex_str


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
