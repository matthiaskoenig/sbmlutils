# -*- coding=utf-8 -*-
"""
Template filters for rendering SBML.

Additional functionality for templates like displaying
annotations or rendering of units.
"""
from __future__ import print_function

from sbmlutils.formating import *

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
    return AnnotationHTML.annotation_to_html(annotation)


def SBML_notesToString(sbase):
    notes = sbase.getNotesString()
    return notes


def SBML_modelHistoryToString(mhistory):
    return modelHistoryToString(mhistory)


def SBML_reactionToString(reaction):
    return equationStringFromReaction(reaction)


def SBML_formulaChargeString(species):
    return formulaChargeStringFromSpecies(species)


def SBML_unitDefinitionToString1(ud):
    return libsbml.UnitDefinition_printUnits(ud)


def SBML_unitDefinitionToString(udef):
    return unitDefinitionToString(udef)


def SBML_ruleVariableToString(udef):
    return ruleVariableToString(udef)
