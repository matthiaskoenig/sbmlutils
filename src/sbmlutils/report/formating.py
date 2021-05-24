"""Helper functions for formating SBML elements."""
import libsbml
import numpy as np

from src.sbmlutils.report import mathml

from typing import Dict, Optional


# -------------------------------------------------------------------------------------
# Core
# -------------------------------------------------------------------------------------

def sbo(item: libsbml.SBase) -> Dict:
    """Create HTML code fragment enclosing SBOTerm data for the item.

    :param item: SBML object for which SBOTerm data has to be displayed
    :return: Dictionary enclosing SBOTerm data for the item
    """

    sbo = {
        "url": item.getSBOTermAsURL(),
        "ID": item.getSBOTermID()
    } if item.isSetSBOTerm() else None

    return sbo


def sbaseref(sref: libsbml.SBaseRef) -> Optional[Dict]:
    """Format the SBaseRef instance.

    :param sref: SBaseRef instance
    :return: Dictionary containging formatted SBaseRef instance's data
    """

    if sref.isSetPortRef():
        return {
            "type": "port_ref",
            "value": sref.getPortRef()
        }
    elif sref.isSetIdRef():
        return {
            "type": "id_ref",
            "value": sref.getIdRef()
        }
    elif sref.isSetUnitRef():
        return {
            "type": "unit_ref",
            "value": sref.getUnitRef()
        }
    elif sref.isSetMetaIdRef():
        return {
            "type": "meta_ID_ref",
            "value": sref.getMetaIdRef()
        }
    return None


def id_dict(item: libsbml.SBase) -> Dict:
    """Create info from id and metaid.

    :param item: SBML object for which info is to be generated
    :return: HTML code fragment enclosing info for item
    """

    sid = item.getId()
    metaid = item.getMetaId() if item.isSetMetaId() else None

    info = {}
    if sid:
        display_sid = sid
        if isinstance(item, libsbml.RateRule) and item.isSetVariable():
            display_sid = "d {}/dt".format(item.getVariable())
        info = {
            "id": sid,
            "display_sid": display_sid,
            "meta": metaid
        }
    else:
        if metaid:
            info = {
                "meta": metaid
            }

    return info


def xml(item: libsbml.SBase) -> str:
    """Create SBML specification in XML for the item and return HTML code fragment.

    :param item: SBML object for which SBML specification (in XML) has to be created
    :return: HTML code fragment enclosing the SBML specification for the item
    """

    html = f"{item.toSBML()}"

    return html
    # return '<textarea style="border:none;">{}</textarea>'.format(item.toSBML())


def rule_variable_to_string(rule: libsbml.Rule) -> str:
    """Format variable for rule.

    :param rule: SBML rule instance
    :return formatted string representation of the rule
    """
    if isinstance(rule, libsbml.AlgebraicRule):
        return "0"
    elif isinstance(rule, libsbml.AssignmentRule):
        return rule.variable  # type: ignore
    elif isinstance(rule, libsbml.RateRule):
        return f"d {rule.variable}/dt"
    else:
        raise TypeError(rule)


# -------------------------------------------------------------------------------------
# Math
# -------------------------------------------------------------------------------------
def formula_to_mathml(string: str) -> str:
    """Parse formula string.

    :param string: formula string
    :return string rendering of parsed formula in the formula string
    """
    astnode = libsbml.parseL3Formula(str(string))
    mathml = libsbml.writeMathMLToString(astnode)
    return str(mathml)


def astnode_to_string(astnode: libsbml.ASTNode) -> str:
    """Convert to string representation.

    :param astnode: ASTNode instance
    :return string rendering of formula in the ASTnode instance
    """
    return str(libsbml.formulaToString(astnode))


def astnode_to_mathml(astnode: libsbml.ASTNode) -> str:
    """Convert to MathML string representation.

    :param astnode: ASTNode instance
    :return string rendering of MathML content for the ASTNode instance
    """
    return libsbml.writeMathMLToString(astnode)  # type: ignore


