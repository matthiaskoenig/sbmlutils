"""Module for parsing reaction equation strings.

Various string formats are allowed which are subsequently brought into
an internal standard format.

Equations are of the form
    '1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]'

The equation consists of
- substrates concatenated via '+' on the left side
  (with optional stoichiometric coefficients)
- separation characters separating the left and right equation sides:
  '<=>' or '<->' for reversible reactions,
  '=>' or '->' for irreversible reactions (irreversible reactions
  are written from left to right)
- products concatenated via '+' on the right side
  (with optional stoichiometric coefficients)
- optional list of modifiers within brackets [] separated by ','

Examples of valid equations are:
    '1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]',
    'c__gal1p => c__gal + c__phos',
    'e__h2oM <-> c__h2oM',
    '3 atp + 2.0 phos + ki <-> 16.98 tet',
    'c__gal1p => c__gal + c__phos [c__udp, c__utp]',
    'A_ext => A []',
    '=> cit',
    'acoa =>',

In addition, variable stoichiometries can be used, by providing sids as stoichiometries.
Examples of valid equations with variable stoichiometries are:
    'fS1 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]',
    'f1 c__gal1p => f1 c__gal + f1 c__phos',
    'f1 * e__h2oM <-> f1 * c__h2oM',
    '3 atp + 2.0 phos + ki <-> stet tet',
    'f * c__gal1p => f * c__gal + f * c__phos [c__udp, c__utp]',
    'A_ext => f * A []',
    '=> f * cit',
    'f * acoa =>',

"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Final, Iterable, List, Optional


@dataclass
class EquationPart:
    """EquationPart.

    # FIXME: this must be a SpeciesReference, but circular imports!

    An equation consists of parts which define species with their respective
    stoichiometries. The stoichiometries could be constant or vary over time.

    The sid may be target of an InitialAssignment, EventAssignment or Rule.

    Two main cases exists:
    1. `stoichiometry=float, constant=True`
      The EquationPart has a constant stoichiometry and does not change in the
      simulation. It could be set via an InitialAssignment if an sid is provided.
    2. `stoichiometry=None, constant=False, sid=str`

    """

    species: str
    stoichiometry: Optional[float] = None
    sid: Optional[str] = None
    constant: bool = True
    metaId: Optional[str] = field(default=None, repr=False)
    sboTerm: Optional[str] = field(default=None, repr=False)
    name: Optional[str] = field(default=None, repr=False)
    annotations: Optional[List] = field(default=None, repr=False)
    notes: Optional[str] = field(default=None, repr=False)
    keyValuePairs: Optional[List[Any]] = field(default=None, repr=False)


REVERSIBILITY_PATTERN: Final = r"<[-=]>"
IRREVERSIBILITY_PATTERN: Final = r"[-=]>"
MODIFIER_PATTERN: Final = r"\[.*\]"
REVERSIBILITY_SEPARATOR: Final = r"<=>"
IRREVERSIBILITY_SEPARATOR: Final = r"=>"


class ReactionEquation:
    """Representation of stoichiometric equations with modifiers."""

    class EquationException(Exception):
        """Exception in Equation."""

        pass

    def __init__(
        self,
        reactants: Optional[List[EquationPart]] = None,
        products: Optional[List[EquationPart]] = None,
        modifiers: Optional[List[str]] = None,
        reversible: bool = True,
    ):
        """Initialize equation."""

        self.reversible: bool = reversible
        self.reactants: List[EquationPart] = reactants if reactants else []
        self.products: List[EquationPart] = products if products else []
        self.modifiers: List[str] = modifiers if modifiers else []

    @staticmethod
    def from_str(equation_str: str) -> ReactionEquation:
        """Parse components of equation string."""
        equation = ReactionEquation()
        equation._parse_equation(equation_str)
        return equation

    def _parse_equation(self, equation_str: str) -> None:
        # handle empty equation (for dummy reations in comp)
        if not equation_str or len(equation_str) == 0:
            return

        # get modifiers and remove from equation string
        mod_list = re.findall(MODIFIER_PATTERN, equation_str)
        if len(mod_list) == 1:
            self._parse_modifiers(mod_list[0])
            tokens = equation_str.split("[")
            equation_str = tokens[0].strip()
        elif len(mod_list) > 1:
            raise self.EquationException(
                f"Invalid equation: {equation_str}. "
                f"Modifier list could not be parsed. "
                f"{ReactionEquation.help()}"
            )

        # now parse the equation without modifiers
        items = re.split(REVERSIBILITY_PATTERN, equation_str)

        if len(items) == 2:
            self.reversible = True
        elif len(items) == 1:
            items = re.split(IRREVERSIBILITY_PATTERN, equation_str)
            self.reversible = False
        else:
            raise self.EquationException(
                f"Invalid equation: {equation_str}. "
                f"Equation could not be split into left "
                f"and right side. {ReactionEquation.help()}"
            )

        # remove whitespaces
        items = [o.strip() for o in items]
        if len(items) < 2:
            raise self.EquationException(
                f"Invalid equation: {equation_str}. "
                f"Equation could not be split into left "
                f"and right side. Use '<=>' or '=>' as separator. {ReactionEquation.help()}"
            )
        left, right = items[0], items[1]
        if len(left) > 0:
            self.reactants = self._parse_half_equation(left)
        if len(right) > 0:
            self.products = self._parse_half_equation(right)

    def _parse_modifiers(self, s: str) -> None:
        s = s.replace("[", "")
        s = s.replace("]", "")
        s = s.strip()
        tokens = re.split("[,;]", s)
        modifiers = [t.strip() for t in tokens]
        self.modifiers = [t for t in modifiers if len(t) > 0]

    def _parse_half_equation(self, string: str) -> List[EquationPart]:
        """Parse half-equation.

        Only '+ supported in equation !, do not use negative stoichiometries.
        """
        items = re.split("[+-]", string)
        items = [item.strip() for item in items]
        return [self._parse_reactant(item) for item in items]

    @staticmethod
    def _parse_reactant(item: str) -> EquationPart:
        """Parse stoichiometry, species, sid information."""
        tokens = item.split()
        if len(tokens) == 1:
            stoichiometry = 1.0
            species = tokens[0]
            constant = True
            sid = None
        else:
            try:
                stoichiometry = float(tokens[0])
                constant = True
                sid = None
            except ValueError:
                stoichiometry = None
                constant = False
                sid = tokens[0]

            if tokens[1] == "*":
                species = " ".join(tokens[2:]).strip()
            else:
                species = " ".join(tokens[1:])

        return EquationPart(
            stoichiometry=stoichiometry,
            species=species,
            constant=constant,
            sid=sid,
        )

    @staticmethod
    def _to_string_side(items: Iterable[EquationPart]) -> str:
        tokens = []
        for item in items:
            stoichiometry = item.stoichiometry
            species = item.species
            sid = item.sid

            if stoichiometry is None:
                if sid is not None:
                    tokens.append(f"{sid} * {species}")
            else:
                if abs(1.0 - stoichiometry) < 1e-10:
                    tokens.append(species)
                else:
                    tokens.append(f"{stoichiometry} {species}")

        return " + ".join(tokens)

    def _to_string_modifiers(self) -> str:
        return f"[{', '.join(self.modifiers)}]"

    def to_string(self, modifiers: bool = False) -> str:
        """Get string representation of equation."""
        left = self._to_string_side(self.reactants)
        right = self._to_string_side(self.products)
        if self.reversible:
            sep = REVERSIBILITY_SEPARATOR
        else:
            sep = IRREVERSIBILITY_SEPARATOR

        if modifiers:
            mod = self._to_string_modifiers()
            return " ".join([left, sep, right, mod])
        else:
            return " ".join([left, sep, right])

    def info(self) -> None:
        """Print overview of parsed equation."""
        lines = [
            f"{'equation':<10s}: {self.to_string(modifiers=True)}",
            f"{'reversible':<10s}: {self.reversible}",
            f"{'reactants':<10s}: {self.reactants}",
            f"{'products':<10s}: {self.products}",
            f"{'modifiers':<10s}: {self.modifiers}",
            "\n",
        ]
        print("\n".join(lines))

    @staticmethod
    def help() -> str:
        """Get help information string."""
        return """
        For information on the supported equation format use
            from sbmlutils import equation
            help(equation)
        """


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    examples = [
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

    for equation_str in examples:
        print("-" * 40)
        print(equation_str)
        print("-" * 40)
        eq = ReactionEquation.from_str(equation_str)
        eq.info()
