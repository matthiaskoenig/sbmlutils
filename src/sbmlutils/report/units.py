"""Helper functions for formating and rendering units."""
from typing import Optional, Union

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


def udef_to_string(
    udef: Optional[Union[libsbml.UnitDefinition, str]],
    model: Optional[libsbml.Model] = None,
    format: str = "latex",
) -> Optional[str]:
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
        else:
            ud = model.getUnitDefinition(udef)  # type: ignore
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

            # (m * 10^s *k)^e
            # parse with pint
            term = Q_(float(m) * 10**s, k) ** float(abs(e))
            try:
                term = term.to_compact()
            except KeyError:
                pass

            if np.isclose(term.magnitude, 1.0):
                term = Q_(1, term.units)

            us = f"{term:~}"  # short formating
            # handle min and hr
            us = us.replace("60.0 s", "1 min")
            us = us.replace("3600.0 s", "1 hr")
            us = us.replace("3.6 ks", "1 hr")
            us = us.replace("86.4 ks", "1 day")
            us = us.replace("10.0 mm", "1 cm")

            # remove 1.0 prefixes
            us = us.replace("1 ", "")
            # exponent
            us = us.replace(" ** ", "^")

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

    # json escape

    return ustr


if __name__ == "__main__":
    import libsbml

    from sbmlutils.factory import *

    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()

    for (key, definition, _, _) in [
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
        udef: libsbml.UnitDefinition = ud.create_sbml(model=model)

        console.rule()
        console.print(udef)
        console.print(udef_to_string(udef, format="str"))
        console.print(udef_to_string(udef, format="latex"))