def math(sbase: libsbml.SBase, math_type: str = "cmathml") -> str:
    """Create MathML content for the item.

    :param sbase: SBML object for which MathML content is to be generated
    :param math_type: specifies which math rendering mode to use
    :return: formatted MathML content for the item
    """

    info = {}
    if sbase:
        if not isinstance(sbase, libsbml.ASTNode):
            astnode = sbase.getMath()
            if not astnode:
                info["type"] = None
                info["math"] = None
        else:
            astnode = sbase

            if math_type == "cmathml":
                info["type"] = "cmathml"
                info["math"] = astnode_to_mathml(astnode)
            elif math_type == "pmathml":
                info["type"] = "pmathml"
                cmathml = astnode_to_mathml(astnode)
                info["math"] = mathml.cmathml_to_pmathml(cmathml)
            elif math_type == "latex":
                info["type"] = "latex"
                latex_str = mathml.astnode_to_latex(astnode, model=sbase.getModel())
                info["math"] = f"$${latex_str}$$"
    else:
        info["type"] = None
        info["math"] = None

    return info


# -------------------------------------------------------------------------------------
# Equations
# -------------------------------------------------------------------------------------
def equation_from_reaction(
    reaction: libsbml.Reaction,
    sep_reversible: str = "&#8646;",
    sep_irreversible: str = "&#10142;",
    modifiers: bool = False,
) -> str:
    """Create equation for reaction.

    :param reaction: SBML reaction instance for which equation is to be generated
    :param sep_reversible: escape sequence for reversible equation (<=>) separator
    :param sep_irreversible: escape sequence for irreversible equation (=>) separator
    :param modifiers: boolean flag to use modifiers
    :return equation string generated for the reaction
    """

    left = _half_equation(reaction.getListOfReactants())
    right = _half_equation(reaction.getListOfProducts())
    if reaction.getReversible():
        # '<=>'
        sep = sep_reversible
    else:
        # '=>'
        sep = sep_irreversible
    if modifiers:
        mods = _modifier_equation(reaction.getListOfModifiers())
        if mods is None:
            return " ".join([left, sep, right])
        else:
            return " ".join([left, sep, right, mods])
    return " ".join([left, sep, right])


def _modifier_equation(modifierList: libsbml.ListOfSpeciesReferences) -> str:
    """Render string representation for list of modifiers.

    :param modifierList: list of modifiers
    :return: string representation for list of modifiers
    """
    if len(modifierList) == 0:
        return ""
    mids = [m.getSpecies() for m in modifierList]
    return "[" + ", ".join(mids) + "]"  # type: ignore


def _half_equation(speciesList: libsbml.ListOfSpecies) -> str:
    """Create equation string of the half reaction of the species in the species list.

    :param speciesList: list of species in the half reaction
    :return: half equation string
    """
    items = []
    for sr in speciesList:
        stoichiometry = sr.getStoichiometry()
        species = sr.getSpecies()
        if abs(stoichiometry - 1.0) < 1e-8:
            sd = f"{species}"
        elif abs(stoichiometry + 1.0) < 1e-8:
            sd = f"-{species}"
        elif stoichiometry >= 0:
            sd = f"{stoichiometry} {species}"
        elif stoichiometry < 0:
            sd = f"-{stoichiometry} {species}"
        items.append(sd)
    return " + ".join(items)

def species_dict(species: libsbml.SpeciesReference):
    return {
        "species": species.getSpecies() if species.isSetSpecies() else None,
        "stoichiometry": species.getStoichiometry() if species.isSetStoichiometry() else None,
        "constant": species.getConstant() if species.isSetConstant() else None
    }

# -------------------------------------------------------------------------------------
# FBC
# -------------------------------------------------------------------------------------
def boundsDictFromReaction(reaction: libsbml.Reaction, model: libsbml.Model) -> Dict:
    """Render string of bounds from the reaction.

    :param reaction: SBML reaction instance
    :param model: SBML model instance
    :return: String of bounds extracted from the reaction
    """
    bounds = {}
    rfbc = reaction.getPlugin("fbc")
    if rfbc is not None:
        # get values for bounds
        lb_id, ub_id = None, None
        lb_value, ub_value = None, None
        if rfbc.isSetLowerFluxBound():
            lb_id = rfbc.getLowerFluxBound()
            lb_p = model.getParameter(lb_id)
            if lb_p.isSetValue():
                lb_value = lb_p.getValue()
        if rfbc.isSetUpperFluxBound():
            ub_id = rfbc.getUpperFluxBound()
            ub_p = model.getParameter(ub_id)
            if ub_p.isSetValue():
                ub_value = ub_p.getValue()

        bounds["lb_value"] = lb_value
        bounds["ub_value"] = ub_value
    else:
        bounds = None

    return bounds


