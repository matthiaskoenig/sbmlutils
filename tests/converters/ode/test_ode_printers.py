"""Test the math printers of the ODE export."""

import ast
import math
from collections.abc import Callable
from pathlib import Path

import libsbml
import numpy as np
import pytest
from ode_helpers import (
    FORMULAS,
    JULIA_PACKAGES,
    compile_latex,
    compile_typst,
    julia_command,
    rscript_command,
    run_julia,
    run_r,
    sbml_with_rate,
    tectonic_command,
)

from sbmlutils.converters.ode.printers import PRINTERS
from sbmlutils.converters.ode.printers.base import (
    MathPrinter,
    Precedence,
    Printed,
    Term,
)
from sbmlutils.converters.ode.printers.document import DocumentPrinter
from sbmlutils.converters.ode.printers.julia import JuliaPrinter
from sbmlutils.converters.ode.printers.latex import LatexPrinter
from sbmlutils.converters.ode.printers.python import PythonPrinter
from sbmlutils.converters.ode.printers.r import RPrinter
from sbmlutils.converters.ode.printers.typst import TypstPrinter

SYMBOLS = {"A": "A", "k": "k", "f": "f"}


def parse(formula: str) -> libsbml.ASTNode:
    """Math of an L3 infix formula."""
    math = libsbml.parseL3Formula(formula)
    assert math is not None, libsbml.getLastParseL3Error()
    return math


def mathml(content: str) -> libsbml.ASTNode:
    """Math of a MathML content element, for the constructs the infix syntax lacks."""
    math = libsbml.readMathMLFromString(
        f'<math xmlns="http://www.w3.org/1998/Math/MathML">{content}</math>'
    )
    assert math is not None, content
    return math


def py(formula: str) -> str:
    """Python of an L3 infix formula."""
    return PythonPrinter().print(parse(formula), SYMBOLS)


def jl(formula: str) -> str:
    """Julia of an L3 infix formula."""
    return JuliaPrinter().print(parse(formula), SYMBOLS)


def r(formula: str) -> str:
    """R of an L3 infix formula."""
    return RPrinter().print(parse(formula), SYMBOLS)


def py_condition(formula: str) -> str:
    """Python of an L3 infix formula used as a condition."""
    return PythonPrinter().print_condition(parse(formula), SYMBOLS)


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("k*A", "k * A"),
        ("-A^2", "-A ** 2"),
        ("(-2)^2", "(-2) ** 2"),
        ("2^3^2", "2 ** 3 ** 2"),
        ("A - (k - 1)", "A - (k - 1)"),
        ("A/(k*2)", "A / (k * 2)"),
        ("log(2, A)", "np.log(A) / np.log(2)"),
        ("rem(A, 2)", "np.fmod(A, 2)"),
        ("piecewise(k, A > 1, 0)", "k if A > 1 else 0"),
        ("A > 1", "float(A > 1)"),
        ("f(A, k)", "f(A, k)"),
        ("time", "t"),
    ],
)
def test_python_golden(formula: str, expected: str) -> None:
    """The python of the constructs of the brief."""
    assert py(formula) == expected


# the rate laws of `tests/converters/test_odefac.py`, verified against roadrunner,
# with their python; it differs from the python of `odefac.python_math` in three
# places: a boolean used as a number is a `float`, `and`, `or` and `implies` in a
# condition are not wrapped, and a logarithm to base 10 and a square root use the
# numpy function
PYTHON_FORMULAS: dict[str, str] = {
    "k*A": "k * A",
    "ln(A) + log10(A) + log(2, A) + exp(-k)": (
        "np.log(A) + np.log10(A) + np.log(A) / np.log(2) + np.exp(-k)"
    ),
    "piecewise(k, A > 1 && !(A > 10) || xor(true, false), 2*k)": (
        "k if A > 1 and not A > 10 or bool(True) ^ bool(False) else 2 * k"
    ),
    "piecewise(k, (A < 1) || (A >= 10), 3*k, A == 3, 0.1)": (
        "k if A < 1 or A >= 10 else 3 * k if A == 3 else 0.1"
    ),
    "piecewise(k, A > 1)": "k if A > 1 else np.nan",
    "rem(A, 2) + rem(-7, A) + quotient(7, A) + root(3, A) + sqrt(A) + A^2 + pow(A, k)": (
        "np.fmod(A, 2) + np.fmod(-7, A) + np.trunc(7 / A) + A ** (1.0 / 3)"
        " + np.sqrt(A) + A ** 2 + A ** k"
    ),
    "max(A, k, 1) + min(A, k) + abs(-A) + floor(A/2) + ceil(A/2)": (
        "max(A, k, 1) + min(A, k) + np.abs(-A) + np.floor(A / 2) + np.ceil(A / 2)"
    ),
    "factorial(3) + pi + exponentiale": "math.gamma(3 + 1) + np.pi + np.e",
    "implies(A > 1, k > 1) + (A != 2) + (1 < A <= 5)": (
        "float(not A > 1 or k > 1) + float(A != 2) + float(1 < A and A <= 5)"
    ),
    "piecewise(1, A < INF, 0) + piecewise(1, 5 > -INF, 0)": (
        "(1 if A < np.inf else 0) + (1 if 5 > -np.inf else 0)"
    ),
    "sin(A) + cos(A) + tan(A) + sec(A) + csc(A) + cot(A)": (
        "np.sin(A) + np.cos(A) + np.tan(A) + 1.0 / np.cos(A) + 1.0 / np.sin(A)"
        " + 1.0 / np.tan(A)"
    ),
    "sinh(k) + cosh(k) + tanh(k) + sech(k) + csch(k) + coth(k)": (
        "np.sinh(k) + np.cosh(k) + np.tanh(k) + 1.0 / np.cosh(k) + 1.0 / np.sinh(k)"
        " + 1.0 / np.tanh(k)"
    ),
    "arcsin(k) + arccos(k) + arctan(k) + arcsinh(k) + arctanh(k)": (
        "np.arcsin(k) + np.arccos(k) + np.arctan(k) + np.arcsinh(k) + np.arctanh(k)"
    ),
    "arcsec(A) + arccsc(A) + arccot(A) + arccosh(A) + arcsech(k) + arccsch(k)": (
        "np.arccos(1.0 / A) + np.arcsin(1.0 / A) + np.arctan(1.0 / A) + np.arccosh(A)"
        " + np.arccosh(1.0 / k) + np.arcsinh(1.0 / k)"
    ),
    "arccoth(A)": "np.arctanh(1.0 / A)",
    "piecewise(k*time, true, 0) + 2^-1 + -A^2 + 1/2 + (-2)^2 + 2^3^2": (
        "(k * t if True else 0) + 2 ** -1 + -A ** 2 + 1 / 2 + (-2) ** 2 + 2 ** 3 ** 2"
    ),
}


