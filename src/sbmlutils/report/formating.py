"""Helper functions for formating SBML elements."""
from typing import Optional

import libsbml

from sbmlutils import utils
from sbmlutils.metadata import miriam
from sbmlutils.report import mathml

from typing import Dict, List


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

def annotation_dict(item: libsbml.SBase) -> Dict:
    """Render dictionary representation of given annotation.

    :param item: SBase instance
    """
    res = {}
    res["cvterms"] = []
    for kcv in range(item.getNumCVTerms()):
        info = {}
        cv = item.getCVTerm(kcv)
        q_type = cv.getQualifierType()
        if q_type == 0:
            qualifier = miriam.ModelQualifierType[cv.getModelQualifierType()]
        elif q_type == 1:
            qualifier = miriam.BiologicalQualifierType[cv.getBiologicalQualifierType()]
        info["qualifier"] = qualifier

        links = []
        for k in range(cv.getNumResources()):
            uri = cv.getResourceURI(k)
            tokens = uri.split("/")
            resource_id = tokens[-1]
            link = {
                "resource_id": resource_id,
                "uri": uri
            }
            links.append(link)
        info["links"] = links

        res["cvterms"].append(info)
    return res

def notes_to_string(sbase: libsbml.SBase) -> str:
    """Render notes to string.

    :param sbase: SBase instance
    :return string rendering of the notes in the SBase instance
    """
    return str(sbase.getNotesString())


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
        return ""
    mids = [m.getSpecies() for m in modifierList]
    return "[" + ", ".join(mids) + "]"  # type: ignore


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
            bounds = {
                "lb_value": lb_value,
                "ub_value": ub_value
            }
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
        return {}
    creators = []
    for kc in range(mhistory.getNumCreators()):
        cdata = {}
        c = mhistory.getCreator(kc)
        if c.isSetGivenName():
            cdata["given_namw"] = c.getGivenName()
        if c.isSetFamilyName():
            cdata["family_name"] = c.getFamilyName()
        if c.isSetOrganisation():
            cdata["organization"] = c.getOrganisation()
        if c.isSetEmail():
            cdata["email"] = c.getEmail()
        creators.append(cdata)

    mhistory["creators"] = creators

    if mhistory.isSetCreatedDate():
        mhistory["created_date"] = dateToDict(mhistory.getCreatedDate())
    modified_dates = []
    for km in range(mhistory.getNumModifiedDates()):
        modified_dates.append({
            "modified_date": dateToDict(mhistory.getModifiedDate(km))
        })
    mhistory["modified_dates"] = modified_dates
    return mhistory

def dateToString(d: libsbml.Date) -> str:
    """Create string representation of date.

    :param d: SBML Date instance
    return string representation of date
    """
    return (
        f"{d.getYear()}-{str(d.getMonth()).zfill(2)}-{str(d.getDay()).zfill(2)} "
        f"{str(d.getHour()).zfill(2)}:{str(d.getMinute()).zfill(2)}"
    )

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
        return rule.variable  # type: ignore
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


