"""
Helper functions for formating SBML elements.
"""

import libsbml
import sbmlutils.annotation as annotation


class AnnotationHTML():
    """ Annotation to HTML converter. """

    @classmethod
    def annotation_to_html(cls, item):
        """ Renders HTML representation of given annotation.

        :param item: SBO item
        """
        items = []
        for kcv in xrange(item.getNumCVTerms()):
            cv = item.getCVTerm(kcv)
            q_type = cv.getQualifierType()
            if q_type == 0:
                qualifier = annotation.ModelQualifierType[cv.getModelQualifierType()]
            elif q_type == 1:
                qualifier = annotation.BiologicalQualifierType[cv.getBiologicalQualifierType()]
            items.append(''.join(['<b>', qualifier, '</b>']))

            for k in xrange(cv.getNumResources()):
                uri = cv.getResourceURI(k)
                tokens = uri.split('/')
                resource_id = tokens[-1]
                link = ''.join(['<a href="', uri, '" target="_blank">', resource_id, '</a>'])
                items.append(link)
        res = "<br />".join(items)
        return res


# ------------------------------
# Equations
# ------------------------------

def equationStringFromReaction(reaction, sep_reversible='&#8646;', sep_irreversible='&#10142;'):
    left = _halfEquation(reaction.getListOfReactants())
    right = _halfEquation(reaction.getListOfProducts())
    if reaction.getReversible():
        # sep = '<=>'
        sep = sep_reversible
    else:
        # sep = '=>'
        sep = sep_irreversible
    # mods = modifierEquation(reaction.getListOfModifiers())
    # if mods == None:
    #     return " ".join([left, sep, right])
    # else:
    #     return " ".join([left, sep, right, mods])
    return " ".join([left, sep, right])


def _modifierEquation(modifierList):
    if len(modifierList) == 0:
        return None
    mids = [m.getSpecies() for m in modifierList]
    return '[' + ', '.join(mids) + ']'


def _halfEquation(speciesList):
    items = []
    for sr in speciesList:
        stoichiometry = sr.getStoichiometry()
        species = sr.getSpecies()
        if abs(stoichiometry-1.0)<1E-8:
            sd = '{}'.format(species)
        elif abs(stoichiometry+1.0)<1E-8:
            sd = '-{}'.format(species)
        elif stoichiometry > 0:
            sd = '{} {}'.format(stoichiometry, species)
        elif stoichiometry < 0:
            sd = '-{} {}'.format(stoichiometry, species)
        items.append(sd)
    return ' + '.join(items)


def modelHistoryToString(mhistory):
    """ Renders HTML representation of the model history. """
    if not mhistory:
        return ""
    items = []
    items.append('<b>Creator</b>')
    for kc in xrange(mhistory.getNumCreators()):
        cdata = []
        c = mhistory.getCreator(kc)
        if c.isSetGivenName():
            cdata.append(c.getGivenName())
        if c.isSetFamilyName():
            cdata.append(c.getFamilyName())
        if c.isSetOrganisation():
            cdata.append(c.getOrganisation())
        if c.isSetEmail():
            cdata.append('<a href="mailto:{}" target="_blank">{}</a>'.format(c.getEmail(), c.getEmail()))
        items.append(", ".join(cdata))
    if mhistory.isSetCreatedDate():
        items.append('<b>Created:</b> ' + dateToString(mhistory.getCreatedDate()))
    for km in xrange(mhistory.getNumModifiedDates()):
        items.append('<b>Modified:</b> ' + dateToString(mhistory.getModifiedDate(km)))
    items.append('<br />')
    return "<br />".join(items)


def dateToString(d):
    """ Creates string representation of date. """
    return "{}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}".format(d.getYear(), d.getMonth(), d.getDay(),
        d.getHour(), d.getMinute())



def _isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    """ Calculate the two floats are identical. """
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def ruleVariableToString(rule):
    """ Formating of variable for rule. """
    if isinstance(rule, libsbml.AlgebraicRule):
        return '0'
    elif isinstance(rule, libsbml.AssignmentRule):
        return rule.variable
    elif isinstance(rule, libsbml.RateRule):
        return 'd {}/dt'.format(rule.variable)
    else:
        raise TypeError(rule)


def formulaChargeStringFromSpecies(species):
    """ Get the formula and charge string from species.
    Using the FBC v2.

    :param species:
    :type species:
    :return:
    :rtype:
    """
    sfbc = species.getPlugin("fbc")
    if (sfbc):
        formula = ''
        if sfbc.isSetChemicalFormula():
            formula = sfbc.getChemicalFormula()
        charge = ''
        if sfbc.isSetCharge():
            c = sfbc.getCharge()
            if c is not 0:
                charge = ' ({})'.format(sfbc.getCharge())
        return '{}{}'.format(formula, charge)
    else:
        return ''


# ------------------------------
# UnitDefinitions
# ------------------------------

UNIT_ABBREVIATIONS = {
    'kilogram': 'kg',
    'meter': 'm',
    'metre': 'm',
    'second': 's',
    'dimensionless': '',
    'katal': 'kat',
    'gram': 'g',
}


def unitDefinitionToString(udef):
    """ Formating of units.
    Units have the general format
        (multiplier * 10^scale *ukind)^exponent
        (m * 10^s *k)^e

    """
    if udef == None:
        return 'None'

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
            m_str = ''
        else:
            m_str = str(m) + '*'

        if _isclose(abs(e), 1.0):
            e_str = ''
        else:
            e_str = '^' + str(abs(e))

        if _isclose(s, 0.0):
            string = '{}{}{}'.format(m_str, k_str, e_str)
        else:
            if e_str == '':
                string = '({}10^{})*{}'.format(m_str, s, k_str)
            else:
                string = '(({}10^{})*{}){}'.format(m_str, s, k_str, e_str)

        # collect the terms
        if e >= 0.0:
            nom.append(string)
        else:
            denom.append(string)

    nom_str = ' * '.join(nom)
    denom_str = ' * '.join(denom)
    if (len(nom_str) > 0) and (len(denom_str) > 0):
        return '({})/({})'.format(nom_str, denom_str)
    if (len(nom_str) > 0) and (len(denom_str) == 0):
        return nom_str
    if (len(nom_str) == 0) and (len(denom_str) > 0):
        return '1/({})'.format(denom_str)
    return ''

