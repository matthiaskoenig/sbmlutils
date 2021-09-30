"""Helper functions for formating and rendering units."""
from typing import Dict, Optional

import libsbml
import pint

ureg = pint.UnitRegistry()
ureg.define("item = dimensionless")
Q_ = ureg.Quantity


def udef_to_latex(ud: libsbml.UnitDefinition, model: libsbml.Model) -> Optional[str]:
    """Convert unit definition to latex."""

    if isinstance(ud, str):
        ud = model.getUnitDefinition(ud)

    return udef_to_string(ud, format="latex")


def udef_to_string(udef: Optional[libsbml.UnitDefinition], format: str="str") -> Optional[str]:
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
    denom: str = ""
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

            us = f"{term:~}"  # short formating
            # handle min and hr
            us = us.replace("60.0 s", "1.0 min")
            us = us.replace("3600.0 s", "1.0 hr")
            # remove 1.0 prefixes
            us = us.replace("1.0 ", "")

            if e >= 0.0:
                if nom == "":
                    nom = us
                else:
                    nom = f"{nom}*{us}"
            else:
                if denom == "":
                    denom = us
                else:
                    denom = f"{denom}*{us}"

    else:
        nom = 'dimensionless'

    if format == "str":
        if nom and denom:
            ustr = f"{nom}/{denom}"
        elif nom and not denom:
            ustr = nom
        elif not nom and denom:
            f"1/{denom}"

    elif format =="latex":
        nom = nom.replace("*", " \\cdot ")
        denom = denom.replace("*", " \\cdot ")
        if nom and denom:
            ustr = f"\\frac{{{nom}}}/{{{denom}}}"
        elif nom and not denom:
            ustr = nom
        elif not nom and denom:
            ustr = f"\\frac{{{1}}}/{{{denom}}}"

    else:
        raise ValueError

    return ustr


if __name__ == "__main__":
    from rich import print

    import libsbml

    from sbmlutils.factory import *

    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()

    ud = UnitDefinition("mM", definition="mmole/min")
    # ud = UnitDefinition("item")
    udef: libsbml.UnitDefinition = ud.create_sbml(model=model)

    print("-" * 40)
    print(udef)
    print(udef_to_string(udef, format="str"))
    print(udef_to_string(udef, format="latex"))
    print("-" * 40)
