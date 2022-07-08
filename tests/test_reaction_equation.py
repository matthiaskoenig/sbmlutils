"""Test equations."""
import pytest

from sbmlutils.reaction_equation import (
    IRREVERSIBILITY_SEPARATOR,
    REVERSIBILITY_SEPARATOR,
    ReactionEquation,
)


equations = [
    # constant stoichiometry
    "1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]",
    "c__gal1p => c__gal + c__phos",
    "e__h2oM <-> c__h2oM",
    "3 atp + 2.0 phos + ki <-> 16.98 tet",
    "c__gal1p => c__gal + c__phos [c__udp, c__utp]",
    "A_ext => A []",
    "=> cit",
    "acoa =>",
    # variable stoichiometry
    "fS1 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]",
    "f1 c__gal1p => f1 c__gal + f1 c__phos",
    "f1 * e__h2oM <-> f1 * c__h2oM",
    "3 atp + 2.0 phos + ki <-> stet tet",
    "f * c__gal1p => f * c__gal + f * c__phos [c__udp, c__utp]",
    "A_ext => f * A []",
    "=> f * cit",
    "f * acoa =>",
]


@pytest.mark.parametrize("equation", equations)
def test_equation_examples(equation: str) -> None:
    """Test equation examples."""
    eq = ReactionEquation.from_str(equation)
    assert eq
    assert isinstance(eq, ReactionEquation)


def test_equation_1() -> None:
    """Test Equation."""
    eq_string = "c__gal1p => c__gal + c__phos"
    eq = ReactionEquation.from_str(eq_string)
    assert eq.to_string() == eq_string


def test_equation_2() -> None:
    """Test Equation."""
    eq_string = "e__h2oM <-> c__h2oM"
    eq = ReactionEquation.from_str(eq_string)
    assert eq.reversible

    test_res = eq_string.replace("<->", REVERSIBILITY_SEPARATOR)
    assert eq.to_string() == test_res


def test_equation_double_stoichiometry() -> None:
    """Test Equation."""
    eq_string = "3.0 atp + 2.0 phos + ki <-> 16.98 tet"
    eq = ReactionEquation.from_str(eq_string)
    assert eq.reversible

    test_res = eq_string.replace("<->", REVERSIBILITY_SEPARATOR)
    assert eq.to_string() == test_res


def test_equation_modifier() -> None:
    """Test Equation."""
    eq_string = "c__gal1p => c__gal + c__phos [c__udp, c__utp]"
    eq = ReactionEquation.from_str(eq_string)
    assert eq.to_string(modifiers=True) == eq_string


def test_equation_empty_modifier() -> None:
    """Test Equation."""
    eq_string = "A_ext => A []"
    eq = ReactionEquation.from_str(eq_string)
    assert len(eq.modifiers) == 0


def test_equation_no_reactants() -> None:
    """Test Equation."""
    eq_string = " => A"
    eq = ReactionEquation.from_str(eq_string)
    test_res = eq_string.replace("=>", IRREVERSIBILITY_SEPARATOR)
    assert eq.to_string() == test_res


def test_equation_no_products() -> None:
    """Test Equation."""
    eq_string = "B => "
    eq = ReactionEquation.from_str(eq_string)
    test_res = eq_string.replace("=>", IRREVERSIBILITY_SEPARATOR)
    assert eq.to_string() == test_res
