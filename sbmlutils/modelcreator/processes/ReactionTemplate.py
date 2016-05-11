"""
ReactionTemplate.
TODO: handle the compartment initialization (comp?)

"""
from __future__ import print_function

import warnings

import libsbml
from sbmlutils.factory import _create_parameter, create_assignment_rules, get_unit_string
from sbmlutils.sbmlio import check
from sbmlutils.equation import Equation
from ..utils.naming import initString


class ReactionTemplate(object):
    """ All reactions are instances of the ReactionTemplate. """
    def __init__(self, rid, equation, formula,
                 pars=[], rules=[], name=None, localization=None, compartments=[]):
        self.rid = rid
        self.key = name
        self.equation = Equation(equation)
        self.localization = localization
        self.compartments = compartments
        self.pars = pars
        self.rules = rules
        self.formula = formula

    def createReactions(self, model, initData):
        """ Create the reaction based on the given comps dictionary """
        # TODO: check if everything is initialized
        # i.e. are all the comp keys in the init dict
        
        # TODO: get the allowed initDicts from the the initData for the given
        # reaction and create this subset of reactions

        # Create the identical replacement
        if not initData:
            initData = [{}]

        for initDict in initData:
            self._createReaction(model, initDict)
    
    def _createParameters(self, initDict):
        """ Parameters have to be initialized. """
        for pdata in self.pars:
            p_new = [initString(part, initDict) for part in pdata]
            pid, value, unit = p_new[0], p_new[1], get_unit_string(p_new[2])
            
            if not self.model.getParameter(pid):
                _create_parameter(self.model, pid, unit, name=None, value=value, constant=True)
    
    def _createRules(self, initDict):
        rules = dict()
        for rule in self.rules:
            r_new = [initString(part, initDict) for part in rule]
            rid = r_new[0]
            if not self.model.getAssignmentRule(rid):
                rules[rid] = {
                    'id': rid,
                    'unit': r_new[2],
                    'value': r_new[1],
                    'name': None
                }
        create_assignment_rules(self.model, rules)

    def _createReaction(self, model, initDict):
        # parameters and rules
        self._createParameters(initDict)
        self._createRules(initDict)
        
        # reaction
        rid = initString(self.rid, initDict)
        r = model.createReaction()
        r.setId(rid)
        r.setName(initString(self.key, initDict))
        r.setCompartment(self.localization)
        r.setReversible(self.equation.reversible)
        r.setFast(False)
    
        #  equation
        for reactant in self.equation.reactants:
            sref = r.createReactant()
            sref.setSpecies(initString(reactant[1], initDict))
            sref.setStoichiometry(reactant[0])
            sref.setConstant(True)
        for product in self.equation.products:
            sref = r.createProduct()
            sref.setSpecies(initString(product[1], initDict))
            sref.setStoichiometry(product[0])
            sref.setConstant(True)
        for modifier in self.equation.modifiers:
            sref = r.createModifier()
            sref.setSpecies(initString(modifier, initDict))        
    
        # kinetics
        formula = initString(self.formula[0], initDict)
        setKineticLaw(model, r, formula) 

        return r


def setKineticLaw(model, reaction, formula):
    """ Sets the kinetic law in reaction based on given formula. """
    law = reaction.createKineticLaw()
    ast_node = libsbml.parseL3FormulaWithModel(formula, model)
    if ast_node is None:
        warnings.warn(libsbml.getLastParseL3Error())
    check(law.setMath(ast_node), 'set math in kinetic law')
    return law
