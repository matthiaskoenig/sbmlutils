"""
Some testing of astnode manipulations

alp(Vm) = abar / (1 + k1 * exp(-2 * d1 * 96.485 * Vm / 8.313424 / (310)) / c)
"""

import libsbml

def ast_info(ast):
    print(ast)
    print(ast.getType(), ast.getName())


def find_names_in_ast(ast, names=None):
    """ Find all names in given astnode.
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




if __name__ == "__main__":
    # parse ast
    formula = "abar / (1 + k1 * exp(-2 * d1 * 96.485 * Vm / 8.313424 / (310)) / c)"
    ast = libsbml.parseL3Formula(formula)

    # print info
    ast_info(ast)

    # iterate the ast
    names = find_names_in_ast(ast)
    print(names)
    print(libsbml.AST_NAME)

    print(type(5))
