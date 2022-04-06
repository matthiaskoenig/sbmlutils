import libsbml
import pytest

from sbmlutils.report import mathml


formulas = [
    "1 dimensionless",
    "power(3, 5) / x * glc",
    "GK_Vmax * GK_gc_free * (atp/(GK_k_atp + atp)) * f_gly * "
    "(power(glc,GK_n)/(power(glc,GK_n) + power(GK_k_glc, GK_n)))",
    "piecewise(3, x>3, 5)",
    "piecewise(x, x > y, y)",
    "lambda(x, y, piecewise(x, x > y, y))",
    "lambda(x, y, x+y)",
    "(1 - gamma) * GSn + gamma * GSp",
    "piecewise(0, (delay(dClk, tau1) - delay(Per, tau1)) < 0, delay(dClk, tau1) - delay(Per, tau1))",
    "piecewise(VmaxM, exercise_level == 1, piecewise(VmaxH, exercise_level == 2, VmaxVH))",
    "Gamma(v, u, J, K)",
    "lambda(r, C, k, r * C * (1 - C / k))",
]

cmathmls = [
    """
    <math xmlns="http://www.w3.org/1998/Math/MathML">
    <apply>
    <divide/>
    <apply>
        <times/>
        <cn>243</cn>
        <ci>glc</ci>
    </apply>
    <ci>x</ci>
    </apply>
    </math>
    """,
    """
    <math xmlns="http://www.w3.org/1998/Math/MathML">
      <apply>
        <times></times>
        <ci> f_gly </ci>
        <ci> GK_Vmax </ci>
        <ci> GK_gc_free </ci>
        <apply>
          <divide></divide>
          <ci> atp </ci>
          <apply>
            <plus></plus>
            <ci> GK_k_atp </ci>
            <ci> atp </ci>
          </apply>
        </apply>
        <apply>
          <divide></divide>
          <apply>
            <power></power>
            <ci> glc </ci>
            <ci> GK_n </ci>
          </apply>
          <apply>
            <plus></plus>
            <apply>
              <power></power>
              <ci> glc </ci>
              <ci> GK_n </ci>
            </apply>
            <apply>
              <power></power>
              <ci> GK_k_glc </ci>
              <ci> GK_n </ci>
            </apply>
          </apply>
        </apply>
      </apply>
    </math>
    """,
]


@pytest.mark.parametrize("formula", formulas)
def test_formula_to_astnode(formula: str) -> None:
    astnode = mathml.formula_to_astnode(formula)
    assert astnode
    assert isinstance(astnode, libsbml.ASTNode)


@pytest.mark.parametrize("cmathml", cmathmls)
def test_cmathml_to_astnode(cmathml: str) -> None:
    astnode = mathml.cmathml_to_astnode(cmathml)
    assert astnode
    assert isinstance(astnode, libsbml.ASTNode)
    libsbml.readMathMLFromString(cmathml)


@pytest.mark.parametrize("formula", formulas)
def test_formula_to_latex(formula: str) -> None:
    latex = mathml.formula_to_latex(formula)
    assert latex
    assert isinstance(latex, str)


@pytest.mark.parametrize("formula", formulas)
def test_astnode_to_latex(formula: str) -> None:
    astnode = mathml.formula_to_astnode(formula)
    latex = mathml.astnode_to_latex(astnode)
    assert latex
    assert isinstance(latex, str)
