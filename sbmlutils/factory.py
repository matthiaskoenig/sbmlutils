"""
This module provides definitions of helper functions for the creation of
SBML objects. These are the low level helpers to create models from scratch
and are used in the higher level SBML factories.

The general workflow to create new SBML models isto create a lists/iterables of
SBMLObjects by using the respective classes in this module,
e.g. Compartment, Parameter, Species.

The actual SBase objects are than created in the SBMLDocument/Model by calling
    create_objects(model, objects)
These functions DO NOT take care of the order of the creation, but the order
must be correct in the model definition files.
To create complete models one should use the modelcreator functionality,
which takes care of the order of object creation.
"""

from __future__ import print_function, division
from six import iteritems

import logging
import warnings
import libsbml

from libsbml import UNIT_KIND_DIMENSIONLESS, UnitKind_toString
from sbmlutils.validation import check

SBML_LEVEL = 3  # default SBML level
SBML_VERSION = 1  # default SBML version


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

def set_notes(model, notes):
    """ Set notes information on model.

    :param model: Model
    :param notes: notes information (xml string)
    :return:
    """
    xml_node = libsbml.XMLNode.convertStringToXMLNode(notes)
    if xml_node is None:
        raise ValueError("XMLNode could not be generated for:\n{}".format(notes))
    check(model.setNotes(xml_node),
          message="Setting notes on model")

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

    def set_fields(self, obj):
        obj.setId(self.sid)
        if self.name is not None:
            obj.setName(self.name)
        if self.sboTerm is not None:
            obj.setSBOTerm(self.sboTerm)
        if self.metaId is not None:
            obj.setMetaId(self.metaId)


