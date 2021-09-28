"""Helper functions for formating and rendering units.

# FIXME: use pint or similar thing for simplification of units
"""
from typing import Dict, Optional

import libsbml
import numpy as np
import pint

from sbmlutils.report.mathml import astnode_to_latex


ureg = pint.UnitRegistry()
ureg.define("item = dimensionless")
Q_ = ureg.Quantity

UNIT_ABBREVIATIONS = {
    "kilogram": "kg",
    "meter": "m",
    "metre": "m",
    "second": "s",
    "dimensionless": "",
    "katal": "kat",
    "gram": "g",
}


def udef_to_latex(ud: libsbml.UnitDefinition, model: libsbml.Model) -> Optional[str]:
    """Convert unit definition to latex."""
    if ud is None or ud == "None":
        return None

    if isinstance(ud, str):
        ud = model.getUnitDefinition(ud)

    ud_str: Optional[str] = udef_to_string(ud)
    if not ud_str:
        return None

    astnode = libsbml.parseL3FormulaWithModel(ud_str, model=model)
    if astnode is None:
        return None

    latex = astnode_to_latex(astnode)
    return latex


def udef_to_string2(udef: libsbml.UnitDefinition) -> Optional[str]:
    """Render formatted string for units.

    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    Returns None if udef is None or no units in UnitDefinition.

    :param udef: unit definition which is to be converted to string
    """
    # order units alphabetically
    # libsbml.UnitDefinition_reorder(udef)

    # FIXME: add item/avogadro

    unit = Q_(1, "dimensionless")
    if udef:
        for u in udef.getListOfUnits():
            m = u.getMultiplier()
            s: int = u.getScale()
            e = u.getExponent()
            k = libsbml.UnitKind_toString(u.getKind())

            # (m * 10^s *k)^e
            term = Q_(float(m) * 10 ** s, k) ** float(e)
            unit = unit * term

    # parse with pint
    unit = unit.to_compact()  # to_base_units().to_root_units()
    # print(unit)

    return str(unit)


def udef_to_string(udef: libsbml.UnitDefinition) -> Optional[str]:
    """Render formatted string for units.

    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    Returns None if udef is None or no units in UnitDefinition.

    :param udef: unit definition which is to be converted to string
    """
    if udef is None:
        return None

    # order units alphabetically
    libsbml.UnitDefinition_reorder(udef)

    # collect formated nominators and denominators
    nom = []
    denom = []
    for u in udef.getListOfUnits():
        m = u.getMultiplier()
        s = u.getScale()
        e = u.getExponent()
        k = libsbml.UnitKind_toString(u.getKind())
        if k == "metre":
            k = "meter"
        if k == "litre":
            k = "liter"

        # get better name for unit
        k_str = UNIT_ABBREVIATIONS.get(k, k)

        # (m * 10^s *k)^e

        # handle m
        if np.isclose(m, 1.0):
            m_str = ""
        else:
            m_str = str(m) + "*"

        if np.isclose(abs(e), 1.0):
            e_str = ""
        else:
            e_str = "^" + str(abs(e))

        if np.isclose(s, 0.0):
            string = f"{m_str}{k_str}{e_str}"
        else:
            if e_str == "":
                string = f"({m_str}10^{s})*{k_str}"
            else:
                string = f"(({m_str}10^{s})*{k_str}){e_str}"

        # collect the terms
        if e >= 0.0:
            nom.append(string)
        else:
            denom.append(string)

    nom_str = " * ".join(nom)
    denom_str = " * ".join(denom)
    if (len(nom_str) > 0) and (len(denom_str) > 0):
        return f"({nom_str})/({denom_str})"
    if (len(nom_str) > 0) and (len(denom_str) == 0):
        return nom_str
    if (len(nom_str) == 0) and (len(denom_str) > 0):
        return f"1/({denom_str})"
    return ""


def units_dict(udef: libsbml.UnitDefinition) -> Optional[Dict]:
    """Render dictionary for units.

    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    :param udef: unit definition which is to be converted to dictionary
    """
    if udef is None:
        return None

    libsbml.UnitDefinition_reorder(udef)
    # collect formatted nominators and denominators
    nom_terms = []
    denom_terms = []
    for u in udef.getListOfUnits():
        m = u.getMultiplier()
        s = u.getScale()
        e = u.getExponent()
        k = libsbml.UnitKind_toString(u.getKind())

        # get better name for unit
        kind = {"name": UNIT_ABBREVIATIONS.get(k, k)}

        # (m * 10^s *k)^e
        unit = {
            "scale": s,
            "multiplier": m,
            "exponent": abs(e),
            "kind": kind,
        }

        # collect the terms
        if e >= 0.0:
            nom_terms.append(unit)
        else:
            denom_terms.append(unit)

    res = {"nom_terms": nom_terms, "denom_terms": denom_terms}
    return res


if __name__ == "__main__":
    import libsbml

    from sbmlutils.factory import *

    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()

    # ud = UnitDefinition("mM", definition="mmole/min")
    ud = UnitDefinition("item")
    udef: libsbml.UnitDefinition = ud.create_sbml(model=model)
    print(udef)
    ustr = udef_to_string(udef)
    print(ustr)
