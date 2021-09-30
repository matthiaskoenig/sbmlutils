"""Helper functions for formating and rendering units."""
from typing import Dict, Optional
import numpy as np

import libsbml
import pint
from sbmlutils.console import console

ureg = pint.UnitRegistry()
ureg.define("item = dimensionless")
Q_ = ureg.Quantity


def udef_to_latex(ud: libsbml.UnitDefinition, model: libsbml.Model) -> Optional[str]:
    """Convert unit definition to latex."""

    if isinstance(ud, str):
        ud = model.getUnitDefinition(ud)

    return udef_to_string(ud, format="latex")


# FIXME: cache the results
def udef_to_string(
    udef: Optional[libsbml.UnitDefinition], format: str = "str"
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

    # collect nominators and denominators
    nom: str = ""
    nom_count = 0
    denom: str = ""
    denom_count = 0
    if udef:
        for u in udef.getListOfUnits():
            m = u.getMultiplier()
            s: int = u.getScale()
            e = u.getExponent()
            k = libsbml.UnitKind_toString(u.getKind())

            # (m * 10^s *k)^e
            # parse with pint
            term = Q_(float(m) * 10 ** s, k) ** float(abs(e))
            term = term.to_compact()

            if np.isclose(term.magnitude, 1.0):
                term = Q_(1, term.units)

            us = f"{term:~}"  # short formating
            # handle min and hr
            us = us.replace("60.0 s", "1 min")
            us = us.replace("3600.0 s", "1 hr")
            us = us.replace("3.6 ks", "1 hr")
            us = us.replace("86.4 ks", "1 day")

            # remove 1.0 prefixes
            us = us.replace("1 ", "")
            # exponent
            us = us.replace(" ** ", "^")

            if e >= 0.0:
                if nom == "":
                    nom = us
                else:
                    nom = f"{nom}*{us}"
                nom_count += 1
            else:
                if denom == "":
                    denom = us
                else:
                    denom = f"{denom}*{us}"
                denom_count += 1

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

    elif format == "latex":
        nom = nom.replace("*", " \\cdot ")
        denom = denom.replace("*", " \\cdot ")
        if nom and denom:
            ustr = f"\\frac{{{nom}}}/{{{denom}}}"
        elif nom and not denom:
            ustr = nom
        elif not nom and denom:
            ustr = f"\\frac{{1}}/{{{denom}}}"
    else:
        raise ValueError

    if ustr == "1":
        ustr = "-"

    console.rule()
    console.print(udef)
    console.print(f"'{ustr}'")

    return ustr


if __name__ == "__main__":
    import libsbml
    from rich import print

    from sbmlutils.factory import *


    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()

    for (key, definition, format, reference) in [
        ("mmole_per_min", "mmole/min", "str", "mmol/min"),
        ("m3", "meter^3", "str", "m^3"),
        ("m3", "meter^3/second", "str", "m^3/s"),
        ("mM", "mmole/liter", "str", "mmol/l"),
        ("ml_per_s_kg", "ml/s/kg", "str", "ml/s/kg"),
        ("dimensionless", "dimensionless", "str", "dimensionless"),

        # ("mM", "mmole/min", "latex", "\\frac{mmol}/{min}"),
    ]:

        ud = UnitDefinition(key, definition=definition)
        # ud = UnitDefinition("item")
        udef: libsbml.UnitDefinition = ud.create_sbml(model=model)

        console.rule()
        console.print(udef)
        console.print(udef_to_string(udef, format="str"))
        console.print(udef_to_string(udef, format="latex"))

    udef = model.getUnitDefinition("dimensionless")
    print(udef)