class Value(Sbase):
    """ Helper class.
    The value field is a helper storage field which is used differently by different
    subclasses.
    """
    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None):
        super(Value, self).__init__(sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.value = value

    def set_fields(self, obj):
        super(Value, self).set_fields(obj)


class ValueWithUnit(Value):
    """ Helper class.
    The value field is a helper storage field which is used differently by different
    subclasses.
    """
    def __init__(self, sid, value, unit="-", name=None, sboTerm=None, metaId=None):
        super(ValueWithUnit, self).__init__(sid, value, name=name, sboTerm=sboTerm, metaId=metaId)
        self.unit = unit

    def set_fields(self, obj):
        super(ValueWithUnit, self).set_fields(obj)
        if self.unit is not None:
            obj.setUnits(Unit.get_unit_string(self.unit))


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

        self.set_fields(unit_def)
        return unit_def

    def set_fields(self, obj):
        super(Unit, self).set_fields(obj)

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
class Function(Sbase):

    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None):
        super(Function, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.formula = value

    def create_sbml(self, model):
        f = model.createFunctionDefinition()
        self.set_fields(f, model)
        return f

    def set_fields(self, obj, model):
        super(Function, self).set_fields(obj)
        ast_node = ast_node_from_formula(model, self.formula)
        obj.setMath(ast_node)


##########################################################################
# Parameters
##########################################################################
class Parameter(ValueWithUnit):

    def __init__(self, sid, value=None, unit=None, constant=True, name=None, sboTerm=None, metaId=None):
        super(Parameter, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId)
        self.constant = constant

    def create_sbml(self, model):
        p = model.createParameter()
        self.set_fields(p)
        return p

    def set_fields(self, obj):
        super(Parameter, self).set_fields(obj)
        obj.setConstant(self.constant)
        if self.value is not None:
            obj.setValue(self.value)


##########################################################################
# Compartments
##########################################################################
class Compartment(ValueWithUnit):

    def __init__(self, sid, value, unit=None, constant=True, spatialDimensions=3, name=None, sboTerm=None, metaId=None):
        super(Compartment, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId)
        self.constant = constant
        self.spatialDimensions = spatialDimensions

    def create_sbml(self, model):
        c = model.createCompartment()
        self.set_fields(c)

        if type(self.value) is str:
            if self.constant:
                # InitialAssignment._create(model, sid=self.sid, formula=self.value)
                InitialAssignment(self.sid, self.value).create_sbml(model)
            else:
                AssignmentRule(self.sid, self.value).create_sbml(model)
                # AssignmentRule._create(model, sid=self.sid, formula=self.value)
        else:
            c.setSize(self.value)
        return c

    def set_fields(self, obj):
        super(Compartment, self).set_fields(obj)
        obj.setConstant(self.constant)
        obj.setSpatialDimensions(self.spatialDimensions)


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
        s = model.createSpecies()
        self.set_fields(s)
        s.setSubstanceUnits(model.getSubstanceUnits())
        return s

    def set_fields(self, obj):
        super(Species, self).set_fields(obj)
        obj.setConstant(self.constant)
        obj.setCompartment(self.compartment)
        obj.setBoundaryCondition(self.boundaryCondition)
        obj.setHasOnlySubstanceUnits(self.hasOnlySubstanceUnits)

        # TODO: handle the amount/concentrations with corresponding substance units correctly
        if self.hasOnlySubstanceUnits:
            obj.setInitialAmount(self.value)
        else:
            obj.setInitialConcentration(self.value)

        if self.conversionFactor:
            obj.setConversionFactor(self.conversionFactor)


##########################################################################
# InitialAssignments
##########################################################################
class InitialAssignment(Value):
    """ InitialAssignments. """

    def __init__(self, sid, value, unit="-", name=None, sboTerm=None, metaId=None):
        super(InitialAssignment, self).__init__(sid, value, name=name, sboTerm=sboTerm, metaId=metaId)
        self.unit = unit

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
            Parameter(sid=sid, value=None, unit=self.unit, constant=True, name=self.name).create_sbml(model)

        a = model.createInitialAssignment()
        self.set_fields(a)
        a.setSymbol(sid)
        ast_node = ast_node_from_formula(model, self.value)
        a.setMath(ast_node)
        return a


##########################################################################
# Rules
##########################################################################
class Rule(ValueWithUnit):
    @staticmethod
    def _rule_factory(model, rule, rule_type, value=None):
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

            # Parameter._create(model, sid, unit=rule.unit, name=rule.name, value=None, constant=False)
            Parameter(sid, unit=rule.unit, name=rule.name, value=value, constant=False).create_sbml(model)

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
            warnings.warn('Rule with sid already exists in model: {}. Rule not updated with "{}"'.format(sid, rule.value))
            obj = model.getRule(sid)
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
        rule = Rule._rule_factory(model, self, rule_type="AssignmentRule")
        self.set_fields(rule)
        return rule

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
        rule = Rule._rule_factory(model, self, rule_type="RateRule")
        self.set_fields(rule)
        return rule

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
class Event(Sbase):
    """ InitialAssignments. """

    def __init__(self, sid, trigger, assignments={},
                 trigger_persistent=True, trigger_initialValue=False, useValuesFromTriggerTime=True,
                 priority=None, delay=None,
                 name=None, sboTerm=None, metaId=None):
        super(Event, self).__init__(sid, name=name, sboTerm=sboTerm, metaId=metaId)

        self.trigger = trigger

        # assignments
        if type(assignments) is not dict:
            warnings.warn("Event assignment must be dict with sid: assignment, but: {}".format(assignments))
        self.assignments = assignments

        self.trigger_persistent = trigger_persistent
        self.trigger_initialValue = trigger_initialValue
        self.useValuesFromTriggerTime = useValuesFromTriggerTime

        self.priority = priority
        self.delay = delay

    def create_sbml(self, model):
        """ Create libsbml InitialAssignment.

        Creates a required parameter if not existing.

        :param model:
        :return:
        """
        event = model.createEvent()
        self.set_fields(event, model)

        return event

    def set_fields(self, obj, model):
        super(Event, self).set_fields(obj)

        obj.setUseValuesFromTriggerTime(True)
        t = obj.createTrigger()
        t.setInitialValue(self.trigger_initialValue)  # False ! not supported by Copasi -> lame fix via time
        t.setPersistent(self.trigger_persistent)  # True ! not supported by Copasi -> careful with usage

        ast_trigger = libsbml.parseL3FormulaWithModel(self.trigger, model)
        t.setMath(ast_trigger)

        if self.priority is not None:
            ast_priority = libsbml.parseL3FormulaWithModel(self.priority, model)
            event.setPriority(ast_priority)
        if self.delay is not None:
            ast_delay = libsbml.parseL3FormulaWithModel(self.delay, model)
            event.setDelay(ast_delay)

        for key, math in iteritems(self.assignments):
            ast_assign = libsbml.parseL3FormulaWithModel(str(math), model)
            ea = obj.createEventAssignment()
            ea.setVariable(key)
            ea.setMath(ast_assign)

    @staticmethod
    def _trigger_from_time(t):
        return '(time >= {})'.format(t)

    @staticmethod
    def _assignments_dict(species, values):
        return dict(zip(species, values))


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
