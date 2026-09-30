"""Module for parsing reaction equation strings.

Various string formats are allowed which are subsequently brought into
an internal standard format.

Equations are of the form
    '1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]'

The equation consists of
- substrates concatenated via '+' on the left side
  (with optional stoichiometric coefficients, which may be written in
  scientific notation like '1e-3')
- separation characters separating the left and right equation sides:
  '<=>' or '<->' for reversible reactions,
  '=>' or '->' for irreversible reactions (irreversible reactions
  are written from left to right)
- products concatenated via '+' on the right side
  (with optional stoichiometric coefficients)
- optional list of modifiers within brackets [] separated by ',' at the
  end of the equation

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

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Final

logger = logging.getLogger(__name__)


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
    stoichiometry: float | None = None
    sid: str | None = None
    constant: bool = True
    metaId: str | None = field(default=None, repr=False)
    sboTerm: str | None = field(default=None, repr=False)
    name: str | None = field(default=None, repr=False)
    annotations: list | None = field(default=None, repr=False)
    notes: str | None = field(default=None, repr=False)
    keyValuePairs: list[Any] | None = field(default=None, repr=False)


REVERSIBILITY_PATTERN: Final = r"<[-=]>"
IRREVERSIBILITY_PATTERN: Final = r"[-=]>"
#: any separator of the two sides, reversible or irreversible
SEPARATOR_PATTERN: Final = r"<?[-=]>"
#: the single modifier list, which closes the equation
MODIFIER_PATTERN: Final = r"\[([^\[\]]*)\]\s*$"
#: the '+' between the parts of a side, but not the sign of an exponent
#: of a stoichiometry in scientific notation like '2.5e+2'
PART_SEPARATOR_PATTERN: Final = r"(?<![0-9.][eE])\+|\+(?!\d)"
REVERSIBILITY_SEPARATOR: Final = r"<=>"
IRREVERSIBILITY_SEPARATOR: Final = r"=>"


class ReactionEquation:
    """Representation of stoichiometric equations with modifiers."""

    class EquationException(ValueError):
        """Exception in Equation, an invalid equation string."""

    def __init__(
        self,
        reactants: list[EquationPart] | None = None,
        products: list[EquationPart] | None = None,
        modifiers: list[EquationPart | str] | None = None,
        reversible: bool = True,
    ):
        """Initialize equation.

        A modifier may be given as a bare species id, which is the documented
        string syntax, or as a full `EquationPart` carrying its own SBase
        fields. Both are stored as `EquationPart`.
        """
        self.reversible: bool = reversible
        self.reactants: list[EquationPart] = reactants if reactants else []
        self.products: list[EquationPart] = products if products else []
        self.modifiers: list[EquationPart] = [
            EquationPart(species=modifier) if isinstance(modifier, str) else modifier
            for modifier in (modifiers if modifiers else [])
        ]

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

        # get the modifiers, a single list which closes the equation
        full_str = equation_str
        match = re.search(MODIFIER_PATTERN, equation_str)
        if match:
            self._parse_modifiers(match.group(1))
            equation_str = equation_str[: match.start()]
        if "[" in equation_str or "]" in equation_str:
            raise self.EquationException(
                f"Invalid equation: {full_str}. "
                f"Modifier list could not be parsed, use a single list "
                f"'[M1, M2]' at the end of the equation. "
                f"{ReactionEquation.help()}"
            )

        # now parse the equation without modifiers
        separators = re.findall(SEPARATOR_PATTERN, equation_str)
        if len(separators) != 1:
            raise self.EquationException(
                f"Invalid equation: {full_str}. "
                f"Equation could not be split into left and right side, "
                f"use a single '<=>' or '=>' as separator. "
                f"{ReactionEquation.help()}"
            )
        self.reversible = re.fullmatch(REVERSIBILITY_PATTERN, separators[0]) is not None
        left, right = (o.strip() for o in re.split(SEPARATOR_PATTERN, equation_str))
        if len(left) > 0:
            self.reactants = self._parse_half_equation(left)
        if len(right) > 0:
            self.products = self._parse_half_equation(right)

    def _parse_modifiers(self, s: str) -> None:
        """Parse the content of the modifier list, without its brackets."""
        tokens = re.split("[,;]", s.strip())
        modifiers = [t.strip() for t in tokens]
        self.modifiers = [
            EquationPart(species=modifier)
            for modifier in modifiers
            if len(modifier) > 0
        ]

    def _parse_half_equation(self, string: str) -> list[EquationPart]:
        """Parse half-equation.

        The parts are separated by '+', negative stoichiometries are not
        supported.
        """
        if re.search(r"(?<![0-9.][eE])-", string):
            raise self.EquationException(
                f"Invalid equation side: '{string}'. "
                f"Parts are separated by '+', a '-' and negative "
                f"stoichiometries are not supported. {ReactionEquation.help()}"
            )
        items = [item.strip() for item in re.split(PART_SEPARATOR_PATTERN, string)]
        if any(not item for item in items):
            raise self.EquationException(
                f"Invalid equation side: '{string}'. "
                f"A '+' must separate two species. {ReactionEquation.help()}"
            )
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
        return f"[{', '.join(modifier.species for modifier in self.modifiers)}]"

    def to_string(self, modifiers: bool = False) -> str:
        """Get string representation of equation."""
        left = self._to_string_side(self.reactants)
        right = self._to_string_side(self.products)
        sep = REVERSIBILITY_SEPARATOR if self.reversible else IRREVERSIBILITY_SEPARATOR

        if modifiers:
            mod = self._to_string_modifiers()
            return " ".join([left, sep, right, mod])
        return " ".join([left, sep, right])

    def info(self) -> None:
        """Log overview of parsed equation."""
        lines = [
            f"{'equation':<10s}: {self.to_string(modifiers=True)}",
            f"{'reversible':<10s}: {self.reversible}",
            f"{'reactants':<10s}: {self.reactants}",
            f"{'products':<10s}: {self.products}",
            f"{'modifiers':<10s}: {self.modifiers}",
        ]
        logger.info("%s", "\n".join(lines))

    @staticmethod
    def help() -> str:
        """Get help information string."""
        return """
        For information on the supported equation format use
            from sbmlutils import reaction_equation
            help(reaction_equation)
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
