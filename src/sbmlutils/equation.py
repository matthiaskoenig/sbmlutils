"""Module for parsing equation strings.

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
"""

import re
from collections import namedtuple
from typing import Iterable, List, Optional


Part = namedtuple("Part", "stoichiometry sid")

REV_PATTERN = r"<[-=]>"
IRREV_PATTERN = r"[-=]>"
MOD_PATTERN = r"\[.*\]"
REV_SEP = r"<=>"
IRREV_SEP = r"=>"


class Equation:
    """Representation of stoichiometric equations with modifiers."""

    class EquationException(Exception):
        """Exception in Equation."""

        pass

    def __init__(self, equation: str):
        """Initialize equation."""
        self.raw = equation

        self.reactants: List[Part] = []
        self.products: List[Part] = []
        self.modifiers: List[str] = []
        self.reversible: Optional[bool] = None

        self._parse_equation()

    def _parse_equation(self) -> None:
        """Parse components of equation string."""
        eq_string = self.raw[:]

        # handle empty equation (for dummy reations in comp)
        if len(eq_string) == 0:
            self.reversible = True
            return

        # get modifiers and remove from equation string
        mod_list = re.findall(MOD_PATTERN, eq_string)
        if len(mod_list) == 1:
            self._parse_modifiers(mod_list[0])
            tokens = eq_string.split("[")
            eq_string = tokens[0].strip()
        elif len(mod_list) > 1:
            raise self.EquationException(
                "Invalid equation: {}. "
                "Modifier list could not be parsed. "
                "{}".format(self.raw, Equation.help())
            )

        # now parse the equation without modifiers
        items = re.split(REV_PATTERN, eq_string)

        if len(items) == 2:
            self.reversible = True
        elif len(items) == 1:
            items = re.split(IRREV_PATTERN, eq_string)
            self.reversible = False
        else:
            raise self.EquationException(
                "Invalid equation: {}. "
                "Equation could not be split into left "
                "and right side. {}".format(self.raw, Equation.help())
            )

        # remove whitespaces
        items = [o.strip() for o in items]
        if len(items) < 2:
            raise self.EquationException(
                "Invalid equation: {}. "
                "Equation could not be split into left "
                "and right side. Use '<=>' or '=>' as separator. "
                "{}".format(self.raw, Equation.help())
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

    def _parse_half_equation(self, string: str) -> List[Part]:
        """Parse half-equation.

        Only '+ supported in equation !, do not use negative stoichiometries.
        """
        items = re.split("[+-]", string)
        items = [item.strip() for item in items]
        return [self._parse_reactant(item) for item in items]

    @staticmethod
    def _parse_reactant(item: str) -> Part:
        """Return tuple of stoichiometry, sid."""
        tokens = item.split()
        if len(tokens) == 1:
            stoichiometry = 1.0
            sid = tokens[0]
        else:
            stoichiometry = float(tokens[0])
            sid = " ".join(tokens[1:])
        return Part(stoichiometry, sid)

    @staticmethod
    def _to_string_side(items: Iterable[Part]) -> str:
        tokens = []
        for item in items:
            stoichiometry, sid = item[0], item[1]
            if abs(1.0 - stoichiometry) < 1e-10:
                tokens.append(sid)
            else:
                tokens.append(" ".join([str(stoichiometry), sid]))
        return " + ".join(tokens)

    def _to_string_modifiers(self) -> str:
        return "[{}]".format(", ".join(self.modifiers))

    def to_string(self, modifiers: bool = False) -> str:
        """Get string representation of equation."""
        left = self._to_string_side(self.reactants)
        right = self._to_string_side(self.products)
        if self.reversible:
            sep = REV_SEP
        else:
            sep = IRREV_SEP

        if modifiers:
            mod = self._to_string_modifiers()
            return " ".join([left, sep, right, mod])
        else:
            return " ".join([left, sep, right])

    def info(self) -> None:
        """Print overview of parsed equation."""
        lines = [
            "{:<10s} : {}".format("raw", self.raw),
            "{:<10s} : {}".format("parsed", self.to_string()),
            "{:<10s} : {}".format("reversible", self.reversible),
            "{:<10s} : {}".format("reactants", self.reactants),
            "{:<10s} : {}".format("products", self.products),
            "{:<10s} : {}".format("modifiers", self.modifiers),
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

    tests = [
        "1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]",
        "c__gal1p => c__gal + c__phos",
        "e__h2oM <-> c__h2oM",
        "3 atp + 2.0 phos + ki <-> 16.98 tet",
        "c__gal1p => c__gal + c__phos [c__udp, c__utp]",
        "A_ext => A []",
        "=> cit",
        "acoa =>",
    ]

    for test in tests:
        print("-" * 40)
        print(test)
        print("-" * 40)
        eq = Equation(test)
        eq.info()