@pytest.mark.parametrize(("formula", "expected"), PYTHON_FORMULAS.items())
def test_python_formulas(formula: str, expected: str) -> None:
    """The python of the rate laws verified against roadrunner, valid python."""
    code = py(formula)
    assert code == expected
    ast.parse(code, mode="eval")


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        # sums and products, left associative
        ("A + k + 1", "A + k + 1"),
        ("A + (k + 1)", "A + (k + 1)"),
        ("(A + k) * 2", "(A + k) * 2"),
        ("A - k - 1", "A - k - 1"),
        ("A - (k + 1)", "A - (k + 1)"),
        ("A / k / 2", "A / k / 2"),
        ("A / (k / 2)", "A / (k / 2)"),
        ("A * (k / 2)", "A * (k / 2)"),
        ("A / k * 2", "A / k * 2"),
        ("A + -k", "A + -k"),
        ("A * -k", "A * -k"),
        # unary minus binds weaker than the power, tighter than a product
        ("-(A + k)", "-(A + k)"),
        ("-(-A)", "-(-A)"),
        ("-A * k", "-A * k"),
        ("-(A * k)", "-(A * k)"),
        # power, right associative
        ("(A^2)^3", "(A ** 2) ** 3"),
        ("(-A)^2", "(-A) ** 2"),
        ("A^(k + 1)", "A ** (k + 1)"),
        ("A^-k", "A ** -k"),
        ("exp(A)^2", "np.exp(A) ** 2"),
        ("2 * A^2", "2 * A ** 2"),
        # functions which are expressions of their argument
        ("factorial(A + 1)", "math.gamma(A + 1 + 1)"),
        ("factorial(piecewise(1, A > 1, 2))", "math.gamma((1 if A > 1 else 2) + 1)"),
        ("quotient(A + 1, k * 2)", "np.trunc((A + 1) / (k * 2))"),
        ("2 * sec(A + k)", "2 * (1.0 / np.cos(A + k))"),
        ("A^sec(A)", "A ** (1.0 / np.cos(A))"),
        ("arcsec(A * k)", "np.arccos(1.0 / (A * k))"),
        ("root(3, A + 1)", "(A + 1) ** (1.0 / 3)"),
        ("root(k + 1, A)", "A ** (1.0 / (k + 1))"),
        ("root(2.0, A)", "np.sqrt(A)"),
        ("log(k, A) * 2", "np.log(A) / np.log(k) * 2"),
        ("2 / log(k, A)", "2 / (np.log(A) / np.log(k))"),
        ("log(10.0, A)", "np.log10(A)"),
        ("max(A + 1, piecewise(1, A > 1, 2))", "max(A + 1, 1 if A > 1 else 2)"),
        ("f(A + 1, k > 1)", "f(A + 1, float(k > 1))"),
        # piecewise
        (
            "piecewise(piecewise(1, A > 1, 2), k > 1, 3)",
            "(1 if A > 1 else 2) if k > 1 else 3",
        ),
        (
            "piecewise(1, A > 1, piecewise(2, k > 1, 3))",
            "1 if A > 1 else 2 if k > 1 else 3",
        ),
        ("piecewise(1, A > 1, 2, k > 1)", "1 if A > 1 else 2 if k > 1 else np.nan"),
        ("2 * piecewise(1, A > 1, 2)", "2 * (1 if A > 1 else 2)"),
        # logic used as a number
        ("!(A > 1)", "float(not A > 1)"),
        ("(A > 1) && (k > 1)", "float(A > 1 and k > 1)"),
        ("xor(A > 1, k > 1)", "float(bool(A > 1) ^ bool(k > 1))"),
        ("(A > 1) + 1", "float(A > 1) + 1"),
        ("true + false", "float(True) + float(False)"),
        ("max(A)", "A"),
        ("min(A + 1) * 2", "(A + 1) * 2"),
        # constants and numbers
        ("pi * exponentiale", "np.pi * np.e"),
        ("avogadro", "6.02214179e+23"),
        ("INF - NaN", "np.inf - np.nan"),
        ("1.5e-3", "0.0015"),
        ("-INF", "-np.inf"),
    ],
)
def test_python_math(formula: str, expected: str) -> None:
    """The python of every construct, with the parentheses its place requires."""
    code = py(formula)
    assert code == expected
    ast.parse(code, mode="eval")


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("A > 1", "A > 1"),
        ("!(A > 1 && k > 1)", "not (A > 1 and k > 1)"),
        ("(A > 1 || k > 1) && A < 5", "(A > 1 or k > 1) and A < 5"),
        # the infix syntax of libsbml gives && and || the same precedence
        ("A > 1 || k > 1 && A < 5", "(A > 1 or k > 1) and A < 5"),
        ("A > 1 || (k > 1 && A < 5)", "A > 1 or k > 1 and A < 5"),
        ("implies(A > 1, k > 1)", "not A > 1 or k > 1"),
        ("implies(A > 1 || k > 1, A < 5)", "not (A > 1 or k > 1) or A < 5"),
        ("xor(A > 1, k > 1, A < 5)", "bool(A > 1) ^ bool(k > 1) ^ bool(A < 5)"),
        ("!xor(A > 1, k > 1)", "not bool(A > 1) ^ bool(k > 1)"),
        ("true", "True"),
        ("piecewise(A > 1, k > 1, false)", "A > 1 if k > 1 else False"),
    ],
)
def test_python_condition(formula: str, expected: str) -> None:
    """The python of math used as a condition is a python bool."""
    code = py_condition(formula)
    assert code == expected
    ast.parse(code, mode="eval")


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        # relations with more than two operands are chained with `and`
        (
            '<apply><lt/><cn type="integer">1</cn><ci>A</ci><cn type="integer">5</cn>'
            "</apply>",
            "float(1 < A and A < 5)",
        ),
        # a relation of conditions compares them as numbers
        (
            "<apply><eq/><apply><gt/><ci>A</ci><ci>k</ci></apply>"
            "<apply><lt/><ci>A</ci><ci>k</ci></apply></apply>",
            "float(float(A > k) == float(A < k))",
        ),
        ("<apply><eq/><ci>A</ci></apply>", "float(True)"),
        # empty and unary n-ary operators
        ("<apply><and/></apply>", "float(True)"),
        ("<apply><or/></apply>", "float(False)"),
        ("<apply><xor/></apply>", "float(False)"),
        (
            "<apply><and/><apply><gt/><ci>A</ci><ci>k</ci></apply></apply>",
            "float(A > k)",
        ),
        ("<apply><plus/></apply>", "0"),
        ("<apply><times/></apply>", "1"),
        ("<apply><plus/><ci>A</ci></apply>", "A"),
        ("<apply><times/><ci>k</ci><ci>A</ci><ci>A</ci></apply>", "k * A * A"),
        # numbers
        ('<cn type="rational">1<sep/>2</cn>', "1 / 2"),
        (
            '<apply><times/><ci>k</ci><cn type="rational">1<sep/>2</cn></apply>',
            "k * (1 / 2)",
        ),
        ('<cn type="e-notation">1<sep/>3</cn>', "1000.0"),
        ('<cn type="integer">-2</cn>', "-2"),
        ('<apply><power/><cn type="integer">-2</cn><ci>A</ci></apply>', "(-2) ** A"),
        ("<apply><power/><cn>-2.5</cn><ci>A</ci></apply>", "(-2.5) ** A"),
        # logarithm and root without their qualifier
        ("<apply><log/><ci>A</ci></apply>", "np.log10(A)"),
        ("<apply><root/><ci>A</ci></apply>", "np.sqrt(A)"),
    ],
)
def test_python_mathml(content: str, expected: str) -> None:
    """The python of the constructs which only MathML can write."""
    code = PythonPrinter().print(mathml(content), SYMBOLS)
    assert code == expected
    ast.parse(code, mode="eval")


def test_formulas_of_odefac() -> None:
    """The python goldens are the rate laws shared by the tests of the dialects."""
    assert list(PYTHON_FORMULAS) == FORMULAS
    assert list(JULIA_FORMULAS) == FORMULAS
    assert list(R_FORMULAS) == FORMULAS


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("<apply><and/></apply>", "True"),
        ("<apply><or/></apply>", "False"),
        ("<apply><eq/><ci>A</ci></apply>", "True"),
        ("<false/>", "False"),
    ],
)
def test_python_boolean_condition(content: str, expected: str) -> None:
    """A boolean constant used as a condition stays a python bool."""
    assert PythonPrinter().print_condition(mathml(content), SYMBOLS) == expected


@pytest.mark.parametrize(
    "printer", [PythonPrinter, JuliaPrinter, RPrinter, LatexPrinter, TypstPrinter]
)
@pytest.mark.parametrize(
    "content",
    [
        "<apply><max/></apply>",
        "<apply><min/></apply>",
        "<apply><sin/><ci>A</ci><ci>k</ci></apply>",
        "<apply><abs/></apply>",
        "<apply><exp/><ci>A</ci><ci>k</ci></apply>",
    ],
)
def test_function_arity(printer: type[MathPrinter], content: str) -> None:
    """A function of the dialect is written only with the arguments it takes."""
    with pytest.raises(NotImplementedError, match="arguments"):
        printer().print(mathml(content), SYMBOLS)


def test_symbols() -> None:
    """Every identifier is written as its symbol."""
    symbols = {"A": "y[0]", "k": "p[1]", "f": "f_fun"}
    code = PythonPrinter().print(parse("f(A, k) * A"), symbols)
    assert code == "f_fun(y[0], p[1]) * y[0]"


@pytest.mark.parametrize(("formula", "sid"), [("B + 1", "B"), ("g(A)", "g")])
def test_unmapped_identifier_raises(formula: str, sid: str) -> None:
    """An identifier without a symbol is never written."""
    with pytest.raises(NotImplementedError, match=f"'{sid}'"):
        py(formula)


def test_unmapped_identifier_message() -> None:
    """The message names the identifier and the printer."""
    with pytest.raises(NotImplementedError, match=r"'B'.*python printer"):
        py("B + 1")


@pytest.mark.parametrize("formula", ["rateOf(A)", "delay(A, 1)"])
def test_python_unsupported(formula: str) -> None:
    """A construct the python code cannot express raises."""
    with pytest.raises(NotImplementedError):
        py(formula)


def test_unsupported_message() -> None:
    """The message names the math which is not supported and the printer."""
    with pytest.raises(NotImplementedError) as error:
        py("A + rateOf(A)")
    assert str(error.value) == (
        "The math 'rateOf(A)' is not supported by the python printer."
    )


def test_unsupported_by_default() -> None:
    """A printer without hooks supports only the arithmetic of the engine."""

    class Minimal(MathPrinter):
        name = "minimal"

    printer = Minimal()
    assert printer.print(parse("-A * (k + 1) / 2"), SYMBOLS) == "-A * (k + 1) / 2"
    for formula in ["A^2", "piecewise(1, A > 1, 0)", "sin(A)", "rem(A, k)"]:
        with pytest.raises(NotImplementedError, match="minimal printer"):
            printer.print(parse(formula), SYMBOLS)


def test_precedence() -> None:
    """The precedence of the expressions, from the weakest binding."""
    assert [p.name for p in sorted(Precedence)] == [
        "CONDITIONAL",
        "OR",
        "AND",
        "NOT",
        "COMPARISON",
        "XOR",
        "SUM",
        "PRODUCT",
        "UNARY",
        "POWER",
        "ATOM",
    ]
    assert Precedence.CONDITIONAL == 1
    assert Precedence.ATOM == 11


def test_registry() -> None:
    """The printers are registered by the name of their dialect."""
    assert PRINTERS["python"] is PythonPrinter
    assert PRINTERS["julia"] is JuliaPrinter
    assert PRINTERS["r"] is RPrinter
    assert PRINTERS["latex"] is LatexPrinter
    assert PRINTERS["typst"] is TypstPrinter
    assert all(printer.name == name for name, printer in PRINTERS.items())


# --- julia --------------------------------------------------------------------------

