# -*- coding=utf-8 -*-
"""
Template filters for rendering SBML.

Additional functionality for templates like displaying
annotations or rendering of units.
"""
from __future__ import print_function, absolute_import, division
from __future__ import unicode_literals
# from future import standard_library
# standard_library.install_aliases()
# from builtins import str
import libsbml

from sbmlutils import formating


filters = [
    'SBML_astnodeToString',
    'SBML_astnodeToMathML',
    'SBML_stringToMathML',
    'SBML_annotationToString',
    'SBML_notesToString',
    'SBML_unitDefinitionToString1',
    'SBML_unitDefinitionToString',
    'SBML_modelHistoryToString',
    'SBML_reactionToString',
    'SBML_formulaChargeString',
    'SBML_ruleVariableToString',
]


def SBML_astnodeToString(astnode):
    return libsbml.formulaToString(astnode)


def SBML_astnodeToMathML(astnode):
    mathml = libsbml.writeMathMLToString(astnode)
    return mathml


def SBML_stringToMathML(string):
    """Parses formula string. """
    astnode = libsbml.parseL3Formula(str(string))
    mathml = libsbml.writeMathMLToString(astnode)
    return mathml


def SBML_annotationToString(annotation):
    return formating.AnnotationHTML.annotation_to_html(annotation)


# noinspection PyCompatibility
def SBML_notesToString(sbase):
    notes = sbase.getNotesString()

    # only decode in python 2, already utf8 str in python 3
    if hasattr(notes, "decode"):
        notes = notes.decode('utf-8')

    return notes


def SBML_modelHistoryToString(mhistory):
    return formating.modelHistoryToString(mhistory)


def SBML_reactionToString(reaction):
    return formating.equationStringFromReaction(reaction)


def SBML_formulaChargeString(species):
    return formating.formulaChargeStringFromSpecies(species)


def SBML_unitDefinitionToString1(ud):
    return libsbml.UnitDefinition_printUnits(ud)


def SBML_unitDefinitionToString(udef):
    return formating.unitDefinitionToString(udef)


def SBML_ruleVariableToString(udef):
    return formating.ruleVariableToString(udef)
