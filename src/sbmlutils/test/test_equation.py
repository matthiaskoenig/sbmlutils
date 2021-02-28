"""
Test equations.
"""
from sbmlutils.equation import IRREV_SEP, REV_SEP, Equation


def test_equation_examples() -> None:
    equations = [
        "1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]",
        "c__gal1p => c__gal + c__phos",
        "e__h2oM <-> c__h2oM",
        "3 atp + 2.0 phos + ki <-> 16.98 tet",
        "c__gal1p => c__gal + c__phos [c__udp, c__utp]",
        "A_ext => A []",
        "=> cit",
        "acoa =>",
    ]
    for eq_str in equations:
        eq = Equation(eq_str)
        assert eq


def test_equation_1() -> None:
    """ Test Equation. """
    eq_string = "c__gal1p => c__gal + c__phos"
    eq = Equation(eq_string)
    assert eq.to_string() == eq_string


def test_equation_2() -> None:
    """ Test Equation. """
    eq_string = "e__h2oM <-> c__h2oM"
    eq = Equation(eq_string)
    assert eq.reversible

    test_res = eq_string.replace("<->", REV_SEP)
    assert eq.to_string() == test_res


def test_equation_double_stoichiometry() -> None:
    """ Test Equation. """
    eq_string = "3.0 atp + 2.0 phos + ki <-> 16.98 tet"
    eq = Equation(eq_string)
    assert eq.reversible

    test_res = eq_string.replace("<->", REV_SEP)
    assert eq.to_string() == test_res


def test_equation_modifier() -> None:
    """ Test Equation. """
    eq_string = "c__gal1p => c__gal + c__phos [c__udp, c__utp]"
    eq = Equation(eq_string)
    assert eq.to_string(modifiers=True) == eq_string


def test_equation_empty_modifier() -> None:
    """ Test Equation. """
    eq_string = "A_ext => A []"
    eq = Equation(eq_string)
    assert len(eq.modifiers) == 0


def test_equation_no_reactants() -> None:
    """ Test Equation. """
    eq_string = " => A"
    eq = Equation(eq_string)
    test_res = eq_string.replace("=>", IRREV_SEP)
    assert eq.to_string() == test_res


def test_equation_no_products() -> None:
    """ Test Equation. """
    eq_string = "B => "
    eq = Equation(eq_string)
    test_res = eq_string.replace("=>", IRREV_SEP)
    assert eq.to_string() == test_res