# every number is a Float64 literal: integer arithmetic of julia overflows and a power
# of integers with a negative exponent throws; a power, a root, a logarithm and the
# functions with a restricted domain are those of NaNMath, which are NaN outside
# their real domain where the functions of Base throw a DomainError
JULIA_FORMULAS: dict[str, str] = {
    "k*A": "k * A",
    "ln(A) + log10(A) + log(2, A) + exp(-k)": (
        "NaNMath.log(A) + NaNMath.log10(A) + NaNMath.log(A) / NaNMath.log(2.0)"
        " + exp(-k)"
    ),
    "piecewise(k, A > 1 && !(A > 10) || xor(true, false), 2*k)": (
        "A > 1.0 && !(A > 10.0) || xor(true, false) ? k : 2.0 * k"
    ),
    "piecewise(k, (A < 1) || (A >= 10), 3*k, A == 3, 0.1)": (
        "A < 1.0 || A >= 10.0 ? k : A == 3.0 ? 3.0 * k : 0.1"
    ),
    "piecewise(k, A > 1)": "A > 1.0 ? k : NaN",
    "rem(A, 2) + rem(-7, A) + quotient(7, A) + root(3, A) + sqrt(A) + A^2 + pow(A, k)": (
        "rem(A, 2.0) + rem(-7.0, A) + trunc(7.0 / A) + NaNMath.pow(A, 1.0 / 3.0)"
        " + NaNMath.sqrt(A) + NaNMath.pow(A, 2.0) + NaNMath.pow(A, k)"
    ),
    "max(A, k, 1) + min(A, k) + abs(-A) + floor(A/2) + ceil(A/2)": (
        "max(A, k, 1.0) + min(A, k) + abs(-A) + floor(A / 2.0) + ceil(A / 2.0)"
    ),
    "factorial(3) + pi + exponentiale": "gamma(3.0 + 1.0) + pi + exp(1.0)",
    "implies(A > 1, k > 1) + (A != 2) + (1 < A <= 5)": (
        "Float64(!(A > 1.0) || k > 1.0) + Float64(A != 2.0)"
        " + Float64(1.0 < A && A <= 5.0)"
    ),
    "piecewise(1, A < INF, 0) + piecewise(1, 5 > -INF, 0)": (
        "(A < Inf ? 1.0 : 0.0) + (5.0 > -Inf ? 1.0 : 0.0)"
    ),
    "sin(A) + cos(A) + tan(A) + sec(A) + csc(A) + cot(A)": (
        "NaNMath.sin(A) + NaNMath.cos(A) + NaNMath.tan(A) + 1.0 / NaNMath.cos(A)"
        " + 1.0 / NaNMath.sin(A) + 1.0 / NaNMath.tan(A)"
    ),
    "sinh(k) + cosh(k) + tanh(k) + sech(k) + csch(k) + coth(k)": (
        "sinh(k) + cosh(k) + tanh(k) + 1.0 / cosh(k) + 1.0 / sinh(k) + 1.0 / tanh(k)"
    ),
    "arcsin(k) + arccos(k) + arctan(k) + arcsinh(k) + arctanh(k)": (
        "NaNMath.asin(k) + NaNMath.acos(k) + atan(k) + asinh(k) + NaNMath.atanh(k)"
    ),
    "arcsec(A) + arccsc(A) + arccot(A) + arccosh(A) + arcsech(k) + arccsch(k)": (
        "NaNMath.acos(1.0 / A) + NaNMath.asin(1.0 / A) + atan(1.0 / A)"
        " + NaNMath.acosh(A) + NaNMath.acosh(1.0 / k) + asinh(1.0 / k)"
    ),
    "arccoth(A)": "NaNMath.atanh(1.0 / A)",
    "piecewise(k*time, true, 0) + 2^-1 + -A^2 + 1/2 + (-2)^2 + 2^3^2": (
        "(true ? k * t : 0.0) + NaNMath.pow(2.0, -1.0) + -NaNMath.pow(A, 2.0)"
        " + 1.0 / 2.0 + NaNMath.pow(-2.0, 2.0)"
        " + NaNMath.pow(2.0, NaNMath.pow(3.0, 2.0))"
    ),
}


@pytest.mark.parametrize(("formula", "expected"), JULIA_FORMULAS.items())
def test_julia_formulas(formula: str, expected: str) -> None:
    """The julia of the rate laws verified against roadrunner."""
    assert jl(formula) == expected


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        # the constructs of the brief
        ("-A^2", "-NaNMath.pow(A, 2.0)"),
        ("(-2)^2", "NaNMath.pow(-2.0, 2.0)"),
        ("piecewise(k, A > 1, 0)", "A > 1.0 ? k : 0.0"),
        ("log(2, A)", "NaNMath.log(A) / NaNMath.log(2.0)"),
        ("rem(-7, 2)", "rem(-7.0, 2.0)"),
        # power, NaN for a negative base and a fractional exponent
        ("2^-1", "NaNMath.pow(2.0, -1.0)"),
        ("A^-k", "NaNMath.pow(A, -k)"),
        ("(A^2)^3", "NaNMath.pow(NaNMath.pow(A, 2.0), 3.0)"),
        ("A^(k + 1)", "NaNMath.pow(A, k + 1.0)"),
        ("10^20", "NaNMath.pow(10.0, 20.0)"),
        # quotient as roadrunner, the truncated quotient of the floats
        ("quotient(1, 0.1)", "trunc(1.0 / 0.1)"),
        ("factorial(A + 1)", "gamma(A + 1.0 + 1.0)"),
        ("root(k + 1, A)", "NaNMath.pow(A, 1.0 / (k + 1.0))"),
        # piecewise
        (
            "piecewise(piecewise(1, A > 1, 2), k > 1, 3)",
            "k > 1.0 ? (A > 1.0 ? 1.0 : 2.0) : 3.0",
        ),
        (
            "piecewise(1, A > 1, piecewise(2, k > 1, 3))",
            "A > 1.0 ? 1.0 : k > 1.0 ? 2.0 : 3.0",
        ),
        ("2 * piecewise(1, A > 1, 2)", "2.0 * (A > 1.0 ? 1.0 : 2.0)"),
        # logic used as a number
        ("!(A > 1)", "Float64(!(A > 1.0))"),
        ("xor(A > 1, k > 1, A < 5)", "Float64(xor(A > 1.0, k > 1.0, A < 5.0))"),
        ("true + false", "Float64(true) + Float64(false)"),
        ("f(A + 1, k > 1)", "f(A + 1.0, Float64(k > 1.0))"),
        # constants and numbers
        ("avogadro", "6.02214179e23"),
        ("1e-5", "1.0e-5"),
        ("1.5e-3", "0.0015"),
        ("INF - NaN", "Inf - NaN"),
        ("-INF", "-Inf"),
        ("time", "t"),
        ("max(A)", "A"),
    ],
)
def test_julia_math(formula: str, expected: str) -> None:
    """The julia of the constructs, with the parentheses their place requires."""
    assert jl(formula) == expected


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("A > 1", "A > 1.0"),
        ("!(A > 1 && k > 1)", "!(A > 1.0 && k > 1.0)"),
        ("!!(A > 1)", "!(!(A > 1.0))"),
        ("(A > 1 || k > 1) && A < 5", "(A > 1.0 || k > 1.0) && A < 5.0"),
        ("implies(A > 1 || k > 1, A < 5)", "!(A > 1.0 || k > 1.0) || A < 5.0"),
        ("true", "true"),
        ("piecewise(A > 1, k > 1, false)", "k > 1.0 ? A > 1.0 : false"),
    ],
)
def test_julia_condition(formula: str, expected: str) -> None:
    """The julia of math used as a condition is a julia Bool."""
    assert JuliaPrinter().print_condition(parse(formula), SYMBOLS) == expected


# --- R ------------------------------------------------------------------------------

R_FORMULAS: dict[str, str] = {
    "k*A": "k * A",
    "ln(A) + log10(A) + log(2, A) + exp(-k)": "log(A) + log10(A) + log(A, 2) + exp(-k)",
    "piecewise(k, A > 1 && !(A > 10) || xor(true, false), 2*k)": (
        "if (isTRUE(A > 1) && !isTRUE(A > 10) || xor(TRUE, FALSE)) k else 2 * k"
    ),
    "piecewise(k, (A < 1) || (A >= 10), 3*k, A == 3, 0.1)": (
        "if (isTRUE(A < 1) || isTRUE(A >= 10)) k"
        " else if (isTRUE(A == 3)) 3 * k else 0.1"
    ),
    "piecewise(k, A > 1)": "if (isTRUE(A > 1)) k else NaN",
    "rem(A, 2) + rem(-7, A) + quotient(7, A) + root(3, A) + sqrt(A) + A^2 + pow(A, k)": (
        "sign(A) * (abs(A) %% abs(2)) + sign(-7) * (abs(-7) %% abs(A))"
        " + trunc(7 / A) + A ^ (1 / 3) + sqrt(A) + A ^ 2 + A ^ k"
    ),
    "max(A, k, 1) + min(A, k) + abs(-A) + floor(A/2) + ceil(A/2)": (
        "max(A, k, 1) + min(A, k) + abs(-A) + floor(A / 2) + ceiling(A / 2)"
    ),
    "factorial(3) + pi + exponentiale": "gamma(3 + 1) + pi + exp(1)",
    "implies(A > 1, k > 1) + (A != 2) + (1 < A <= 5)": (
        "as.numeric(!isTRUE(A > 1) || isTRUE(k > 1)) + as.numeric(!isTRUE(A == 2))"
        " + as.numeric(isTRUE(1 < A) && isTRUE(A <= 5))"
    ),
    "piecewise(1, A < INF, 0) + piecewise(1, 5 > -INF, 0)": (
        "(if (isTRUE(A < Inf)) 1 else 0) + (if (isTRUE(5 > -Inf)) 1 else 0)"
    ),
    "sin(A) + cos(A) + tan(A) + sec(A) + csc(A) + cot(A)": (
        "sin(A) + cos(A) + tan(A) + 1 / cos(A) + 1 / sin(A) + 1 / tan(A)"
    ),
    "sinh(k) + cosh(k) + tanh(k) + sech(k) + csch(k) + coth(k)": (
        "sinh(k) + cosh(k) + tanh(k) + 1 / cosh(k) + 1 / sinh(k) + 1 / tanh(k)"
    ),
    "arcsin(k) + arccos(k) + arctan(k) + arcsinh(k) + arctanh(k)": (
        "asin(k) + acos(k) + atan(k) + asinh(k) + atanh(k)"
    ),
    "arcsec(A) + arccsc(A) + arccot(A) + arccosh(A) + arcsech(k) + arccsch(k)": (
        "acos(1 / A) + asin(1 / A) + atan(1 / A) + acosh(A) + acosh(1 / k)"
        " + asinh(1 / k)"
    ),
    "arccoth(A)": "atanh(1 / A)",
    "piecewise(k*time, true, 0) + 2^-1 + -A^2 + 1/2 + (-2)^2 + 2^3^2": (
        "(if (TRUE) k * t else 0) + 2 ^ (-1) + -A ^ 2 + 1 / 2 + (-2) ^ 2 + 2 ^ 3 ^ 2"
    ),
}


