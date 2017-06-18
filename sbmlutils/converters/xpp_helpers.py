"""
Some testing of astnode manipulations

alp(Vm) = abar / (1 + k1 * exp(-2 * d1 * 96.485 * Vm / 8.313424 / (310)) / c)
"""
from __future__ import print_function, absolute_import
import re
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


##################################
# Formula replacement helpers
##################################

def replace_formula(formula, fid, old_args, new_args):
    """ Replace information in given formula.

    :param formula:
    :param fid:
    :param old_args:
    :param new_args:
    :return:
    """
    new_formula = formula
    pattern = re.compile('(?<!\w){}\s*\(.*?\)'.format(fid))

    for m in pattern.finditer(formula):
        g = formula[m.start():]
        content = top_bracket_content(g)

        if False:
            print('-'*80)
            print('formula:\t', formula)
            # print('groups:\t', groups)
            print('match:', m.start(), m.group())
            print('g:', g)
            print('bracket_content: ', content)

        # replace with the new arguments
        # TODO: find the real number of arguments (if arguments are functions this calculation is wrong)
        n_args = len(content.split(','))
        if n_args < len(old_args) + len(new_args):
            old_phrase = fid + '(' + content + ')'
            new_phrase = fid + '(' + content + ',' + ','.join(new_args) + ')'
            new_formula = new_formula.replace(old_phrase, new_phrase)
        if False:
            print('new_formula:\t', new_formula)
            print('-' * 80)

    return new_formula

# This is a workaround due to not using a real parser.
def top_bracket_content(s):
    """ Get content of top bracket.

    :param s:
    :return:
    """
    toret = bracket_stack(s)
    start_idx = sorted(toret.keys())[0]
    end_idx = toret[start_idx]
    return s[start_idx+1:end_idx]


def bracket_stack(s):
    toret = {}
    pstack = []
    for i, c in enumerate(s):
        if c == '(':
            pstack.append(i)
        elif c == ')':
            if len(pstack) == 0:
                return toret
            toret[pstack.pop()] = i

    return toret



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

    print('------------------------')

    # s = "vtest(v(a, b, c), x(a, b, c), d)*(abc)"
    s = 'hv(t-1,sharpness) - hv(t-2,sharpness) + (hv(t-5,sharpness) - hv(t-6,sharpness)))'
    toret = bracket_stack(s)
    print(toret)
    test = top_bracket_content(s)
    print('formula:', s)
    print('content first top bracket:', test)
