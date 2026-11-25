"""Test MathML functionality."""

from pathlib import Path

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
    """Test conversion formula to ASTNode."""
    astnode = mathml.formula_to_astnode(formula)
    assert astnode
    assert isinstance(astnode, libsbml.ASTNode)


@pytest.mark.parametrize("cmathml", cmathmls)
def test_cmathml_to_astnode(cmathml: str) -> None:
    """Test conversion content MathML to ASTNode."""
    astnode = mathml.cmathml_to_astnode(cmathml)
    assert astnode
    assert isinstance(astnode, libsbml.ASTNode)
    libsbml.readMathMLFromString(cmathml)


@pytest.mark.parametrize("formula", formulas)
def test_formula_to_latex(formula: str) -> None:
    """Test conversion formula to Latex."""
    latex = mathml.formula_to_latex(formula)
    assert latex
    assert isinstance(latex, str)


@pytest.mark.parametrize("formula", formulas)
def test_astnode_to_latex(formula: str) -> None:
    """Test conversion ASTNode to Latex."""
    astnode = mathml.formula_to_astnode(formula)
    latex = mathml.astnode_to_latex(astnode)
    assert latex
    assert isinstance(latex, str)


def test_mathml_entities_are_not_resolved(tmp_path: Path) -> None:
    """A document type declaration cannot read a local file into the latex.

    `cmathml_to_latex` is public and may get MathML from a file, so an external
    entity must neither be resolved (XXE) nor fetched.
    """
    secret = tmp_path / "secret.txt"
    secret.write_text("SECRET_TOKEN", encoding="utf-8")
    cmathml = (
        f'<!DOCTYPE math [<!ENTITY xxe SYSTEM "{secret.as_uri()}">]>'
        '<math xmlns="http://www.w3.org/1998/Math/MathML"><ci>&xxe;</ci></math>'
    )
    assert "SECRET_TOKEN" not in mathml.cmathml_to_latex(cmathml)