@pytest.mark.parametrize(("formula", "expected"), R_FORMULAS.items())
def test_r_formulas(formula: str, expected: str) -> None:
    """The R of the rate laws verified against roadrunner."""
    assert r(formula) == expected


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        # the constructs of the brief
        ("-A^2", "-A ^ 2"),
        ("(-2)^2", "(-2) ^ 2"),
        ("piecewise(k, A > 1, 0)", "if (isTRUE(A > 1)) k else 0"),
        ("log(2, A)", "log(A, 2)"),
        # the remainder of `fmod` as roadrunner, exact for rem(1, 0.1)
        ("rem(-7, 2)", "sign(-7) * (abs(-7) %% abs(2))"),
        ("rem(A + 1, k * 2)", "sign(A + 1) * (abs(A + 1) %% abs(k * 2))"),
        ("2 * rem(A, k)", "2 * (sign(A) * (abs(A) %% abs(k)))"),
        # power, a negative exponent in parentheses
        ("2^-1", "2 ^ (-1)"),
        ("A^-k", "A ^ (-k)"),
        ("(A^2)^3", "(A ^ 2) ^ 3"),
        ("quotient(A + 1, k * 2)", "trunc((A + 1) / (k * 2))"),
        ("factorial(A + 1)", "gamma(A + 1 + 1)"),
        ("2 * sec(A + k)", "2 * (1 / cos(A + k))"),
        # piecewise, an `if` takes everything up to its end
        (
            "piecewise(piecewise(1, A > 1, 2), k > 1, 3)",
            "if (isTRUE(k > 1)) (if (isTRUE(A > 1)) 1 else 2) else 3",
        ),
        (
            "piecewise(1, A > 1, piecewise(2, k > 1, 3))",
            "if (isTRUE(A > 1)) 1 else if (isTRUE(k > 1)) 2 else 3",
        ),
        (
            "piecewise(1, A > 1, 2, k > 1)",
            "if (isTRUE(A > 1)) 1 else if (isTRUE(k > 1)) 2 else NaN",
        ),
        ("2 * piecewise(1, A > 1, 2)", "2 * (if (isTRUE(A > 1)) 1 else 2)"),
        ("piecewise(1, A > 1, 2) * 2", "(if (isTRUE(A > 1)) 1 else 2) * 2"),
        # logic used as a number
        ("!(A > 1)", "as.numeric(!isTRUE(A > 1))"),
        (
            "xor(A > 1, k > 1, A < 5)",
            "as.numeric(xor(xor(isTRUE(A > 1), isTRUE(k > 1)), isTRUE(A < 5)))",
        ),
        ("true + false", "as.numeric(TRUE) + as.numeric(FALSE)"),
        # constants and numbers
        ("avogadro", "6.02214179e+23"),
        ("1e-5", "1e-05"),
        ("INF - NaN", "Inf - NaN"),
        ("-INF", "-Inf"),
        ("time", "t"),
        ("max(A)", "A"),
    ],
)
def test_r_math(formula: str, expected: str) -> None:
    """The R of the constructs, with the parentheses their place requires."""
    assert r(formula) == expected


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("A > 1", "isTRUE(A > 1)"),
        ("!(A > 1 && k > 1)", "!(isTRUE(A > 1) && isTRUE(k > 1))"),
        (
            "(A > 1 || k > 1) && A < 5",
            "(isTRUE(A > 1) || isTRUE(k > 1)) && isTRUE(A < 5)",
        ),
        ("implies(A > 1, k > 1)", "!isTRUE(A > 1) || isTRUE(k > 1)"),
        ("true", "TRUE"),
        (
            "piecewise(A > 1, k > 1, false)",
            "if (isTRUE(k > 1)) isTRUE(A > 1) else FALSE",
        ),
    ],
)
def test_r_condition(formula: str, expected: str) -> None:
    """The R of math used as a condition is an R logical."""
    assert RPrinter().print_condition(parse(formula), SYMBOLS) == expected


@pytest.mark.parametrize("printer", [JuliaPrinter, RPrinter])
@pytest.mark.parametrize("formula", ["rateOf(A)", "delay(A, 1)"])
def test_julia_r_unsupported(printer: type[MathPrinter], formula: str) -> None:
    """A construct julia and R code cannot express raises."""
    with pytest.raises(NotImplementedError, match=f"{printer.name} printer"):
        printer().print(parse(formula), SYMBOLS)


# --- documents: LaTeX and typst -----------------------------------------------------

LATEX_SYMBOLS = {**SYMBOLS, "x": "x", "y": "y", "k_cat": r"k_{\mathrm{cat}}"}
TYPST_SYMBOLS = {**SYMBOLS, "x": "x", "y": "y", "k_cat": 'k_("cat")'}


def tex(formula: str) -> str:
    """LaTeX of an L3 infix formula."""
    return LatexPrinter().print(parse(formula), LATEX_SYMBOLS)


def typ(formula: str) -> str:
    """Typst of an L3 infix formula."""
    return TypstPrinter().print(parse(formula), TYPST_SYMBOLS)


# the rate laws shared by the dialects, as LaTeX and as typst
DOCUMENT_FORMULAS: dict[str, tuple[str, str]] = {
    "k*A": (r"k \cdot A", "k dot A"),
    "ln(A) + log10(A) + log(2, A) + exp(-k)": (
        r"\ln\mathopen{}\left(A\right) + \log_{10}\mathopen{}\left(A\right) + \log_{2}\mathopen{}\left(A\right)"
        r" + \exp\mathopen{}\left(-k\right)",
        "ln(A) + log_(10) (A) + log_(2) (A) + exp(-k)",
    ),
    "piecewise(k, A > 1 && !(A > 10) || xor(true, false), 2*k)": (
        r"\begin{cases} k & \text{if } \mathopen{}\left(A > 1 \land \lnot \mathopen{}\left(A > 10\right)"
        r"\right) \lor \mathopen{}\left(\mathrm{true} \oplus \mathrm{false}\right) \\"
        r" 2 \cdot k & \text{otherwise} \end{cases}",
        'cases(k & quad "if" (A > 1 and not (A > 10)) or ("true" xor "false"),'
        ' 2 dot k & quad "otherwise")',
    ),
    "piecewise(k, (A < 1) || (A >= 10), 3*k, A == 3, 0.1)": (
        r"\begin{cases} k & \text{if } A < 1 \lor A \geq 10 \\"
        r" 3 \cdot k & \text{if } A = 3 \\ 0.1 & \text{otherwise} \end{cases}",
        'cases(k & quad "if" A < 1 or A >= 10, 3 dot k & quad "if" A = 3, 0.1 & quad "otherwise")',
    ),
    "piecewise(k, A > 1)": (
        r"\begin{cases} k & \text{if } A > 1 \\"
        r" \mathrm{NaN} & \text{otherwise} \end{cases}",
        'cases(k & quad "if" A > 1, "NaN" & quad "otherwise")',
    ),
    "rem(A, 2) + rem(-7, A) + quotient(7, A) + root(3, A) + sqrt(A) + A^2 + pow(A, k)": (
        r"\operatorname{rem}\mathopen{}\left(A, 2\right) + \operatorname{rem}\mathopen{}\left(-7, A\right)"
        r" + \operatorname{quotient}\mathopen{}\left(7, A\right) + \sqrt[3]{A} + \sqrt{A}"
        r" + A^{2} + A^{k}",
        'op("rem")(A, 2) + op("rem")(-7, A) + op("quotient")(7, A) + root(3, A)'
        " + sqrt(A) + A^(2) + A^(k)",
    ),
    "max(A, k, 1) + min(A, k) + abs(-A) + floor(A/2) + ceil(A/2)": (
        r"\max\mathopen{}\left(A, k, 1\right) + \min\mathopen{}\left(A, k\right) + \mathopen{}\left| -A \right|"
        r" + \mathopen{}\left\lfloor \frac{A}{2} \right\rfloor"
        r" + \mathopen{}\left\lceil \frac{A}{2} \right\rceil",
        "max(A, k, 1) + min(A, k) + abs(-A) + floor((A)/(2)) + ceil((A)/(2))",
    ),
    "factorial(3) + pi + exponentiale": (
        r"3! + \pi + \mathrm{e}",
        "3! + pi + upright(e)",
    ),
    "implies(A > 1, k > 1) + (A != 2) + (1 < A <= 5)": (
        r"\mathopen{}\left[A > 1 \Rightarrow k > 1\right] + \mathopen{}\left[A \neq 2\right]"
        r" + \mathopen{}\left[1 < A \land A \leq 5\right]",
        "[A > 1 => k > 1] + [A != 2] + [1 < A and A <= 5]",
    ),
    "piecewise(1, A < INF, 0) + piecewise(1, 5 > -INF, 0)": (
        r"\mathopen{}\left(\begin{cases} 1 & \text{if } A < \infty \\"
        r" 0 & \text{otherwise} \end{cases}\right)"
        r" + \mathopen{}\left(\begin{cases} 1 & \text{if } 5 > -\infty \\"
        r" 0 & \text{otherwise} \end{cases}\right)",
        '(cases(1 & quad "if" A < infinity, 0 & quad "otherwise"))'
        ' + (cases(1 & quad "if" 5 > -infinity, 0 & quad "otherwise"))',
    ),
    "sin(A) + cos(A) + tan(A) + sec(A) + csc(A) + cot(A)": (
        r"\sin\mathopen{}\left(A\right) + \cos\mathopen{}\left(A\right) + \tan\mathopen{}\left(A\right)"
        r" + \sec\mathopen{}\left(A\right) + \csc\mathopen{}\left(A\right) + \cot\mathopen{}\left(A\right)",
        "sin(A) + cos(A) + tan(A) + sec(A) + csc(A) + cot(A)",
    ),
    "sinh(k) + cosh(k) + tanh(k) + sech(k) + csch(k) + coth(k)": (
        r"\sinh\mathopen{}\left(k\right) + \cosh\mathopen{}\left(k\right) + \tanh\mathopen{}\left(k\right)"
        r" + \operatorname{sech}\mathopen{}\left(k\right) + \operatorname{csch}\mathopen{}\left(k\right)"
        r" + \coth\mathopen{}\left(k\right)",
        "sinh(k) + cosh(k) + tanh(k) + sech(k) + csch(k) + coth(k)",
    ),
    "arcsin(k) + arccos(k) + arctan(k) + arcsinh(k) + arctanh(k)": (
        r"\arcsin\mathopen{}\left(k\right) + \arccos\mathopen{}\left(k\right) + \arctan\mathopen{}\left(k\right)"
        r" + \operatorname{arcsinh}\mathopen{}\left(k\right)"
        r" + \operatorname{arctanh}\mathopen{}\left(k\right)",
        'arcsin(k) + arccos(k) + arctan(k) + op("arcsinh")(k) + op("arctanh")(k)',
    ),
    "arcsec(A) + arccsc(A) + arccot(A) + arccosh(A) + arcsech(k) + arccsch(k)": (
        r"\operatorname{arcsec}\mathopen{}\left(A\right) + \operatorname{arccsc}\mathopen{}\left(A\right)"
        r" + \operatorname{arccot}\mathopen{}\left(A\right)"
        r" + \operatorname{arccosh}\mathopen{}\left(A\right)"
        r" + \operatorname{arcsech}\mathopen{}\left(k\right)"
        r" + \operatorname{arccsch}\mathopen{}\left(k\right)",
        'op("arcsec")(A) + op("arccsc")(A) + op("arccot")(A) + op("arccosh")(A)'
        ' + op("arcsech")(k) + op("arccsch")(k)',
    ),
    "arccoth(A)": (
        r"\operatorname{arccoth}\mathopen{}\left(A\right)",
        'op("arccoth")(A)',
    ),
    "piecewise(k*time, true, 0) + 2^-1 + -A^2 + 1/2 + (-2)^2 + 2^3^2": (
        r"\mathopen{}\left(\begin{cases} k \cdot t & \text{if } \mathrm{true} \\"
        r" 0 & \text{otherwise} \end{cases}\right) + 2^{-1} - A^{2}"
        r" + \frac{1}{2} + \mathopen{}\left(-2\right)^{2} + 2^{3^{2}}",
        '(cases(k dot t & quad "if" "true", 0 & quad "otherwise")) + 2^(-1) - A^(2)'
        " + (1)/(2) + (-2)^(2) + 2^(3^(2))",
    ),
}

