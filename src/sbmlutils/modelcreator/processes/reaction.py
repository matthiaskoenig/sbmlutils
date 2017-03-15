"""
ReactionTemplate.
"""
from __future__ import print_function

import warnings
from collections import namedtuple

import libsbml
from sbmlutils.validation import check
from sbmlutils.equation import Equation

Formula = namedtuple('Formula', 'value unit')


class ReactionTemplate(object):
    """ All reactions are instances of the ReactionTemplate. """
    def __init__(self, rid, equation, formula, pars=[], rules=[],
                 name=None, compartment=None, fast=False):
        self.rid = rid
        self.name = name
        self.equation = Equation(equation)
        self.compartment = compartment
        self.pars = pars
        self.rules = rules
        self.formula = Formula(*formula)
        self.fast = fast

    def create_sbml(self, model):
        from sbmlutils.factory import create_objects
        # parameters and rules
        create_objects(model, self.pars)
        create_objects(model, self.rules)

        # reaction
        r = model.createReaction()
        r.setId(self.rid)
        if self.name:
            r.setName(self.name)
        else:
            r.setName(self.rid)
        if self.compartment:
            r.setCompartment(self.compartment)
        r.setReversible(self.equation.reversible)
        r.setFast(self.fast)

        #  equation
        for reactant in self.equation.reactants:
            sref = r.createReactant()
            sref.setSpecies(reactant.sid)
            sref.setStoichiometry(reactant.stoichiometry)
            sref.setConstant(True)
        for product in self.equation.products:
            sref = r.createProduct()
            sref.setSpecies(product.sid)
            sref.setStoichiometry(product.stoichiometry)
            sref.setConstant(True)
        for modifier in self.equation.modifiers:
            sref = r.createModifier()
            sref.setSpecies(modifier)

        # kinetics
        ReactionTemplate.set_kinetic_law(model, r, self.formula.value)
        return r

    @staticmethod
    def set_kinetic_law(model, reaction, formula):
        """ Sets the kinetic law in reaction based on given formula. """
        law = reaction.createKineticLaw()
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            warnings.warn(libsbml.getLastParseL3Error())
        check(law.setMath(ast_node), 'set math in kinetic law')
        return law
