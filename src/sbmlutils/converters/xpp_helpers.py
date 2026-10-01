"""Some testing of astnode manipulations.

alp(Vm) = abar / (1 + k1 * exp(-2 * d1 * 96.485 * Vm / 8.313424 / (310)) / c)
"""

import logging
import re

import libsbml

logger = logging.getLogger(__name__)


def find_names_in_ast(
    ast: libsbml.ASTNode, names: list[str] | None = None
) -> list[str]:
    """Find all names in given astnode.

    Names are the variables in the formula.

    :param ast:
    :param names:
    :return:
    """
    if names is None:
        names = []

    # name for this node
    if ast.getType() == libsbml.AST_NAME:
        names.append(ast.getName())

    for k in range(ast.getNumChildren()):
        ast_child = ast.getChild(k)
        find_names_in_ast(ast_child, names)

    return names


def replace_formula(
    formula: str, fid: str, old_args: list[str], new_args: list[str]
) -> str:
    """Replace information in given formula.

    :param formula:
    :param fid:
    :param old_args:
    :param new_args:
    :return:
    """
    new_formula = formula
    pattern = re.compile(rf"(?<!\w){fid}\s*\(.*?\)")

    for m in pattern.finditer(formula):
        g = formula[m.start() :]
        content = _top_bracket_content(g)

        # replace with the new arguments
        # TODO: find the real number of arguments (if arguments are functions this calculation is wrong)
        n_args = len(content.split(","))
        if n_args < len(old_args) + len(new_args):
            old_phrase = fid + "(" + content + ")"
            new_phrase = fid + "(" + content + "," + ",".join(new_args) + ")"
            new_formula = new_formula.replace(old_phrase, new_phrase)

    return new_formula


# This is a workaround due to not using a real parser.
def _top_bracket_content(s: str) -> str:
    """Get content of top bracket."""
    toret = _bracket_stack(s)
    start_idx = sorted(toret.keys())[0]
    end_idx = toret[start_idx]
    return s[start_idx + 1 : end_idx]


def _bracket_stack(s: str) -> dict[int, int]:
    """Get bracket stack."""
    toret: dict[int, int] = {}
    pstack = []
    for i, c in enumerate(s):
        if c == "(":
            pstack.append(i)
        elif c == ")":
            if len(pstack) == 0:
                return toret
            toret[pstack.pop()] = i

    return toret
