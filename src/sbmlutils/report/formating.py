"""Helper functions for formating SBML elements."""
import libsbml

from sbmlutils.metadata import miriam


def annotation_to_html(item: libsbml.SBase) -> str:
    """Render HTML representation of given annotation.

    :param item: SBase instance
    """
    lines = []
    for kcv in range(item.getNumCVTerms()):
        cv = item.getCVTerm(kcv)
        q_type = cv.getQualifierType()
        if q_type == 0:
            qualifier = miriam.ModelQualifierType[cv.getModelQualifierType()]
        elif q_type == 1:
            qualifier = miriam.BiologicalQualifierType[cv.getBiologicalQualifierType()]
        lines.append("".join(['<span class="collection">', qualifier, "</span>"]))

        items = []
        for k in range(cv.getNumResources()):
            uri = cv.getResourceURI(k)
            tokens = uri.split("/")
            resource_id = tokens[-1]
            link = "".join(
                ['<a href="', uri, '" target="_blank">', resource_id, "</a>"]
            )
            items.append(link)
        lines.append("; ".join(items))
    res = "<br />".join(lines)
    return res


def notes_to_string(sbase: libsbml.SBase) -> str:
    """Render notes to string.

    :param sbase: SBase instance
    :return string rendering of the notes in the SBase instance
    """
    return sbase.getNotesString()


def formula_to_mathml(string: str) -> str:
    """Parse formula string.

    :param string: formula string
    :return string rendering of parsed formula in the formula string
    """
    astnode = libsbml.parseL3Formula(str(string))
    mathml = libsbml.writeMathMLToString(astnode)
    return mathml


def astnode_to_string(astnode: libsbml.ASTNode) -> str:
    """Convert to string representation.

    :param astnode: ASTNode instance
    :return string rendering of formula in the ASTnode instance
    """
    return libsbml.formulaToString(astnode)


def astnode_to_mathml(astnode: libsbml.ASTNode) -> str:
    """Convert to MathML string representation.

    :param astnode: ASTNode instance
    :return string rendering of MathML content for the ASTNode instance
    """
    return libsbml.writeMathMLToString(astnode)


# ---------
# Equations
# ---------
def equationStringFromReaction(
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

    left = _halfEquation(reaction.getListOfReactants())
    right = _halfEquation(reaction.getListOfProducts())
    if reaction.getReversible():
        # '<=>'
        sep = sep_reversible
    else:
        # '=>'
        sep = sep_irreversible
    if modifiers:
        mods = _modifierEquation(reaction.getListOfModifiers())
        if mods is None:
            return " ".join([left, sep, right])
        else:
            return " ".join([left, sep, right, mods])
    return " ".join([left, sep, right])


def _modifierEquation(modifierList: libsbml.ListOfSpeciesReferences) -> str:
    """Render string representation for list of modifiers.

    :param modifierList: list of modifiers
    :return: string representation for list of modifiers
    """
    if len(modifierList) == 0:
        return None
    mids = [m.getSpecies() for m in modifierList]
    return "[" + ", ".join(mids) + "]"


def _halfEquation(speciesList: libsbml.ListOfSpecies) -> str:
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


# ------------------------------
# FBC
# ------------------------------
def boundsStringFromReaction(reaction: libsbml.Reaction, model: libsbml.Model) -> str:
    """Render string of bounds from the reaction.

    :param reaction: SBML reaction instance
    :param model: SBML model instance
    :return: String of bounds extracted from the reaction
    """
    bounds = ""
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
        if (lb_value is not None) or (ub_value is not None):
            bounds = f"""
                    <code>[{lb_value}
                    <i class="fa fa-sort fa-rotate-90" aria-hidden="true"></i>
                    {ub_value}]
                    </code>
                    """
    return bounds


def geneProductAssociationStringFromReaction(reaction: libsbml.Reaction) -> str:
    """Render string representation of the GeneProductAssociation for given reaction.

    :param reaction: SBML reaction instance
    :return: string representation of GeneProductAssociation
    """
    info = ""
    rfbc = reaction.getPlugin("fbc")

    if rfbc and rfbc.isSetGeneProductAssociation():
        gpa = rfbc.getGeneProductAssociation()
        association = gpa.getAssociation()
        info = association.toInfix()
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
        return ""
    items = []
    items.append("<b>Creator</b>")
    for kc in range(mhistory.getNumCreators()):
        cdata = []
        c = mhistory.getCreator(kc)
        if c.isSetGivenName():
            cdata.append(c.getGivenName())
        if c.isSetFamilyName():
            cdata.append(c.getFamilyName())
        if c.isSetOrganisation():
            cdata.append(c.getOrganisation())
        if c.isSetEmail():
            cdata.append(
                f'<a href="mailto:{c.getEmail()}" target="_blank">{c.getEmail()}</a>'
            )
        items.append(", ".join(cdata))
    if mhistory.isSetCreatedDate():
        items.append("<b>Created:</b> " + dateToString(mhistory.getCreatedDate()))
    for km in range(mhistory.getNumModifiedDates()):
        items.append("<b>Modified:</b> " + dateToString(mhistory.getModifiedDate(km)))
    items.append("<br />")
    return "<br />".join(items)


def dateToString(d: libsbml.Date) -> str:
    """Create string representation of date.

    :param d: SBML Date instance
    return string representation of date
    """
    return (
        f"{d.getYear()}-{str(d.getMonth()).zfill(2)}-{str(d.getDay()).zfill(2)} "
        f"{str(d.getHour()).zfill(2)}:{str(d.getMinute()).zfill(2)}"
    )


def _isclose(a: float, b: float, rel_tol: float = 1e-09, abs_tol: float = 0.0) -> bool:
    """Calculate the two floats are identical.

    :param a: float value
    :param b: float value
    :param rel_tol: relative tolerance value
    :param abs_tol: absolute tolerance value
    """
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def ruleVariableToString(rule: libsbml.Rule) -> str:
    """Format variable for rule.

    :param rule: SBML rule instance
    :return formatted string representation of the rule
    """
    if isinstance(rule, libsbml.AlgebraicRule):
        return "0"
    elif isinstance(rule, libsbml.AssignmentRule):
        return rule.variable
    elif isinstance(rule, libsbml.RateRule):
        return f"d {rule.variable}/dt"
    else:
        raise TypeError(rule)


# ---------------
# UnitDefinitions
# ---------------
UNIT_ABBREVIATIONS = {
    "kilogram": "kg",
    "meter": "m",
    "metre": "m",
    "second": "s",
    "dimensionless": "",
    "katal": "kat",
    "gram": "g",
}


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
        if _isclose(m, 1.0):
            m_str = ""
        else:
            m_str = str(m) + "*"

        if _isclose(abs(e), 1.0):
            e_str = ""
        else:
            e_str = "^" + str(abs(e))

        if _isclose(s, 0.0):
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
