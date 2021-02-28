"""Helper functions for evaluation of mathml expressions.

In this namespace all the possible names occuring in formula strings have to be defined.

In build in python are
    *, /, +, -
    and, or, not
"""
from math import *
from typing import Any, Dict, Optional, Tuple

import libsbml


def product(*args: float) -> float:
    """Product calculation."""
    res = 1.0
    for arg in args:
        res *= arg
    return res


def sqr(x: float) -> float:
    """Square calculation."""
    return x * x


def root(a: float, b: float) -> float:
    """Root calculation."""
    return a ** (1 / b)


def xor(*args: float) -> int:
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


def piecewise(*args: float) -> float:
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


def evaluableMathML(astnode: libsbml.ASTNode, variables: Optional[Dict] = None) -> str:
    """Create evaluable python formula string from ASTNode."""
    if variables is None:
        variables = {}
    # replace variables with provided values
    for key, value in variables.items():
        astnode.replaceArgument(key, libsbml.parseFormula(str(value)))

    # parse formula
    settings = libsbml.L3ParserSettings()  # type: libsbml.L3ParserSettings
    settings.setParseUnits(False)
    settings.setParseCollapseMinus(True)
    formula: str = libsbml.formulaToL3StringWithSettings(astnode, settings)

    # <replacements>
    formula = formula.replace("&&", "and")
    formula = formula.replace("||", "or")
    formula = formula.replace("^", "**")

    return formula


def evaluateMathML(astnode: libsbml.ASTNode, variables: Optional[Dict] = None) -> Any:
    """Evaluate MathML string with given set of variable and parameter values.

    :param astnode: astnode of MathML string
    :param variables: dictionary of var : value
    :return: value of evaluated MathML
    """
    if variables is None:
        variables = {}
    formula = evaluableMathML(astnode, variables=variables)
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
