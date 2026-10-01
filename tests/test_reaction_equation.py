"""Test equations."""

import pytest

from sbmlutils.reaction_equation import (
    IRREVERSIBILITY_SEPARATOR,
    REVERSIBILITY_SEPARATOR,
    EquationPart,
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


def test_modifiers_accept_strings() -> None:
    """Test that the `modifiers=["M1"]` authoring style still works."""
    equation = ReactionEquation.from_str("S1 -> S2 [M1]")
    assert len(equation.modifiers) == 1
    assert equation.modifiers[0].species == "M1"


def test_modifiers_keep_sbase_fields() -> None:
    """Test that a modifier carries its own metaId and sboTerm."""
    equation = ReactionEquation(
        reactants=[EquationPart(species="S1")],
        products=[EquationPart(species="S2")],
        modifiers=[EquationPart(species="M1", metaId="mod1", sboTerm="SBO:0000019")],
    )
    assert equation.modifiers[0].metaId == "mod1"


def test_scientific_stoichiometry() -> None:
    """A stoichiometry in scientific notation is one number, not two sides."""
    equation = ReactionEquation.from_str("1e-3 A + 2.5E+2 B => C")
    assert [(r.stoichiometry, r.species) for r in equation.reactants] == [
        (1e-3, "A"),
        (250.0, "B"),
    ]
    assert [p.species for p in equation.products] == ["C"]


def test_plus_without_spaces() -> None:
    """Species joined by a '+' without whitespace are still separate species."""
    equation = ReactionEquation.from_str("A+2 B => C")
    assert [(r.stoichiometry, r.species) for r in equation.reactants] == [
        (1.0, "A"),
        (2.0, "B"),
    ]


@pytest.mark.parametrize(
    "equation",
    [
        "A => B => C",
        "A <=> B => C",
        "A => B <=> C",
        "A <=> B <=> C",
        "A -> B -> C",
    ],
)
def test_more_than_two_sides(equation: str) -> None:
    """An equation with more than one separator is rejected, never truncated."""
    with pytest.raises(ValueError, match="left and right side"):
        ReactionEquation.from_str(equation)


def test_modifiers_in_one_list() -> None:
    """The modifiers of a single list at the end are all read."""
    equation = ReactionEquation.from_str("A => B [M1, M2]")
    assert [m.species for m in equation.modifiers] == ["M1", "M2"]
    assert [p.species for p in equation.products] == ["B"]


@pytest.mark.parametrize(
    "equation",
    [
        "A => B [M1] [M2]",
        "A => B [M1] C",
        "A [M1] => B",
        "A => B [M1",
        "A => B M1]",
    ],
)
def test_invalid_modifier_list(equation: str) -> None:
    """Anything but a single modifier list at the end is rejected."""
    with pytest.raises(ValueError, match="Modifier list"):
        ReactionEquation.from_str(equation)


@pytest.mark.parametrize("equation", ["A + => B", "A => + B", "A + + B => C"])
def test_empty_part(equation: str) -> None:
    """A '+' without a species on both sides is rejected."""
    with pytest.raises(ValueError, match="must separate two species"):
        ReactionEquation.from_str(equation)


@pytest.mark.parametrize("equation", ["A - B => C", "-1 A => B", "A => 2 B - C"])
def test_minus_rejected(equation: str) -> None:
    """A '-' is no separator of parts and no sign of a stoichiometry."""
    with pytest.raises(ValueError, match="'-' and negative"):
        ReactionEquation.from_str(equation)