def geneProductAssociationDictFromReaction(reaction: libsbml.Reaction) -> Dict:
    """Render string representation of the GeneProductAssociation for given reaction.

    :param reaction: SBML reaction instance
    :return: string representation of GeneProductAssociation
    """

    rfbc = reaction.getPlugin("fbc")
    info = rfbc.getGeneProductAssociation().getAssociation().toInfix() if (
        rfbc and rfbc.isSetGeneProductAssociation()
    ) else None

    return info


# ------------
# ModelHistory
# ------------
def modelHistoryToString(mhistory: libsbml.ModelHistory) -> str:
    """Render HTML representation of the model history.

    :param mhistory: SBML ModelHistory instance
    :return HTML representation of the model history
    """
    if not mhistory:
        return None

    creators = []
    for kc in range(mhistory.getNumCreators()):
        cdata = {}
        c = mhistory.getCreator(kc)
        cdata["given_namw"] = c.getGivenName() if c.isSetGivenName() else None
        cdata["family_namw"] = c.getFamilyName() if c.isSetFamilyName() else None
        cdata["organization"] = c.getOrganization() if c.isSetOrganization() else None
        cdata["email"] = c.getEmail() if c.isSetEmail() else None

        creators.append(cdata)

    mhistory["creators"] = creators

    mhistory["created_date"] = dateToDict(mhistory.getCreatedDate()) if mhistory.isSetCreatedDate() else None

    modified_dates = []
    for km in range(mhistory.getNumModifiedDates()):
        modified_dates.append({
            "modified_date": dateToDict(mhistory.getModifiedDate(km))
        })
    mhistory["modified_dates"] = modified_dates if len(modified_dates) > 0 else None

    return mhistory


def dateToDict(d: libsbml.Date) -> Dict:
    """Create dictionary representation of date.

    :param d: SBML Date instance
    return dictionary containing date details
    """
    return {
        "date": {
            "year": d.getYear(),
            "month": str(d.getMonth()).zfill(2),
            "day": str(d.getDay()).zfill(2)
        },
        "time": {
            "hour": str(d.getHour()).zfill(2),
            "minute": str(d.getMinute()).zfill(2)
        }
    }


# -------------------------------------------------------------------------------------
# Units
# -------------------------------------------------------------------------------------
UNIT_ABBREVIATIONS = {
    "kilogram": "kg",
    "meter": "m",
    "metre": "m",
    "second": "s",
    "dimensionless": "",
    "katal": "kat",
    "gram": "g",
}

# still being used in convering derived units
def unitDefinitionToString(udef: libsbml.UnitDefinition) -> str:
    """Render formatted string for units.

    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    :param udef: unit definition which is to be converted to string
    """
    if udef is None:
        return "None"

    libsbml.UnitDefinition_reorder(udef)
    # collect formated nominators and denominators
    nom = []
    denom = []
    for u in udef.getListOfUnits():
        m = u.getMultiplier()
        s = u.getScale()
        e = u.getExponent()
        k = libsbml.UnitKind_toString(u.getKind())

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


def units_dict(udef: libsbml.UnitDefinition) -> Dict:
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
        kind = {
            "name": UNIT_ABBREVIATIONS.get(k, k)
        }

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

    res = {
        "nom_terms": nom_terms,
        "denom_terms": denom_terms
    }
    return res


def derived_units(item: libsbml.SBase) -> Dict:
    """Create formatted string for Unit definition object.

    :param item: SBML object from which Unit Definition string is to be created
    :return: formatted string for Unit Definition derived from the item
    """

    info = {
        "math": formula_to_mathml(
            item.getDerivedUnitDefinition()
        ),
        "unit_terms": units_dict(item.getDerivedUnitDefinition())
    } if item else None

    return info
