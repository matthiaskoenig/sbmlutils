"""Helper functions for formating and rendering units."""

import contextlib

import libsbml
import numpy as np
import pint

from sbmlutils.console import console

ureg = pint.UnitRegistry()
ureg.define("item = dimensionless")
ureg.define("avogadro = 6.02214179E23 dimensionless")
Q_ = ureg.Quantity

short_names = {
    "metre": "m",
    "meter": "m",
    "liter": "l",
    "litre": "l",
    "dimensionless": "-",
    "second": "s",
}


#: units which are named for a multiple of an SBML base unit, as
#: (kind, factor, name); a factor is compared to the unit, never the text
_NAMED_UNITS: list[tuple[str, float, str]] = [
    ("second", 60.0, "min"),
    ("second", 3600.0, "hr"),
    ("second", 86400.0, "day"),
    ("metre", 0.01, "cm"),
]


def _unit_term_to_string(factor: float, kind: str) -> str:
    """Render a unit term `factor * kind` without its exponent.

    A factor which names a unit of its own (60 second is `min`) is rendered by
    that name. Otherwise the term is brought to the closest SI prefix and a
    magnitude which is not 1 is kept as a number in front of the unit,
    `160 s` or `2.1 g`. A dimensionless term is rendered by its magnitude
    only, and by the empty string if that is 1.

    Args:
        factor: the multiplier times ten to the power of the scale of the unit
        kind: the SBML unit kind, as `libsbml.UnitKind_toString` names it

    Returns:
        the short string of the term
    """
    for named_kind, named_factor, name in _NAMED_UNITS:
        if kind == named_kind and np.isclose(factor, named_factor):
            return name

    term = Q_(factor, kind)
    with contextlib.suppress(KeyError):
        term = term.to_compact()

    unit = f"{term.units:~}"
    magnitude = float(term.magnitude)
    if np.isclose(magnitude, 1.0):
        return unit
    number = f"{magnitude:g}"
    return f"{number} {unit}" if unit else number


def udef_to_string(
    udef: libsbml.UnitDefinition | str | None,
    model: libsbml.Model | None = None,
    format: str = "latex",
) -> str | None:
    """Render formatted string for units.

    Format can be either 'str' or 'latex'

    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    Returns None if udef is None or no units in UnitDefinition.

    :param udef: unit definition which is to be converted to string
    """
    if udef is None:
        return None

    ud: libsbml.UnitDefinition
    if isinstance(udef, str):
        # check for internal unit
        if libsbml.UnitKind_forName(udef) != libsbml.UNIT_KIND_INVALID:
            return short_names.get(udef, udef)
        if model is None:
            raise ValueError(
                f"A model is required to resolve the unit definition '{udef}'."
            )
        ud = model.getUnitDefinition(udef)
    else:
        ud = udef

    # collect nominators and denominators
    nom: str = ""
    denom: str = ""
    if ud:
        for u in ud.getListOfUnits():
            m = u.getMultiplier()
            s: int = u.getScale()
            e = u.getExponent()
            k = libsbml.UnitKind_toString(u.getKind())

            # (m * 10^s * k)^e
            us = _unit_term_to_string(factor=float(m) * 10**s, kind=k)
            if not us or e == 0.0:
                continue
            if abs(e) != 1.0:
                exponent = f"{abs(e):g}"
                # the exponent applies to the magnitude as well: (2.1 g)^2
                us = f"({us})^{exponent}" if " " in us else f"{us}^{exponent}"

            if e >= 0.0:
                nom = us if nom == "" else f"{nom}*{us}"
            else:
                denom = us if denom == "" else f"{denom}*{us}"

    else:
        nom = "-"

    if format == "str":
        denom = denom.replace("*", "/")
        if nom and denom:
            ustr = f"{nom}/{denom}"
        elif nom and not denom:
            ustr = nom
        elif not nom and denom:
            ustr = f"1/{denom}"
        elif not nom and not denom:
            ustr = "-"

    elif format == "latex":
        nom = nom.replace("*", " \\cdot ")
        denom = denom.replace("*", " \\cdot ")
        if nom and denom:
            ustr = f"\\frac{{{nom}}}{{{denom}}}"
        elif nom and not denom:
            ustr = nom
        elif not nom and denom:
            ustr = f"\\frac{{1}}{{{denom}}}"
        elif not nom and not denom:
            ustr = "-"
    else:
        raise ValueError

    if ustr == "1":
        ustr = "-"

    return ustr


if __name__ == "__main__":
    import libsbml

    from sbmlutils.factory import UnitDefinition

    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()

    for key, definition, _, _ in [
        # ("mmole_per_min", "mmole/min", "str", "mmol/min"),
        # ("m3", "meter^3", "str", "m^3"),
        # ("m3", "meter^3/second", "str", "m^3/s"),
        # ("mM", "mmole/liter", "str", "mmol/l"),
        # ("ml_per_s_kg", "ml/s/kg", "str", "ml/s/kg"),
        # ("dimensionless", "dimensionless", "str", "dimensionless"),
        ("item", "item", "str", "item"),
        # ("mM", "mmole/min", "latex", "\\frac{mmol}/{min}"),
    ]:
        ud = UnitDefinition(key, definition=definition)
        # ud = UnitDefinition("item")
        udef: libsbml.UnitDefinition | None = ud.create_sbml(model=model)

        console.rule()
        console.print(udef)
        console.print(udef_to_string(udef, format="str"))
        console.print(udef_to_string(udef, format="latex"))