# the constructs with the parentheses their place requires, as LaTeX and as typst
DOCUMENT_MATH: list[tuple[str, str, str]] = [
    # sums with the signs of their terms, a product with a negative operand
    ("-A^2", "-A^{2}", "-A^(2)"),
    ("A * -k", r"A \cdot \mathopen{}\left(-k\right)", "A dot (-k)"),
    ("A + -k", "A - k", "A - k"),
    ("A - -k", "A + k", "A + k"),
    ("-A * k", r"-A \cdot k", "-A dot k"),
    ("-(A * k)", r"-A \cdot k", "-A dot k"),
    ("-(A + k)", "-A - k", "-A - k"),
    ("--A", "A", "A"),
    ("A - (k - 1)", "A - k + 1", "A - k + 1"),
    ("(A - k) - 1", "A - k - 1", "A - k - 1"),
    ("A * (k + 1)", r"A \cdot \mathopen{}\left(k + 1\right)", "A dot (k + 1)"),
    ("A / k * 2", r"\frac{A}{k} \cdot 2", "(A)/(k) dot 2"),
    # fractions
    ("k*A/(1+A)", r"\frac{k \cdot A}{1 + A}", "(k dot A)/(1 + A)"),
    ("(A/k)/(k/A)", r"\frac{\frac{A}{k}}{\frac{k}{A}}", "((A)/(k))/((k)/(A))"),
    ("-A/k", r"\frac{-A}{k}", "(-A)/(k)"),
    ("-(A/k)", r"-\frac{A}{k}", "-(A)/(k)"),
    ("A * (k/2)", r"A \cdot \frac{k}{2}", "A dot (k)/(2)"),
    # powers
    ("(A/k)^2", r"\mathopen{}\left(\frac{A}{k}\right)^{2}", "((A)/(k))^(2)"),
    ("A^(1/2)", r"A^{\frac{1}{2}}", "A^((1)/(2))"),
    ("(A^2)^3", r"\mathopen{}\left(A^{2}\right)^{3}", "(A^(2))^(3)"),
    ("A^(k + 1)", "A^{k + 1}", "A^(k + 1)"),
    ("(A + 1)^2", r"\mathopen{}\left(A + 1\right)^{2}", "(A + 1)^(2)"),
    ("k_cat^2", r"k_{\mathrm{cat}}^{2}", 'k_("cat")^(2)'),
    (
        "sin(A)^2",
        r"\mathopen{}\left(\sin\mathopen{}\left(A\right)\right)^{2}",
        "(sin(A))^(2)",
    ),
    ("abs(A)^2", r"\mathopen{}\left| A \right|^{2}", "abs(A)^(2)"),
    ("sqrt(A)^2", r"\mathopen{}\left(\sqrt{A}\right)^{2}", "(sqrt(A))^(2)"),
    ("factorial(A)^2", r"\mathopen{}\left(A!\right)^{2}", "(A!)^(2)"),
    # piecewise
    (
        "piecewise(k, A > 1, 0)",
        r"\begin{cases} k & \text{if } A > 1 \\ 0 & \text{otherwise} \end{cases}",
        'cases(k & quad "if" A > 1, 0 & quad "otherwise")',
    ),
    (
        "2 * piecewise(1, A > 1, 2)",
        r"2 \cdot \mathopen{}\left(\begin{cases} 1 & \text{if } A > 1 \\ 2 & \text{otherwise} \end{cases}\right)",
        '2 dot (cases(1 & quad "if" A > 1, 2 & quad "otherwise"))',
    ),
    (
        "piecewise(1, A > 1, 2)^2",
        r"\mathopen{}\left(\begin{cases} 1 & \text{if } A > 1 \\ 2 & \text{otherwise} \end{cases}\right)^{2}",
        '(cases(1 & quad "if" A > 1, 2 & quad "otherwise"))^(2)',
    ),
    (
        "piecewise(1, A > 1, 2) / k",
        r"\frac{\begin{cases} 1 & \text{if } A > 1 \\ 2 & \text{otherwise} \end{cases}}{k}",
        '(cases(1 & quad "if" A > 1, 2 & quad "otherwise"))/(k)',
    ),
    (
        "exp(piecewise(1, A > 1, 2))",
        r"\exp\mathopen{}\left(\begin{cases} 1 & \text{if } A > 1 \\ 2 & \text{otherwise} \end{cases}\right)",
        'exp(cases(1 & quad "if" A > 1, 2 & quad "otherwise"))',
    ),
    (
        "piecewise(piecewise(1, A > 1, 2), k > 1, 3)",
        r"\begin{cases} \begin{cases} 1 & \text{if } A > 1 \\ 2 & \text{otherwise} \end{cases} & \text{if } k > 1 \\ 3 & \text{otherwise} \end{cases}",
        'cases(cases(1 & quad "if" A > 1, 2 & quad "otherwise") & quad "if" k > 1, 3 & quad "otherwise")',
    ),
    # functions
    ("factorial(A + 1)", r"\mathopen{}\left(A + 1\right)!", "(A + 1)!"),
    ("factorial(-A)", r"\mathopen{}\left(-A\right)!", "(-A)!"),
    ("root(k + 1, A)", r"\sqrt[k + 1]{A}", "root(k + 1, A)"),
    ("sqrt(A + k)", r"\sqrt{A + k}", "sqrt(A + k)"),
    ("root(2, A)", r"\sqrt{A}", "sqrt(A)"),
    # an index with a bracket is in braces, which would end the optional argument
    (
        "root(A > 1, k)",
        r"\sqrt[{\mathopen{}\left[A > 1\right]}]{k}",
        "root([A > 1], k)",
    ),
    # a product with a negative first factor is negative
    ("x + (-2)*y", r"x - 2 \cdot y", "x - 2 dot y"),
    ("x - -k*A", r"x + k \cdot A", "x + k dot A"),
    ("-(-2*y)", r"2 \cdot y", "2 dot y"),
    ("x + (-1)*y", "x - y", "x - y"),
    ("x * (-2*y)", r"x \cdot \mathopen{}\left(-2 \cdot y\right)", "x dot (-2 dot y)"),
    ("(-2*y)^2", r"\mathopen{}\left(-2 \cdot y\right)^{2}", "(-2 dot y)^(2)"),
    # every nested sum is written with the signs of its terms
    ("(x + (-2)*y)/k", r"\frac{x - 2 \cdot y}{k}", "(x - 2 dot y)/(k)"),
    ("exp(x - -y)", r"\exp\mathopen{}\left(x + y\right)", "exp(x + y)"),
    ("(x + (-1)*y)^2", r"\mathopen{}\left(x - y\right)^{2}", "(x - y)^(2)"),
    (
        "k * (x - (y - 1))",
        r"k \cdot \mathopen{}\left(x - y + 1\right)",
        "k dot (x - y + 1)",
    ),
    ("(-1)*y", "-y", "-y"),
    ("k * ((-1)*y)", r"k \cdot \mathopen{}\left(-y\right)", "k dot (-y)"),
    ("((-2)*y)*k", r"-2 \cdot y \cdot k", "-2 dot y dot k"),
    ("log(A)", r"\log_{10}\mathopen{}\left(A\right)", "log_(10) (A)"),
    ("log(k + 1, A)", r"\log_{k + 1}\mathopen{}\left(A\right)", "log_(k + 1) (A)"),
    (
        "rem(A, k)^2",
        r"\mathopen{}\left(\operatorname{rem}\mathopen{}\left(A, k\right)\right)^{2}",
        '(op("rem")(A, k))^(2)',
    ),
    (
        "abs(max(A, k))",
        r"\mathopen{}\left| \max\mathopen{}\left(A, k\right) \right|",
        "abs(max(A, k))",
    ),
    ("floor(-A)", r"\mathopen{}\left\lfloor -A \right\rfloor", "floor(-A)"),
    ("f(A + 1, k)", r"f\mathopen{}\left(A + 1, k\right)", "f(A + 1, k)"),
    ("max(A)", "A", "A"),
    (
        "log(2, A)^2",
        r"\mathopen{}\left(\log_{2}\mathopen{}\left(A\right)\right)^{2}",
        "(log_(2) (A))^(2)",
    ),
    (
        "factorial(sin(A))",
        r"\mathopen{}\left(\sin\mathopen{}\left(A\right)\right)!",
        "(sin(A))!",
    ),
    ("-abs(A)", r"-\mathopen{}\left| A \right|", "-abs(A)"),
    ("-sin(A)", r"-\sin\mathopen{}\left(A\right)", "-sin(A)"),
    ("A * sqrt(k)", r"A \cdot \sqrt{k}", "A dot sqrt(k)"),
    # booleans used as numbers, in Iverson brackets
    (
        "!(A > 1)",
        r"\mathopen{}\left[\lnot \mathopen{}\left(A > 1\right)\right]",
        "[not (A > 1)]",
    ),
    (
        "xor(A > 1, k > 1, A < 5)",
        r"\mathopen{}\left[\mathopen{}\left(A > 1\right) \oplus \mathopen{}\left(k > 1\right) \oplus \mathopen{}\left(A < 5\right)\right]",
        "[(A > 1) xor (k > 1) xor (A < 5)]",
    ),
    (
        "true + false",
        r"\mathopen{}\left[\mathrm{true}\right] + \mathopen{}\left[\mathrm{false}\right]",
        '["true"] + ["false"]',
    ),
    (
        "f(A + 1, k > 1)",
        r"f\mathopen{}\left(A + 1, \mathopen{}\left[k > 1\right]\right)",
        "f(A + 1, [k > 1])",
    ),
    ("(A > 1) * 2", r"\mathopen{}\left[A > 1\right] \cdot 2", "[A > 1] dot 2"),
    # numbers and constants
    ("2.0 * A", r"2 \cdot A", "2 dot A"),
    ("0.1", "0.1", "0.1"),
    ("1e-5", "10^{-5}", "10^(-5)"),
    ("1.5e-3", "0.0015", "0.0015"),
    ("2.5e-5 * A", r"2.5 \times 10^{-5} \cdot A", "2.5 times 10^(-5) dot A"),
    (
        "A * 2.5e-5",
        r"A \cdot \mathopen{}\left(2.5 \times 10^{-5}\right)",
        "A dot (2.5 times 10^(-5))",
    ),
    ("(1e-5)^2", r"\mathopen{}\left(10^{-5}\right)^{2}", "(10^(-5))^(2)"),
    (
        "(2.5e20)^2",
        r"\mathopen{}\left(2.5 \times 10^{20}\right)^{2}",
        "(2.5 times 10^(20))^(2)",
    ),
    ("1e16", "10^{16}", "10^(16)"),
    ("10^20", "10^{20}", "10^(20)"),
    ("avogadro * A", r"N_{\mathrm{A}} \cdot A", 'N_"A" dot A'),
    ("INF - NaN", r"\infty - \mathrm{NaN}", 'infinity - "NaN"'),
    ("-INF", r"-\infty", "-infinity"),
    ("time", "t", "t"),
]

