"""
Create latex from AstNode for rendering.

Some replacements necessary

/ <- \frac

replace  '__' --> '_'
make {} around all formula parts

"""

import sympy
from sympy import latex


def astnode_to_latex(astnode):
    pass


def string_to_latex(string, symbols):
    pass


if __name__ == "__main__":
    # TODO: keep order
    # TODO: keep brackets
    # TODO: make species bold

    # sympy solution (autosimplification alters the order and the brackets)
    from sympy import Symbol, sympify

    scale_f = Symbol("scale_f")
    Vmax_bA = Symbol("Vmax_bA")
    Km_A = Symbol("Km_A")
    e__A = Symbol("e__A")
    c__A = Symbol("c__A")

    from sympy.core.sympify import kernS

    s = 'scale_f * (Vmax_bA / Km_A) * ((e__A - c__A) / (1 + e__A / Km_A + c__A / Km_A))'
    expr = sympify(s)
    print(expr)
    expr = kernS(s)
    print(expr)

    expr = sympify("(e__A - c__A)")
    latex_str = latex(expr, order=None, mode='equation', itex=True,
                      mul_symbol='dot',
                      symbol_names={
                          e__A: 'A_{(e)}',
                          c__A: 'A_{(c)}',
                      })
    print(latex_str)

    # Equation solution, necessary to make replacements
    import Equation
    from Equation import Expression

    fn = Expression(s, ["scale_f", "Vmax_bA", "Km_A", 'e__A', 'c__a'])
    print(fn)
