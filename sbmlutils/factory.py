"""
Definition of general helper functions to create SBML objects
and setting SBMLObjects in models.
This are the low level helpers to create models from scratch.

The general workflow is to create a list/iterable of SBMLObjects by using the
respective classes in this module, e.g. Compartment, Parameter, Species.
The object are than created in the model by calling
    create_objects(model, objects)
This does NOT take care of the order of the creation.

To create complete models one should use the modelcreator functionality,
which takes care of the order of object creation.

All model objects are created with the given SBML_LEVEL and SBML_VERSION.
"""
from __future__ import print_function, division
from six import iteritems

import logging
import warnings
import libsbml
from libsbml import UNIT_KIND_DIMENSIONLESS, UnitKind_toString

SBML_LEVEL = 3
SBML_VERSION = 1


# TODO: allow setting of sboTerms & metaIds, currently not taken into account


#####################################################################

def create_objects(model, obj_iter, debug=False):
    """ Create the objects in the model.

    This function calls the respective create_sbml function of all objects
    in the order of the objects.

    :param model: SBMLModel instance
    :param obj_iter: iterator of given model object classes like Parameter, ...
    :param debug: print list of created objects
    :return:
    """
    sbml_objects = {}
    for obj in obj_iter:
        if debug:
            print(obj)
        sbml_obj = obj.create_sbml(model)
        sbml_objects[sbml_obj.getId()] = sbml_obj
    return sbml_objects


def ast_node_from_formula(model, formula):
    """ Parses the ASTNode from given formula string with model.

    :param model: SBMLModel instance
    :param formula: formula str
    :return:
    """
    ast_node = libsbml.parseL3FormulaWithModel(formula, model)
    if not ast_node:
        warnings.warn("Formula could not be parsed: '{}'".format(formula))
        warnings.warn(libsbml.getLastParseL3Error())
    return ast_node


def set_main_units(model, main_units):
    """ Sets the main units in model from dictionary.

    Allowed keys are:
        time
        extent
        substance
        length
        area
        volume

    :param model: SBMLModel
    :param main_units: dict of units
    :return:
    """
    for key in ('time', 'extent', 'substance', 'length', 'area', 'volume'):
        if key not in main_units:
            logging.warn('The following key is missing in main_units: {}'.format(key))
            continue
        unit = main_units[key]
        unit = Unit.get_unit_string(unit)
        # set the values
        if key == 'time':
            model.setTimeUnits(unit)
        elif key == 'extent':
            model.setExtentUnits(unit)
        elif key == 'substance':
            model.setSubstanceUnits(unit)
        elif key == 'length':
            model.setLengthUnits(unit)
        elif key == 'area':
            model.setAreaUnits(unit)
        elif key == 'volume':
            model.setVolumeUnits(unit)


#####################################################################
# Base classes
#####################################################################
class Sbase(object):
    def __init__(self, sid, name=None, sboTerm=None, metaId=None):
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId

    def __str__(self):
        tokens = str(self.__class__).split('.')
        class_name = tokens[-1][:-2]
        name = self.name
        if name is None:
            name = ''
        else:
            name = ' ' + name
        return '<{}[{}]{}>'.format(class_name, self.sid, name)