# math used as a condition, as LaTeX and as typst
DOCUMENT_CONDITIONS: list[tuple[str, str, str]] = [
    # a call is no operand which needs parentheses
    ("f(A) && A > 1", r"f\mathopen{}\left(A\right) \land A > 1", "f(A) and A > 1"),
    ("!f(A)", r"\lnot f\mathopen{}\left(A\right)", "not f(A)"),
    (
        "xor(f(A), k > 1)",
        r"f\mathopen{}\left(A\right) \oplus \mathopen{}\left(k > 1\right)",
        "f(A) xor (k > 1)",
    ),
    (
        "xor(!(A > 1), k > 1)",
        r"\lnot \mathopen{}\left(A > 1\right) \oplus \mathopen{}\left(k > 1\right)",
        "not (A > 1) xor (k > 1)",
    ),
    (
        "xor(A > 1, k > 1) && A < 5",
        r"\mathopen{}\left(\mathopen{}\left(A > 1\right) \oplus \mathopen{}\left(k > 1\right)\right) \land A < 5",
        "((A > 1) xor (k > 1)) and A < 5",
    ),
    (
        "implies(A > 1, implies(k > 1, A < 5))",
        r"A > 1 \Rightarrow \mathopen{}\left(k > 1 \Rightarrow A < 5\right)",
        "A > 1 => (k > 1 => A < 5)",
    ),
    (
        "piecewise(1, A > 1, 2) > k",
        r"\mathopen{}\left(\begin{cases} 1 & \text{if } A > 1 \\ 2 & \text{otherwise} \end{cases}\right) > k",
        '(cases(1 & quad "if" A > 1, 2 & quad "otherwise")) > k',
    ),
    ("A > 1", "A > 1", "A > 1"),
    ("A <= k", r"A \leq k", "A <= k"),
    ("A >= k", r"A \geq k", "A >= k"),
    ("A != k", r"A \neq k", "A != k"),
    (
        "!(A > 1 && k > 1)",
        r"\lnot \mathopen{}\left(A > 1 \land k > 1\right)",
        "not (A > 1 and k > 1)",
    ),
    ("!!(A > 1)", r"\lnot \lnot \mathopen{}\left(A > 1\right)", "not not (A > 1)"),
    (
        "A > 1 && k > 1 && A < 5",
        r"A > 1 \land k > 1 \land A < 5",
        "A > 1 and k > 1 and A < 5",
    ),
    (
        "(A > 1 || k > 1) && A < 5",
        r"\mathopen{}\left(A > 1 \lor k > 1\right) \land A < 5",
        "(A > 1 or k > 1) and A < 5",
    ),
    (
        "A > 1 || (k > 1 && A < 5)",
        r"A > 1 \lor \mathopen{}\left(k > 1 \land A < 5\right)",
        "A > 1 or (k > 1 and A < 5)",
    ),
    (
        "implies(A > 1 || k > 1, A < 5)",
        r"\mathopen{}\left(A > 1 \lor k > 1\right) \Rightarrow A < 5",
        "(A > 1 or k > 1) => A < 5",
    ),
    ("A + 1 > 2 * k", r"A + 1 > 2 \cdot k", "A + 1 > 2 dot k"),
    ("A > -1", "A > -1", "A > -1"),
    ("true", r"\mathrm{true}", '"true"'),
    (
        "piecewise(A > 1, k > 1, false)",
        r"\begin{cases} A > 1 & \text{if } k > 1 \\ \mathrm{false} & \text{otherwise} \end{cases}",
        'cases(A > 1 & quad "if" k > 1, "false" & quad "otherwise")',
    ),
]


@pytest.mark.parametrize(
    ("formula", "expected"), [(f, latex) for f, (latex, _) in DOCUMENT_FORMULAS.items()]
)
def test_latex_formulas(formula: str, expected: str) -> None:
    """The LaTeX of the rate laws shared by the dialects."""
    assert tex(formula) == expected


@pytest.mark.parametrize(
    ("formula", "expected"), [(f, typst) for f, (_, typst) in DOCUMENT_FORMULAS.items()]
)
def test_typst_formulas(formula: str, expected: str) -> None:
    """The typst of the rate laws shared by the dialects."""
    assert typ(formula) == expected


def test_document_formulas_of_odefac() -> None:
    """The document goldens are the rate laws shared by the tests of the dialects."""
    assert list(DOCUMENT_FORMULAS) == FORMULAS


@pytest.mark.parametrize(
    ("formula", "expected"), [(f, latex) for f, latex, _ in DOCUMENT_MATH]
)
def test_latex_math(formula: str, expected: str) -> None:
    """The LaTeX of the constructs, with the parentheses their place requires."""
    assert tex(formula) == expected


@pytest.mark.parametrize(
    ("formula", "expected"), [(f, typst) for f, _, typst in DOCUMENT_MATH]
)
def test_typst_math(formula: str, expected: str) -> None:
    """The typst of the constructs, with the parentheses their place requires."""
    assert typ(formula) == expected


@pytest.mark.parametrize(
    ("formula", "expected"), [(f, latex) for f, latex, _ in DOCUMENT_CONDITIONS]
)
def test_latex_condition(formula: str, expected: str) -> None:
    """The LaTeX of math used as a condition."""
    assert LatexPrinter().print_condition(parse(formula), LATEX_SYMBOLS) == expected


@pytest.mark.parametrize(
    ("formula", "expected"), [(f, typst) for f, _, typst in DOCUMENT_CONDITIONS]
)
def test_typst_condition(formula: str, expected: str) -> None:
    """The typst of math used as a condition."""
    assert TypstPrinter().print_condition(parse(formula), TYPST_SYMBOLS) == expected


@pytest.mark.parametrize(
    ("content", "latex", "typst"),
    [
        # a negative literal is a unary minus
        (
            "<apply><times/><ci>A</ci><cn>-2.5</cn></apply>",
            r"A \cdot \mathopen{}\left(-2.5\right)",
            "A dot (-2.5)",
        ),
        (
            "<apply><power/><cn type='integer'>-2</cn><ci>A</ci></apply>",
            r"\mathopen{}\left(-2\right)^{A}",
            "(-2)^(A)",
        ),
        (
            "<apply><plus/><ci>A</ci><cn type='e-notation'>-1<sep/>-5</cn></apply>",
            "A - 10^{-5}",
            "A - 10^(-5)",
        ),
        (
            "<apply><power/><cn type='e-notation'>-1<sep/>-5</cn><ci>A</ci></apply>",
            r"\mathopen{}\left(-10^{-5}\right)^{A}",
            "(-10^(-5))^(A)",
        ),
        ("<cn type='rational'>1<sep/>3</cn>", r"\frac{1}{3}", "(1)/(3)"),
        (
            "<apply><log/><ci>A</ci></apply>",
            r"\log_{10}\mathopen{}\left(A\right)",
            "log_(10) (A)",
        ),
        ("<apply><root/><ci>A</ci></apply>", r"\sqrt{A}", "sqrt(A)"),
        ("<apply><and/></apply>", r"\mathopen{}\left[\mathrm{true}\right]", '["true"]'),
        # negative zero is zero
        ("<cn>-0.0</cn>", "0", "0"),
        (
            "<apply><plus/><ci>A</ci><apply><times/><cn type='integer'>-1</cn>"
            "<ci>k</ci></apply></apply>",
            "A - k",
            "A - k",
        ),
        # a relation of conditions (which the infix syntax reads as a chain)
        (
            "<apply><eq/><apply><gt/><ci>A</ci><cn>1</cn></apply>"
            "<apply><gt/><ci>k</ci><cn>1</cn></apply></apply>",
            r"\mathopen{}\left[\mathopen{}\left[A > 1\right] = \mathopen{}\left[k > 1\right]\right]",
            "[[A > 1] = [k > 1]]",
        ),
    ],
)
def test_document_mathml(content: str, latex: str, typst: str) -> None:
    """The LaTeX and the typst of the constructs the infix syntax lacks."""
    assert LatexPrinter().print(mathml(content), LATEX_SYMBOLS) == latex
    assert TypstPrinter().print(mathml(content), TYPST_SYMBOLS) == typst


