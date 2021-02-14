"""Helper functions for evaluation of mathml expressions.

In this namespace all the possible names occuring in formula strings have to be defined.

In build in python are
    *, /, +, -
    and, or, not
"""
from math import *

import libsbml


def product(*args):
    """Product calculation."""
    res = 1.0
    for arg in args:
        res *= arg
    return res


def sqr(x):
    """Square calculation."""
    return x * x


def root(a, b):
    """Root calculation."""
    return a ** (1 / b)


def xor(*args):
    """XOR calculation."""
    foundZero = 0
    foundOne = 0
    for a in args:
        if not a:
            foundZero = 1
        else:
            foundOne = 1
    if foundZero and foundOne:
        return 1
    else:
        return 0


def piecewise(*args):
    """Piecewise calculation."""
    Nargs = len(args)
    for k in range(0, Nargs - 1, 2):
        if args[k + 1]:
            return args[k]
    else:
        return args[Nargs - 1]


"""
def pow(x, y):
    return x**y


def gt(a, b):
    if a > b:
        return 1
    else:
        return 0


def lt(a, b):
    if a < b:
        return 1
    else:
        return 0


def geq(a, b):
    if a >= b:
        return 1
    else:
        return 0


def leq(a, b):
    if a <= b:
        return 1
    else:
        return 0


def neq(a, b):
    if a != b:
        return 1
    else:
        return 0


def f_not(a):
    if a == 1:
        return 0
    else:
        return 1


def f_and(*args):
    for a in args:
        if a != 1:
            return 0
    return 1


def f_or(*args):
    for a in args:
        if a != 0:
            return 1
    return 0
"""


def evaluableMathML(astnode, variables=None, array=False):
    """Create evaluable python string."""
    if variables is None:
        variables = {}
    # replace variables with provided values
    for key, value in variables.items():
        astnode.replaceArgument(key, libsbml.parseFormula(str(value)))

    # get formula
    # formula = libsbml.formulaToL3String(astnode)
    settings = libsbml.L3ParserSettings()  # type: libsbml.L3ParserSettings
    settings.setParseUnits(False)
    settings.setParseCollapseMinus(True)

    formula = libsbml.formulaToL3StringWithSettings(astnode, settings)

    # <replacements>
    formula = formula.replace("&&", "and")
    formula = formula.replace("||", "or")
    formula = formula.replace("^", "**")

    return formula


def evaluateMathML(astnode, variables=None, array=False):
    """Evaluate MathML string with given set of variable and parameter values.

    :param astnode: astnode of MathML string
    :type astnode: libsbml.ASTNode
    :param variables: dictionary of var : value
    :type variables: dict
    :param parameters: dictionary of par : value
    :type parameters: dict
    :return: value of evaluated MathML
    :rtype: float
    """
    if variables is None:
        variables = {}
    formula = evaluableMathML(astnode, variables=variables, array=array)
    print(formula)
    # return the evaluated formula
    return eval(formula)


if __name__ == "__main__":
    mathmlStr = """
           <math xmlns="http://www.w3.org/1998/Math/MathML">
                <piecewise>
                  <piece>
                    <cn type="integer"> 8 </cn>
                    <apply>
                      <lt/>
                      <ci> x </ci>
                      <cn type="integer"> 4 </cn>
                    </apply>
                  </piece>
                  <piece>
                    <cn> 0.1 </cn>
                    <apply>
                      <and/>
                      <apply>
                        <leq/>
                        <cn type="integer"> 4 </cn>
                        <ci> x </ci>
                      </apply>
                      <apply>
                        <lt/>
                        <ci> x </ci>
                        <cn type="integer"> 6 </cn>
                      </apply>
                    </apply>
                  </piece>
                  <otherwise>
                    <cn type="integer"> 8 </cn>
                  </otherwise>
                </piecewise>
              </math>
    """

    # evaluate the function with the values
    astnode = libsbml.readMathMLFromString(mathmlStr)

    y = 5
    res = evaluateMathML(astnode, variables={"x": "y"})
    print("Result:", res)