def unit_definitions_dict(udef: libsbml.UnitDefinition) -> Dict:
    """Render dictionary for units.

    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    :param udef: unit definition which is to be converted to dictionary
    """
    if udef is None:
        return {}

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

        # handle m
        multiplier = {
            "is_close": _isclose(m, 1.0),
            "value": m
        }

        exponent = {
            "is_close": _isclose(abs(e), 1.0),
            "value": abs(e)
        }

        unit = {
            "is_close": _isclose(s, 0.0),
            "scale": s,
            "multiplier": multiplier,
            "exponent": exponent,
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

def notes(item: libsbml.SBase) -> str:
    """Convert the SBML object's notes subelement to formatted string.

    :param item: SBML object containing the notes subelement
    :return: formatted string for the notes subelement of the item
    """
    if item.isSetNotes():
        return notes_to_string(item)
    return ""


def cvterm(item: libsbml.SBase) -> Dict:
    """Create HTML code fragment enclosing cvterm data for the item.

    :param item: SBML object for which cvterm data has to be displayed
    :return: HTML code fragment enclosing cvterm data for the item
    """
    if item.isSetAnnotation():
        return annotation_dict(item)
    return {}


def sbo(item: libsbml.SBase) -> Dict:
    """Create HTML code fragment enclosing SBOTerm data for the item.

    :param item: SBML object for which SBOTerm data has to be displayed
    :return: Dictionary enclosing SBOTerm data for the item
    """

    if item.getSBOTerm() != -1:
        return {
            "url": item.getSBOTermAsURL(),
            "ID": item.getSBOTermID()
        }
    return {}


def sbaseref(sref: libsbml.SBaseRef) -> Dict:
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
    return {}


def empty_html() -> str:
    """Create a blank HTML code fragment."""

    return '<i class="fa fa-ban gray"></i>'


def metaid(item: libsbml.SBase) -> str:
    """Create metaid data for the item.

    :param item: SBML object for which metaid data has to be generated
    :return: HTML code fragment enclosing metaid data for item
    """
    if item.isSetMetaId():
        return str(item.getMetaId())
    return ""


def id_dict(item: libsbml.SBase) -> Dict:
    """Create info from id and metaid.

    :param item: SBML object for which info is to be generated
    :return: HTML code fragment enclosing info for item
    """

    sid = item.getId()
    meta = metaid(item)

    info = {}
    if sid:
        display_sid = sid
        if isinstance(item, libsbml.RateRule) and item.isSetVariable():
            display_sid = "d {}/dt".format(item.getVariable())
        info = {
            "id": sid,
            "display_sid": display_sid,
            "meta": meta
        }
    else:
        if meta:
            info = {
                "meta": meta
            }

    # create modal information
    info["xml_modal"] = xml_modal(item)

    return info


def annotation_html(item: libsbml.SBase) -> str:
    """Create annotation HTML content for the item.

    :param item: SBML object for which annotation HTML content is to be generated
    :return: HTML code fragment enclosing annotation for item
    """

    info = '<div class="cvterm">'
    if item.getSBOTerm() != -1:
        info += f"""
            <a href="{item.getSBOTermAsURL()}" target="_blank">
                {item.getSBOTermID()}
            </a><br />
            """
    if item.isSetAnnotation():
        info += annotation_to_html(item)
    info += "</div>"
    return info


def math(sbase: libsbml.SBase, math_type: str = "cmathml") -> str:
    """Create MathML content for the item.

    :param sbase: SBML object for which MathML content is to be generated
    :param math_type: specifies which math rendering mode to use
    :return: formatted MathML content for the item
    """

    if sbase:
        if not isinstance(sbase, libsbml.ASTNode):
            astnode = sbase.getMath()
            if not astnode:
                return empty_html()
        else:
            astnode = sbase
        if math_type == "cmathml":
            return astnode_to_mathml(astnode)
        elif math_type == "pmathml":
            cmathml = astnode_to_mathml(astnode)
            return mathml.cmathml_to_pmathml(cmathml)
        elif math_type == "latex":
            latex_str = mathml.astnode_to_latex(astnode, model=sbase.getModel())
            return f"$${latex_str}$$"
    return empty_html()


def boolean(condition: bool) -> bool:
    """Check the truth value of condition and create corresponding HTML code fragment.

    :param condition: condition for which the truth value is to be checked
    :return: boolean value of the condition
    """

    return condition


def annotation_xml(item: libsbml.SBase) -> str:
    """Create Annotation string for the item.

    :param item: SBML object for which MathML content is to be generated
    :return: Annotation string for the item
    """
    if item.isSetAnnotation():
        return f"<pre>{item.getAnnotationString().decode('utf-8')}</pre>"
    return ""


def xml_modal(item: libsbml.SBase) -> str:
    """Create modal information for a given sbase.

    This provides some popup which allows to inspect the xml content of the element.

    :param item: SBML object for which xml content is to be created
    :return: HTML code fragment enclosing the xml content for the item
    """
    # filter sbase
    if type(item) is libsbml.Model:
        return ""

    hash_id = utils.create_hash_id(item)

    info = f"""
      <button type="button" class="btn btn-default btn-xs" data-toggle="modal"
         data-target="#model-{hash_id}">
        <i class="fa fa-code"></i>
      </button>
      <div class="modal fade" id="model-{hash_id}" role="dialog">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header"><h4 class="modal-title">{hash_id}</h4></div>
            <div class="modal-body">
                <textarea rows="20" class="form-control"
                    style="min-width: 100%; font-family: 'Courier New'">
                    {xml(item)}
                </textarea>
            </div>
          </div>
        </div>
      </div>
    """
    return info


def xml(item: libsbml.SBase) -> str:
    """Create SBML specification in XML for the item and return HTML code fragment.

    :param item: SBML object for which SBML specification (in XML) has to be created
    :return: HTML code fragment enclosing the SBML specification for the item
    """

    html = f"{item.toSBML()}"

    return html
    # return '<textarea style="border:none;">{}</textarea>'.format(item.toSBML())


def derived_units(item: libsbml.SBase) -> str:
    """Create formatted string for Unit definition object.

    :param item: SBML object from which Unit Definition string is to be created
    :return: formatted string for Unit Definition derived from the item
    """

    if item:
        return formula_to_mathml(
            unitDefinitionToString(item.getDerivedUnitDefinition())
        )
    return ""