@pytest.mark.parametrize("printer", [LatexPrinter, TypstPrinter])
@pytest.mark.parametrize("formula", ["rateOf(A)", "delay(A, 1)"])
def test_document_unsupported(printer: type[MathPrinter], formula: str) -> None:
    """A construct without a notation raises and names the printer."""
    with pytest.raises(NotImplementedError, match=f"{printer.name} printer"):
        printer().print(parse(formula), SYMBOLS)


def test_document_unmapped_identifier() -> None:
    """An identifier without a symbol is never typeset."""
    with pytest.raises(NotImplementedError, match=r"'B'.*latex printer"):
        tex("B + 1")
    with pytest.raises(NotImplementedError, match=r"'B'.*typst printer"):
        typ("B + 1")


# --- terms and lines ----------------------------------------------------------------

LINE_SYMBOLS = {name: name for name in "abcdefAkxy"}


def test_terms() -> None:
    """The signed terms of a sum, nested sums and unary minus flattened."""
    terms = PythonPrinter().terms(
        parse("a - (b - c) + -(d + -e) + f * (a + b)"), LINE_SYMBOLS
    )
    assert terms == [
        Term(negative=False, printed=Printed("a", Precedence.ATOM)),
        Term(negative=True, printed=Printed("b", Precedence.ATOM)),
        Term(negative=False, printed=Printed("c", Precedence.ATOM)),
        Term(negative=True, printed=Printed("d", Precedence.ATOM)),
        Term(negative=False, printed=Printed("e", Precedence.ATOM)),
        Term(negative=False, printed=Printed("f * (a + b)", Precedence.PRODUCT)),
    ]


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("a * b", [Term(negative=False, printed=Printed("a * b", Precedence.PRODUCT))]),
        ("-a", [Term(negative=True, printed=Printed("a", Precedence.ATOM))]),
        ("--a", [Term(negative=False, printed=Printed("a", Precedence.ATOM))]),
        (
            "a + b",
            [
                Term(negative=False, printed=Printed("a", Precedence.ATOM)),
                Term(negative=False, printed=Printed("b", Precedence.ATOM)),
            ],
        ),
    ],
)
def test_terms_of(formula: str, expected: list[Term]) -> None:
    """Math which is no sum is a single term, a negation a term with a minus."""
    assert PythonPrinter().terms(parse(formula), LINE_SYMBOLS) == expected


def test_terms_negative_literal() -> None:
    """A negative number is a term with a minus."""
    content = "<apply><plus/><ci>a</ci><cn>-2.5</cn><cn type='integer'>-3</cn></apply>"
    terms = PythonPrinter().terms(mathml(content), LINE_SYMBOLS)
    assert terms == [
        Term(negative=False, printed=Printed("a", Precedence.ATOM)),
        Term(negative=True, printed=Printed("2.5", Precedence.ATOM)),
        Term(negative=True, printed=Printed("3", Precedence.ATOM)),
    ]


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("a + (-2)*b", [(False, "a"), (True, "2 * b")]),
        ("a - -c*b", [(False, "a"), (False, "c * b")]),
        ("-(-2*b)", [(False, "2 * b")]),
        ("a + (-1)*b", [(False, "a"), (True, "b")]),
        ("a + (-1.0)*b*c", [(False, "a"), (True, "b * c")]),
        ("a - (-1)*(-1)*b", [(False, "a"), (True, "b")]),
        ("-1 * (a + b) + c", [(True, "a"), (True, "b"), (False, "c")]),
        ("a + b*(-2)", [(False, "a"), (False, "b * -2")]),
    ],
)
def test_terms_negative_factor(formula: str, expected: list[tuple[bool, str]]) -> None:
    """The sign of a negative first factor is the sign of the term, `-1 * b` is `-b`."""
    terms = PythonPrinter().terms(parse(formula), LINE_SYMBOLS)
    assert [(term.negative, term.printed.code) for term in terms] == expected


def test_terms_negative_factor_mathml() -> None:
    """A negative number as the first factor is a term with a minus."""
    content = (
        "<apply><plus/><ci>a</ci><apply><times/><cn type='integer'>-1</cn><ci>b</ci>"
        "</apply><apply><times/><cn>-2.5</cn><ci>b</ci></apply></apply>"
    )
    terms = PythonPrinter().terms(mathml(content), LINE_SYMBOLS)
    assert [(term.negative, term.printed.code) for term in terms] == [
        (False, "a"),
        (True, "b"),
        (True, "2.5 * b"),
    ]


def test_terms_unsupported() -> None:
    """A term which the printer cannot write raises as `print` does."""
    with pytest.raises(NotImplementedError, match=r"'rateOf\(a\)'.*python printer"):
        PythonPrinter().terms(parse("a + rateOf(a)"), LINE_SYMBOLS)


@pytest.mark.parametrize(
    ("formula", "width", "latex", "typst"),
    [
        ("a+b+c+d+e+f", 4, ["a + b + c + d", "+ e + f"], ["a + b + c + d", "+ e + f"]),
        ("a+b+c+d", 4, ["a + b + c + d"], ["a + b + c + d"]),
        ("a+b+c+d+e", 4, ["a + b + c + d", "+ e"], ["a + b + c + d", "+ e"]),
        ("a - b + c - d", 2, ["a - b", "+ c - d"], ["a - b", "+ c - d"]),
        (
            "a - b - c - d - e",
            2,
            ["a - b", "- c - d", "- e"],
            ["a - b", "- c - d", "- e"],
        ),
        ("-a + b", 4, ["-a + b"], ["-a + b"]),
        ("a + -b", 4, ["a - b"], ["a - b"]),
        ("a - (b - 1)", 4, ["a - b + 1"], ["a - b + 1"]),
        ("-(a + b) - 1", 4, ["-a - b - 1"], ["-a - b - 1"]),
        ("-a^2 - a/b", 4, ["-a^{2} - \\frac{a}{b}"], ["-a^(2) - (a)/(b)"]),
        ("-(a * b) + c", 4, [r"-a \cdot b + c"], ["-a dot b + c"]),
        (
            "a * (b + 1)",
            1,
            [r"a \cdot \mathopen{}\left(b + 1\right)"],
            ["a dot (b + 1)"],
        ),
        ("a", 4, ["a"], ["a"]),
        ("-a", 4, ["-a"], ["-a"]),
        ("x + (-2)*y", 4, [r"x - 2 \cdot y"], ["x - 2 dot y"]),
        ("x - -k*A", 4, [r"x + k \cdot A"], ["x + k dot A"]),
        ("-(-2*y)", 4, [r"2 \cdot y"], ["2 dot y"]),
        ("x + (-1)*y", 4, ["x - y"], ["x - y"]),
        ("(-2)*y + x", 4, [r"-2 \cdot y + x"], ["-2 dot y + x"]),
        (
            "piecewise(a, b > 1, 0)",
            4,
            [r"\begin{cases} a & \text{if } b > 1 \\ 0 & \text{otherwise} \end{cases}"],
            ['cases(a & quad "if" b > 1, 0 & quad "otherwise")'],
        ),
        (
            "piecewise(a, b > 1, 0) - c",
            4,
            [
                r"\mathopen{}\left(\begin{cases} a & \text{if } b > 1 \\ 0 & \text{otherwise} \end{cases}\right) - c"
            ],
            ['(cases(a & quad "if" b > 1, 0 & quad "otherwise")) - c'],
        ),
        (
            "c - piecewise(a, b > 1, 0)",
            4,
            [
                r"c - \mathopen{}\left(\begin{cases} a & \text{if } b > 1 \\ 0 & \text{otherwise} \end{cases}\right)"
            ],
            ['c - (cases(a & quad "if" b > 1, 0 & quad "otherwise"))'],
        ),
        (
            "-piecewise(a, b > 1, 0)",
            4,
            [
                r"-\mathopen{}\left(\begin{cases} a & \text{if } b > 1 \\ 0 & \text{otherwise} \end{cases}\right)"
            ],
            ['-(cases(a & quad "if" b > 1, 0 & quad "otherwise"))'],
        ),
    ],
)
def test_print_lines(
    formula: str, width: int, latex: list[str], typst: list[str]
) -> None:
    """A sum of more terms than the width is split into lines of signed terms."""
    assert LatexPrinter().print_lines(parse(formula), LINE_SYMBOLS, width) == latex
    assert TypstPrinter().print_lines(parse(formula), LINE_SYMBOLS, width) == typst


@pytest.mark.parametrize(
    "formula", [*DOCUMENT_FORMULAS, *(formula for formula, _, _ in DOCUMENT_MATH)]
)
@pytest.mark.parametrize(
    ("printer", "symbols"),
    [(LatexPrinter, LATEX_SYMBOLS), (TypstPrinter, TYPST_SYMBOLS)],
)
def test_print_lines_one_line_is_print(
    formula: str, printer: type[DocumentPrinter], symbols: dict[str, str]
) -> None:
    """A sum which fits on one line is printed as `print` prints it."""
    math = parse(formula)
    assert printer().print_lines(math, symbols, width=100) == [
        printer().print(math, symbols)
    ]


def test_print_lines_default_width() -> None:
    """The default width is four terms."""
    lines = LatexPrinter().print_lines(parse("a+b+c+d+e+f+a+b+c"), LINE_SYMBOLS)
    assert lines == ["a + b + c + d", "+ e + f + a + b", "+ c"]


@pytest.mark.parametrize("printer", [LatexPrinter, TypstPrinter])
def test_print_lines_width(printer: type[DocumentPrinter]) -> None:
    """A line holds at least one term."""
    with pytest.raises(ValueError, match="width"):
        printer().print_lines(parse("a + b"), LINE_SYMBOLS, 0)


# --- compilation of the documents ---------------------------------------------------


def _typst_goldens() -> list[str]:
    """Every typst golden of the tests, the lines of a sum as one list each."""
    goldens = [typst for _, typst in DOCUMENT_FORMULAS.values()]
    goldens += [typst for _, _, typst in DOCUMENT_MATH]
    goldens += [typst for _, _, typst in DOCUMENT_CONDITIONS]
    return goldens


