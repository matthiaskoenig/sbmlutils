"""
ReactionTemplate.
"""
import logging
from collections import namedtuple
import libsbml

from sbmlutils.validation import check
from sbmlutils.equation import Equation
from sbmlutils.annotation.sbo import SBO_EXCHANGE_REACTION
from sbmlutils.annotation.annotator import ModelAnnotator, Annotation

Formula = namedtuple('Formula', 'value unit')


# FIXME: integrate into factory and reuse existing SBase code

# -----------------------------------------------------------------------------
# Reactions
# -----------------------------------------------------------------------------
class ReactionTemplate(object):
    """ All reactions are instances of the ReactionTemplate. """
    def __init__(self, rid, equation, formula=None, pars=[], rules=[],
                 name=None, compartment=None, fast=False, sboTerm=None,
                 metaId=None, annotations=None,
                 lowerFluxBound=None, upperFluxBound=None):
        self.rid = rid
        self.name = name
        self.metaId = metaId
        self.equation = Equation(equation)
        self.compartment = compartment
        self.pars = pars
        self.rules = rules
        self.formula = formula
        if formula is not None:
            self.formula = Formula(*formula)
        self.fast = fast
        self.sboTerm = sboTerm
        self.annotations = annotations
        self.lowerFluxBound = lowerFluxBound
        self.upperFluxBound = upperFluxBound

    def create_sbml(self, model):
        from sbmlutils.factory import create_objects
        # parameters and rules
        create_objects(model, self.pars, key='parameters')
        create_objects(model, self.rules, key='rules')

        # reaction
        r = model.createReaction()  # type: libsbml.Reaction
        r.setId(self.rid)
        if not libsbml.SyntaxChecker.isValidSBMLSId(self.rid):
            logging.error(
                "The id `{}` is not a valid SBML SId on Reaction. "
                "The SId syntax is defined as: SId ::= ( letter | '_' ) idChar*".format(self.rid)
            )
        if self.metaId:
            r.setMetaId(self.metaId)
        if self.name:
            r.setName(self.name)
        else:
            r.setName(self.rid)
        if self.compartment:
            r.setCompartment(self.compartment)
        if self.sboTerm:
            r.setSBOTerm(self.sboTerm)
        r.setReversible(self.equation.reversible)
        r.setFast(self.fast)

        # equation
        for reactant in self.equation.reactants:  # type: libsbml.SpeciesReference
            sref = r.createReactant()
            sref.setSpecies(reactant.sid)
            sref.setStoichiometry(reactant.stoichiometry)
            sref.setConstant(True)
        for product in self.equation.products:  # type: libsbml.SpeciesReference
            sref = r.createProduct()
            sref.setSpecies(product.sid)
            sref.setStoichiometry(product.stoichiometry)
            sref.setConstant(True)
        for modifier in self.equation.modifiers:
            sref = r.createModifier()
            sref.setSpecies(modifier)

        # kinetics
        if self.formula:
            ReactionTemplate.set_kinetic_law(model, r, self.formula.value)

        # add fbc bounds
        if self.upperFluxBound or self.lowerFluxBound:
            r_fbc = r.getPlugin("fbc")  # type: libsbml.FbcReactionPlugin
            if self.upperFluxBound:
                r_fbc.setUpperFluxBound(self.upperFluxBound)
            if self.lowerFluxBound:
                r_fbc.setLowerFluxBound(self.lowerFluxBound)

        # annotations
        if self.annotations:
            for a_tuple in self.annotations:
                ModelAnnotator.annotate_sbase(
                    sbase=r,
                    annotation=Annotation.from_tuple(a_tuple)
                )

        return r

    @staticmethod
    def set_kinetic_law(model, reaction, formula):
        """ Sets the kinetic law in reaction based on given formula. """
        law = reaction.createKineticLaw()
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            logging.error(libsbml.getLastParseL3Error())
        check(law.setMath(ast_node), 'set math in kinetic law')
        return law


# -----------------------------------------------------------------------------
# ExchangeReactions
# -----------------------------------------------------------------------------
EXCHANGE_REACTION_PREFIX = 'EX_'


class ExchangeReactionTemplate(object):
    """ Exchange reactions define substances which can be exchanged.
     This is important for FBC models.

     EXCHANGE_IMPORT (-INF, 0): is defined as negative flux through the exchange reaction,
        i.e. the upper bound must be 0, the lower bound some negative value,
        e.g. -INF

    EXCHANGE_EXPORT (0, INF): is defined as positive flux through the exchange reaction,
        i.e. the lower bound must be 0, the upper bound some positive value,
        e.g. INF
     """
    def __init__(self, species_id, flux_unit=None,
                 lowerFluxBound=None, upperFluxBound=None):
        self.species_id = species_id
        self.flux_unit = flux_unit
        self.lower_bound = lowerFluxBound
        self.upper_bound = upperFluxBound

    def create_sbml(self, model):

        # id (e.g. EX_A)
        ex_rid = EXCHANGE_REACTION_PREFIX + self.species_id

        rt = ReactionTemplate(
            rid=ex_rid,
            equation="{} ->".format(self.species_id),
            sboTerm=SBO_EXCHANGE_REACTION,
            lowerFluxBound=self.lower_bound,
            upperFluxBound=self.upper_bound
        )
        return rt.create_sbml(model)