class Value(Sbase):
    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None):
        super(Value, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.value = value


class ValueWithUnit(Value):
    def __init__(self, sid, value, unit="-", name=None, sboTerm=None, metaId=None):
        super(ValueWithUnit, self).__init__(sid=sid, value=value, name=name, sboTerm=sboTerm, metaId=metaId)
        self.unit = unit


#####################################################################
# Creator
#####################################################################
class Creator(object):
    """ Creator in ModelHistory. """

    def __init__(self, familyName, givenName, email, organization, site=None):
        self.familyName = familyName
        self.givenName = givenName
        self.email = email
        self.organization = organization
        self.site = site


##########################################################################
# Units
##########################################################################
class Unit(Sbase):
    def __init__(self, sid, definition, name=None, sboTerm=None, metaId=None):
        super(Unit, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.definition = definition

    def create_sbml(self, model):
        """ Creates the defined unit definitions.

        (kind, exponent, scale, multiplier)

        :param model:
        :return:
        """
        unit_def = model.createUnitDefinition()
        unit_def.setId(self.sid)
        for data in self.definition:
            kind = data[0]
            exponent = data[1]
            scale = 0
            multiplier = 1.0
            if len(data) > 2:
                scale = data[2]
            if len(data) > 3:
                multiplier = data[3]

            Unit._create(unit_def, kind, exponent, scale, multiplier)
        return unit_def

    @staticmethod
    def _create(unit_def, kind, exponent, scale=0, multiplier=1.0):
        """ Create libsbml unit.

        :param unit_def:
        :param kind:
        :param exponent:
        :param scale:
        :param multiplier:
        :return:
        """
        unit = unit_def.createUnit()
        unit.setKind(kind)
        unit.setExponent(exponent)
        unit.setScale(scale)
        unit.setMultiplier(multiplier)
        return unit

    @staticmethod
    def get_unit_string(unit):
        if type(unit) is int:
            unit = UnitKind_toString(unit)
        if unit == '-':
            unit = UnitKind_toString(UNIT_KIND_DIMENSIONLESS)
        return unit


##########################################################################
# Functions
##########################################################################
class Function(Value):
    """ Function. """

    def create_sbml(self, model):
        """ Create function in model.

        :param model:
        :return:
        """
        return Function._create(model,
                                sid=self.sid,
                                formula=self.value,
                                name=self.name)

    @staticmethod
    def _create(model, sid, formula, name):
        """ Create libsbml FunctionDefinition.

        :param model:
        :param sid:
        :param formula:
        :param name:
        :return:
        """
        f = model.createFunctionDefinition()
        f.setId(sid)
        ast_node = ast_node_from_formula(model, formula)
        f.setMath(ast_node)
        if name is not None:
            f.setName(name)
        return f


##########################################################################
# Parameters
##########################################################################
class Parameter(ValueWithUnit):
    """ Parameter. """

    def __init__(self, sid, value=None, unit=None, constant=True, name=None, sboTerm=None, metaId=None):
        super(Parameter, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId)
        self.constant = constant

    def create_sbml(self, model):
        """ Create parameter in model."""
        return Parameter._create(model,
                                 sid=self.sid,
                                 value=self.value,
                                 unit=self.unit,
                                 constant=self.constant,
                                 name=self.name,
                                 sboTerm=self.sboTerm,
                                 metaId=self.metaId)

    @staticmethod
    def _create(model, sid, unit, name, value, constant, sboTerm=None, metaId=None):
        """ Create libsbml Parameter.

        :param model:
        :param sid:
        :param unit:
        :param name:
        :param value:
        :param constant:
        :return:
        """
        p = model.createParameter()
        p.setId(sid)
        if unit is not None:
            p.setUnits(Unit.get_unit_string(unit))
        if name is not None:
            p.setName(name)
        if value is not None:
            p.setValue(value)
        if sboTerm is not None:
            p.setSBOTerm(sboTerm)
        if metaId is not None:
            p.setMetaId(metaId)
        p.setConstant(constant)
        return p


##########################################################################
# Compartments
##########################################################################
class Compartment(ValueWithUnit):
    """ Compartment. """

    def __init__(self, sid, value, unit=None, constant=True, spatialDimension=3, name=None, sboTerm=None, metaId=None):
        super(Compartment, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId)
        self.constant = constant
        self.spatialDimension = spatialDimension

    def create_sbml(self, model):
        """ Create compartment in model.

        :param model: SBMLModel
        :return: SBMLCompartment
        """
        return Compartment._create(model,
                                   sid=self.sid,
                                   name=self.name,
                                   dims=self.spatialDimension,
                                   unit=self.unit,
                                   constant=self.constant,
                                   value=self.value)

    @staticmethod
    def _create(model, sid, name, dims, unit, constant, value):
        """ Create libsbml Compartment.

        :param model:
        :param sid:
        :param name:
        :param dims:
        :param unit:
        :param constant:
        :param value:
        :return:
        """
        c = model.createCompartment()
        c.setId(sid)
        if name is not None:
            c.setName(name)
        c.setSpatialDimensions(dims)
        if unit is not None:
            c.setUnits(Unit.get_unit_string(unit))
        c.setConstant(constant)
        if type(value) is str:
            if constant:
                InitialAssignment._create(model, sid=sid, formula=value)
            else:
                AssignmentRule._create(model, sid=sid, formula=value)
        else:
            c.setSize(value)
        return c


##########################################################################
# Species
##########################################################################
class Species(ValueWithUnit):
    """ Species. """

    def __init__(self, sid, value, compartment, unit=None, constant=False, boundaryCondition=False,
                 hasOnlySubstanceUnits=False, conversionFactor=None, name=None, sboTerm=None, metaId=None):
        super(Species, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId)
        self.compartment = compartment
        self.constant = constant
        self.boundaryCondition = boundaryCondition
        self.hasOnlySubstanceUnits = hasOnlySubstanceUnits
        self.conversionFactor = conversionFactor

    def create_sbml(self, model):
        """ Create species in model.

        :param model: SBMLModel
        :return: SBMLSpecies
        """
        return Species._create(model,
                               sid=self.sid,
                               name=self.name,
                               value=self.value,
                               unit=self.unit,
                               compartment=self.compartment,
                               boundaryCondition=self.boundaryCondition,
                               constant=self.constant,
                               hasOnlySubstanceUnits=self.hasOnlySubstanceUnits,
                               conversionFactor=self.conversionFactor,
                               sboTerm=self.sboTerm,
                               metaId=self.metaId)

    @staticmethod
    def _create(model, sid, name, value, unit, compartment,
                boundaryCondition, constant, hasOnlySubstanceUnits, conversionFactor, sboTerm, metaId):
        """ Create libsbml Species.

        :param model:
        :param sid:
        :param name:
        :param value:
        :param unit:
        :param compartment:
        :param boundaryCondition:
        :param constant:
        :param hasOnlySubstanceUnits:
        :param conversionFactor
        :return:
        """
        s = model.createSpecies()
        s.setId(sid)
        if name:
            s.setName(name)
        if sboTerm is not None:
            s.setSBOTerm(sboTerm)
        if metaId is not None:
            s.setMetaId(metaId)
        if unit:
            s.setUnits(Unit.get_unit_string(unit))
        s.setCompartment(compartment)

        s.setBoundaryCondition(boundaryCondition)
        s.setConstant(constant)
        s.setHasOnlySubstanceUnits(hasOnlySubstanceUnits)

        # TODO: handle the amount/concentrations with corresponding substance units correctly
        if hasOnlySubstanceUnits:
            s.setInitialAmount(value)
        else:
            s.setInitialConcentration(value)
        s.setSubstanceUnits(model.getSubstanceUnits())

        if conversionFactor:
            s.setConversionFactor(conversionFactor)

        return s


##########################################################################
# InitialAssignments
##########################################################################
class InitialAssignment(ValueWithUnit):
    """ InitialAssignments. """

    def create_sbml(self, model):
        """ Create libsbml InitialAssignment.

        Creates a required parameter if not existing.

        :param model:
        :return:
        """
        sid = self.sid
        # Create parameter if not existing
        if (not model.getParameter(sid)) \
                and (not model.getSpecies(sid)) \
                and (not model.getCompartment(sid)):
            Parameter._create(model,
                              sid=sid,
                              unit=self.unit,
                              name=self.name,
                              value=None,
                              constant=True)

        return InitialAssignment._create(model, sid=sid, formula=self.value)

    @staticmethod
    def _create(model, sid, formula):
        """ Create libsbml InitialAssignment.

        :param model:
        :param sid:
        :param formula:
        :return:
        """
        a = model.createInitialAssignment()
        a.setSymbol(sid)
        ast_node = ast_node_from_formula(model, formula)
        a.setMath(ast_node)
        return a


##########################################################################
# Rules
##########################################################################
class Rule(ValueWithUnit):
    @staticmethod
    def _rule_factory(model, rule, rule_type):
        """ Creates libsbml rule of given rule_type.

        :param model:
        :param rule:
        :param rule_type:
        :return:
        """
        assert rule_type in ["AssignmentRule", "RateRule"]
        sid = rule.sid

        # Create parameter if symbol is neither parameter or species, or compartment
        if (not model.getParameter(sid)) \
                and (not model.getSpecies(sid)) \
                and (not model.getCompartment(sid)):
            Parameter._create(model, sid, unit=rule.unit, name=rule.name, value=None, constant=False)

        # Make sure the parameter is const=False
        p = model.getParameter(sid)
        if p is not None:
            p.setConstant(False)
        # Add rule if not existing
        if not model.getRule(sid):
            if rule_type == "RateRule":
                obj = RateRule._create(model, sid=sid, formula=rule.value)
            elif rule_type == "AssignmentRule":
                obj = AssignmentRule._create(model, sid=sid, formula=rule.value)
        else:
            warnings.warn('Rule with sid already exists in model: {}'.format(sid))
        return obj

    @staticmethod
    def _create_rule(model, rule, sid, formula):
        """

        :param rule:
        :param sid:
        :param formula:
        :return:
        """
        rule.setVariable(sid)
        ast_node = ast_node_from_formula(model, formula)
        rule.setMath(ast_node)
        return rule


class AssignmentRule(Rule):
    """ AssignmentRule. """

    def create_sbml(self, model):
        """ Create AssignmentRule in model.

        :param model:
        :return:
        """
        return Rule._rule_factory(model, self, rule_type="AssignmentRule")

    @staticmethod
    def _create(model, sid, formula):
        """ Creates libsbml AssignmentRule.

        :param model:
        :param sid:
        :param formula:
        :return:
        """
        rule = model.createAssignmentRule()
        return Rule._create_rule(model, rule, sid, formula)


class RateRule(Rule):
    """ RateRule. """

    def create_sbml(self, model):
        """ Create RateRule in model.

        :param model:
        :return:
        """
        return Rule._rule_factory(model, self, rule_type="RateRule")

    @staticmethod
    def _create(model, sid, formula):
        """ Create libsbml RateRule.

        :param model:
        :param sid:
        :param formula:
        :return:
        """
        rule = model.createRateRule()
        return Rule._create_rule(model, rule, sid, formula)


##########################################################################
# Reactions
##########################################################################

# TODO: Reaction class

def create_reaction(model, rid, name=None, fast=False, reversible=True, reactants={}, products={}, modifiers=[],
                    formula=None, compartment=None, sboTerm=None):
    """ Create basic reaction structure. """
    r = model.createReaction()
    r.setId(rid)
    if name:
        r.setName(name)
    if sboTerm is not None:
        r.setSBOTerm(sboTerm)
    r.setFast(fast)
    r.setReversible(reversible)

    for sid, stoichiometry in iteritems(reactants):
        rt = r.createReactant()
        rt.setSpecies(sid)
        rt.setStoichiometry(abs(stoichiometry))
        rt.setConstant(True)

    for sid, stoichiometry in iteritems(products):
        rt = r.createProduct()
        rt.setSpecies(sid)
        rt.setStoichiometry(abs(stoichiometry))
        rt.setConstant(True)

    for sid in modifiers:
        rt = r.createModifier()
        rt.setSpecies(sid)

    if formula is not None:
        # set formula in reaction
        ast_node = ast_node_from_formula(model=model, formula=formula)
        law = r.createKineticLaw()
        law.setMath(ast_node)

    if compartment is not None:
        r.setCompartment(compartment)

    return r


##########################################################################
# Events
##########################################################################
# Deficiency Events (Galactosemias)

# TODO: Event class
# TODO: implement more general

def getDeficiencyEventId(deficiency):
    return 'EDEF_{:0>2d}'.format(deficiency)


def createDeficiencyEvent(model, deficiency):
    eid = getDeficiencyEventId(deficiency)
    e = model.createEvent()
    e.setId(eid)
    e.setUseValuesFromTriggerTime(True)
    t = e.createTrigger()
    t.setInitialValue(False)  # ! not supported by Copasi -> lame fix via time
    t.setPersistent(True)  # ! not supported by Copasi -> careful with usage
    formula = '(time>0) && (deficiency=={:d})'.format(deficiency)
    astnode = libsbml.parseL3FormulaWithModel(formula, model)
    t.setMath(astnode)
    return e


def createSimulationEvents(model, elist):
    """ Simulation Events (Peaks & Challenges). """
    for edata in elist:
        createEventFromEventData(model, edata)


def createEventFromEventData(model, edata):
    e = model.createEvent()
    e.setId(edata.eid)
    e.setName(edata.key)
    e.setUseValuesFromTriggerTime(True)
    t = e.createTrigger()
    t.setInitialValue(False)
    t.setPersistent(True)
    astnode = libsbml.parseL3FormulaWithModel(edata.trigger, model)
    t.setMath(astnode)
    # assignments
    for key, value in iteritems(edata.assignments):
        astnode = libsbml.parseL3FormulaWithModel(value, model)
        ea = e.createEventAssignment()
        ea.setVariable(key)
        ea.setMath(astnode)


##########################################################################
# FBC
##########################################################################
# TODO: FluxBound and Objective class

def set_flux_bounds(reaction, lb, ub):
    """ Set flux bounds on given reaction. """
    rplugin = reaction.getPlugin("fbc")
    rplugin.setLowerFluxBound(lb)
    rplugin.setUpperFluxBound(ub)


def create_objective(model_fbc, oid, otype, fluxObjectives, active=True):
    """ Create flux optimization objective.

    :param model_fbc: FbcModelPlugin
    :param oid: objective identifier
    :param otype:
    :param fluxObjectives:
    :param active:
    :return:
    """
    objective = model_fbc.createObjective()
    objective.setId(oid)
    objective.setType(otype)
    if active:
        model_fbc.setActiveObjectiveId(oid)
    for rid, coefficient in iteritems(fluxObjectives):
        fluxObjective = objective.createFluxObjective()
        fluxObjective.setReaction(rid)
        fluxObjective.setCoefficient(coefficient)
    return objective