def _latex_goldens() -> list[str]:
    """Every LaTeX golden of the tests."""
    goldens = [latex for latex, _ in DOCUMENT_FORMULAS.values()]
    goldens += [latex for _, latex, _ in DOCUMENT_MATH]
    goldens += [latex for _, latex, _ in DOCUMENT_CONDITIONS]
    return goldens


LINES_FORMULA = "a+b-c+d+e-f*a+b/c"


def typst_document() -> str:
    """Typst document with every typst golden as an equation of its own."""
    lines = TypstPrinter().print_lines(parse(LINES_FORMULA), LINE_SYMBOLS)
    equations = [f"$ {golden} $" for golden in _typst_goldens()]
    # the empty string before a line spaces its sign as a binary operator
    equations.append("$ y &= " + ' \\\n  & quad "" '.join(lines) + " $")
    return (
        "#set page(width: 16cm, height: auto, margin: 1cm)\n\n"
        + "\n\n".join(equations)
        + "\n"
    )


def latex_document() -> str:
    """LaTeX document with every LaTeX golden as an equation of its own."""
    lines = LatexPrinter().print_lines(parse(LINES_FORMULA), LINE_SYMBOLS)
    equations = [f"\\[ {golden} \\]" for golden in _latex_goldens()]
    equations.append(
        "\\begin{align*}\ny &= " + " \\\\\n  &\\quad ".join(lines) + "\n\\end{align*}"
    )
    return (
        "\\documentclass{article}\n\\usepackage{amsmath}\n\\begin{document}\n\n"
        + "\n\n".join(equations)
        + "\n\n\\end{document}\n"
    )


def test_typst_compiles(tmp_path: Path) -> None:
    """Every typst golden compiles, without a warning."""
    assert compile_typst(typst_document(), tmp_path).startswith(b"%PDF")


@pytest.mark.skipif(tectonic_command() is None, reason="tectonic is not on the path")
def test_latex_compiles(tmp_path: Path) -> None:
    """Every LaTeX golden compiles with tectonic."""
    assert compile_latex(latex_document(), tmp_path).exists()


# --- evaluation ---------------------------------------------------------------------

# formulas whose value depends on the semantics of the dialect beyond `FORMULAS`,
# their reference is roadrunner
EDGE_FORMULAS: list[str] = [
    "quotient(1, 0.1)",
    "quotient(-7, 2)",
    "rem(1, 0.1)",
    "rem(-7.5, 2)",
    "rem(7.5, -2)",
    "2^-3",
    "10^20",
    "(A - 3)^-1",
    "max(A)",
    "true + false",
    "(A > 1) * 2 + xor(A > 1, k > 1, A < 5)",
    # outside the real domain: NaN, never an error or a complex number; a power has
    # a variable operand, python numbers alone (literals) are no numpy scalars
    "(-A * 1e-15)^1.8",
    "(-A)^k",
    "root(3, -A)",
    "sqrt(-1e-15)",
    "sqrt(-A)",
    "ln(-A)",
    "log10(-A)",
    "log(2, -A)",
    "log(-2, A)",
    "arccosh(k)",
    "arcsin(A)",
    "arccos(A)",
    "arctanh(A)",
    "arcsec(k)",
    "arccsc(k)",
    "arccoth(k)",
    "arcsech(A)",
    "sin(INF)",
    "cos(INF)",
    "tan(INF)",
    "sec(INF)",
    "csc(INF)",
    "cot(INF)",
    "rem(INF, 2)",
    "rem(A, 0)",
    # NaN, a relation with NaN in which roadrunner agrees with IEEE 754
    "NaN + 1",
    "piecewise(NaN, A > 1, 0)",
    "NaN != 2",
    "(NaN < 1) || (k < 1)",
    "piecewise(1, sqrt(-A) != 2, 0)",
]

# relations with NaN: roadrunner compares unordered, so that every relation with NaN
# holds (`NaN > 1` and `NaN == 2` are true); the dialects follow IEEE 754 as python,
# julia and C do, in which only `!=` holds; the value of IEEE 754 of each formula
NAN_RELATIONS: dict[str, float] = {
    "NaN > 1": 0.0,
    "NaN == 2": 0.0,
    "sqrt(-A) <= 1": 0.0,
    "piecewise(1, NaN > 1, 2)": 2.0,
    "piecewise(1, !(NaN > 1), 2)": 1.0,
    "xor(NaN > 1, k > 1)": 0.0,
}

EVALUATED: list[str] = [*FORMULAS, *EDGE_FORMULAS, *NAN_RELATIONS]
VALUES: dict[str, float] = {"A": 3.0, "k": 0.5, "t": 2.0}
DIALECTS: list[str] = ["python", "julia", "r"]


def _python_value(formula: str) -> float:
    """Value of a formula, by `eval` of its python.

    The variables are numpy scalars, as the states and the parameters of the
    generated code, whose arithmetic is NaN outside the real domain (with a
    `RuntimeWarning`, which is silenced) where python floats raise or turn complex.
    """
    code = PythonPrinter().print(parse(formula), SYMBOLS)
    variables = {name: np.float64(value) for name, value in VALUES.items()}
    with np.errstate(all="ignore"):
        return float(eval(code, {"np": np, "math": math, **variables}))  # noqa: S307


def _julia_script(codes: list[str]) -> str:
    """Julia script which prints the value of each expression, one per line.

    Each expression is parsed and evaluated on its own, so that an error of one
    is printed in its line instead of ending the script.
    """
    lines = [f"using {', '.join(JULIA_PACKAGES)}"]
    lines += [f"{name} = {value!r}" for name, value in VALUES.items()]
    for code in codes:
        assert '"' not in code
        lines += [
            "try",
            f'    println(Float64(eval(Meta.parse(raw"{code}"))))',
            "catch error",
            '    println("error: ", replace(sprint(showerror, error), "\\n" => " "))',
            "end",
        ]
    return "\n".join(lines) + "\n"


def _r_script(codes: list[str]) -> str:
    """R script which prints the value of each expression, one per line.

    Each expression is parsed and evaluated on its own, so that an error of one
    is printed in its line instead of ending the script.
    """
    lines = [f"{name} <- {value!r}" for name, value in VALUES.items()]
    for code in codes:
        assert '"' not in code
        lines.append(
            "tryCatch("
            f'cat(sprintf("%.17g", as.numeric(eval(parse(text = r"({code})")))), '
            '"\\n", sep = ""), '
            'error = function(e) cat("error:", gsub("\\n", " ", conditionMessage(e)), '
            '"\\n"))'
        )
    return "\n".join(lines) + "\n"


TOOLCHAINS: dict[
    str, tuple[Callable[[], list[str] | None], type[MathPrinter], Callable, Callable]
] = {
    "julia": (julia_command, JuliaPrinter, _julia_script, run_julia),
    "r": (rscript_command, RPrinter, _r_script, run_r),
}


@pytest.fixture(scope="module")
def evaluate(
    tmp_path_factory: pytest.TempPathFactory,
) -> Callable[[str, str], float]:
    """Value of a formula of `EVALUATED` in a dialect.

    The julia and the R of all formulas are evaluated in one process per dialect.
    """
    outputs: dict[str, dict[str, str]] = {}

    def value(dialect: str, formula: str) -> float:
        if dialect == "python":
            return _python_value(formula)
        command, printer, script, run = TOOLCHAINS[dialect]
        if command() is None:
            pytest.skip(f"The toolchain of {dialect} is not runnable.")
        if dialect not in outputs:
            codes = [printer().print(parse(f), SYMBOLS) for f in EVALUATED]
            stdout = run(script(codes), tmp_path_factory.mktemp(dialect))
            lines = stdout.splitlines()
            assert len(lines) == len(EVALUATED), stdout
            outputs[dialect] = dict(zip(EVALUATED, lines, strict=True))
        line = outputs[dialect][formula]
        assert not line.startswith("error"), line
        assert line != "NA", f"{formula} is NA in {dialect}"
        return float(line)

    return value


@pytest.fixture(scope="module")
def roadrunner_value() -> Callable[[str], float]:
    """Value of a formula as the rate of a reaction in roadrunner."""
    roadrunner = pytest.importorskip("roadrunner")
    values: dict[str, float] = {}

    def value(formula: str) -> float:
        assert "time" not in formula, "roadrunner evaluates the rates at time 0"
        if formula not in values:
            model = roadrunner.RoadRunner(sbml_with_rate(formula))
            values[formula] = float(model.getReactionRates()[0])
        return values[formula]

    return value


def _assert_value(actual: float, expected: float) -> None:
    """Assert a value at the point tolerance, NaN equal to NaN."""
    if math.isnan(expected):
        assert math.isnan(actual), actual
    else:
        assert actual == pytest.approx(expected, rel=1e-8, abs=1e-12)


@pytest.mark.parametrize("formula", FORMULAS)
@pytest.mark.parametrize("dialect", TOOLCHAINS)
def test_evaluation(
    dialect: str, formula: str, evaluate: Callable[[str, str], float]
) -> None:
    """The julia and the R of a formula evaluate to the value of its python."""
    expected = evaluate("python", formula)
    assert evaluate(dialect, formula) == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("formula", EDGE_FORMULAS)
@pytest.mark.parametrize("dialect", DIALECTS)
def test_evaluation_edge(
    dialect: str,
    formula: str,
    evaluate: Callable[[str, str], float],
    roadrunner_value: Callable[[str], float],
) -> None:
    """A formula at the edge of the semantics evaluates as in roadrunner."""
    _assert_value(evaluate(dialect, formula), roadrunner_value(formula))


@pytest.mark.parametrize("formula", NAN_RELATIONS)
@pytest.mark.parametrize("dialect", DIALECTS)
def test_evaluation_nan_relation(
    dialect: str, formula: str, evaluate: Callable[[str, str], float]
) -> None:
    """A relation with NaN is false in every dialect, `!=` is true (IEEE 754)."""
    _assert_value(evaluate(dialect, formula), NAN_RELATIONS[formula])


@pytest.mark.parametrize("formula", NAN_RELATIONS)
def test_roadrunner_nan_relation(
    formula: str, roadrunner_value: Callable[[str], float]
) -> None:
    """Roadrunner differs from IEEE 754 for a relation with NaN.

    If this fails, roadrunner follows IEEE 754 and the formula belongs to
    `EDGE_FORMULAS`.
    """
    assert roadrunner_value(formula) != NAN_RELATIONS[formula]
