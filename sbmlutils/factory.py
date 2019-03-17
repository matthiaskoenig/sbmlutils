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

import logging
import libsbml
from sbmlutils.validation import check
from sbmlutils.modelcreator.processes.reaction import ReactionTemplate, ExchangeReactionTemplate


SBML_LEVEL = 3  # default SBML level
SBML_VERSION = 1  # default SBML version
PORT_SUFFIX = "_port"
PREFIX_EXCHANGE_REACTION = 'EX_'

__all__ = [
    'Notes',
    'ModelUnits',
    'Creator',
    'Compartment',
    'Unit',
    'Function',
    'Species',
    'Parameter',
    'InitialAssignment',
    'AssignmentRule',
    'RateRule',
    'Event',
    'Constraint',
    'ReactionTemplate',
    'ExchangeReactionTemplate',
]


def create_objects(model, obj_iter, key=None, debug=False):
    """ Create the objects in the model.

    This function calls the respective create_sbml function of all objects
    in the order of the objects.

    :param model: SBMLModel instance
    :param obj_iter: iterator of given model object classes like Parameter, ...
    :param key: object key
    :param debug: print list of created objects
    :return:
    """
    sbml_objects = {}
    try:
        for obj in obj_iter:
            if debug:
                print(obj)
            sbml_obj = obj.create_sbml(model)
            sbml_objects[sbml_obj.getId()] = sbml_obj
    except Exception as error:
        logging.error("Error creation SBML objects <{}>: {}".format(key, obj_iter))
        logging.error(error)

        raise

    return sbml_objects


def ast_node_from_formula(model, formula):
    """ Parses the ASTNode from given formula string with model.

    :param model: SBMLModel instance
    :param formula: formula str
    :return:
    """
    ast_node = libsbml.parseL3FormulaWithModel(formula, model)
    if not ast_node:
        logging.error("Formula could not be parsed: '{}'".format(formula))
        logging.error(libsbml.getLastParseL3Error())
    return ast_node


#####################################################################
# Notes
#####################################################################
class Notes(object):

    def __init__(self, notes):
        tokens = ["<body xmlns='http://www.w3.org/1999/xhtml'>"]
        if isinstance(notes, (dict, list)):
            tokens.extend(notes)
        else:
            tokens.append(notes)

        tokens.append("</body>")
        notes_str = "\n".join(tokens)
        self.xml = libsbml.XMLNode.convertStringToXMLNode(notes_str)
        if self.xml is None:
            raise ValueError("XMLNode could not be generated for:\n{}".format(notes))


def set_notes(model, notes):
    """ Set notes information on model.

    :param model: Model
    :param notes: notes information (xml string)
    :return:
    """
    if not isinstance(notes, Notes):
        logging.error("Using notes strings is deprecated, use 'Notes' instead.")
        notes = Notes(notes)

    check(model.setNotes(notes.xml), message="Setting notes on model")


#####################################################################
# ModelUnits
#####################################################################
class ModelUnits(object):
    def __init__(self, time=None, extent=None, substance=None, length=None, area=None, volume=None):
        self.time = time
        self.extent = extent
        self.substance = substance
        self.length = length
        self.area = area
        self.volume = volume


def set_model_units(model, model_units):
    """ Sets the main units in model from dictionary.

    Allowed keys are:
        time
        extent
        substance
        length
        area
        volume

    :param model: SBMLModel
    :param model_units: dict of units
    :return:
    """
    if isinstance(model_units, dict):
        logging.error("Providing model units as dict is deprecated, use 'ModelUnits' instead.")
        model_units = ModelUnits(**model_units)

    if not model_units:
        logging.error("Model units should be provided for a model, i.e., set 'model_unit' on model.")
    else:
        for key in ('time', 'extent', 'substance', 'length', 'area', 'volume'):
            if getattr(model_units, key) is None:
                logging.error('The following key is missing in model_units: {}'.format(key))
                continue
            unit = getattr(model_units, key)
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
    def __init__(self, sid, name=None, sboTerm=None, metaId=None, port=None):
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.port = port

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

    def create_port(self, model):
        """ Create port if existing. """
        if self.port is None:
            return

        if isinstance(self.port, bool) and self.port is True:
            # manually create port for the id
            cmodel = model.getPlugin("comp")
            p = cmodel.createPort()
            port_sid = '{}{}'.format(self.sid, PORT_SUFFIX)
            p.setId(port_sid)
            p.setName(port_sid)
            p.setMetaId(port_sid)
            p.setSBOTerm(599)  # port
            p.setIdRef(self.sid)

        else:
            # use the port object
            if (not self.port.portRef) and (not self.port.idRef) and (not self.port.unitRef) and (not self.port.metaIdRef):
                # if no reference set id reference to current object
                self.port.idRef = self.sid
            self.port.create_sbml(model)


class Value(Sbase):
    """ Helper class.
    The value field is a helper storage field which is used differently by different
    subclasses.
    """
    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None, port=None):
        super(Value, self).__init__(sid, name=name, sboTerm=sboTerm, metaId=metaId, port=port)
        self.value = value

    def set_fields(self, obj):
        super(Value, self).set_fields(obj)


class ValueWithUnit(Value):
    """ Helper class.
    The value field is a helper storage field which is used differently by different
    subclasses.
    """
    def __init__(self, sid, value, unit="-", name=None, sboTerm=None, metaId=None, port=None):
        super(ValueWithUnit, self).__init__(sid, value, name=name, sboTerm=sboTerm, metaId=metaId, port=port)
        self.unit = unit

    def set_fields(self, obj):
        super(ValueWithUnit, self).set_fields(obj)
        if self.unit is not None:
            obj.setUnits(Unit.get_unit_string(self.unit))


##########################################################################
# Units
##########################################################################
class Unit(Sbase):
    def __init__(self, sid, definition, name=None, sboTerm=None, metaId=None, port=None):
        super(Unit, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId, port=port)
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
        if isinstance(unit, Unit):
            return unit.sid
        elif isinstance(unit, int):
            # libsbml unit
            return libsbml.UnitKind_toString(unit)
        if isinstance(unit, str):
            if unit == '-':
                return libsbml.UnitKind_toString(libsbml.UNIT_KIND_DIMENSIONLESS)
            else:
                return unit
        else:
            return None


##########################################################################
# Functions
##########################################################################
class Function(Sbase):
    """ SBML FunctionDefinitions

    FunctionDefinitions consist of a lambda expression in the value field, e.g.,
        lambda(x,y, piecewise(x,gt(x,y),y) )  #  definition of minimum function
        lambda(x, sin(x) )
    """

    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None, port=None):
        super(Function, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId, port=port)
        self.formula = value

    def create_sbml(self, model):
        f = model.createFunctionDefinition()  # type: libsbml.FunctionDefinition
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

    def __init__(self, sid, value=None, unit=None, constant=True, name=None, sboTerm=None, metaId=None, port=None):
        super(Parameter, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId, port=port)
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

    def __init__(self, sid, value, unit=None, constant=True, spatialDimensions=3, name=None, sboTerm=None, metaId=None,
                 port=None):
        super(Compartment, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId, port=port)
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

        self.create_port(model)
        return c

    def set_fields(self, obj):
        super(Compartment, self).set_fields(obj)
        obj.setConstant(self.constant)
        obj.setSpatialDimensions(self.spatialDimensions)


##########################################################################
# Species
##########################################################################
class Species(Sbase):
    """ Species. """

    def __init__(self, sid, compartment, initialAmount=None, initialConcentration=None, substanceUnit=None, constant=False, boundaryCondition=False,
                 hasOnlySubstanceUnits=False, conversionFactor=None, name=None, sboTerm=None, metaId=None,
                 port=None):
        super(Species, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId, port=port)

        if (initialAmount is None) and (initialConcentration is None):
            raise ValueError("Either initialAmount or initialConcentration required on species: {}".format(sid))
        if initialAmount and initialConcentration:
            raise ValueError("initialAmount and initialConcentration cannot be set on species: {}".format(sid))
        self.substanceUnit = Unit.get_unit_string(substanceUnit)
        self.initialAmount = initialAmount
        self.initialConcentration = initialConcentration
        self.compartment = compartment
        self.constant = constant
        self.boundaryCondition = boundaryCondition
        self.hasOnlySubstanceUnits = hasOnlySubstanceUnits
        self.conversionFactor = conversionFactor

    def create_sbml(self, model):
        s = model.createSpecies()  # type: libsbml.Species
        self.set_fields(s)
        # substance unit must be set on the given substance unit
        s.setSubstanceUnits(model.getSubstanceUnits())
        if self.substanceUnit is not None:
            s.setSubstanceUnits(self.substanceUnit)
        else:
            s.setSubstanceUnits(model.getSubstanceUnits())

        self.create_port(model)
        return s

    def set_fields(self, obj):
        super(Species, self).set_fields(obj)
        obj.setConstant(self.constant)
        if self.compartment is None:
            raise ValueError("Compartment cannot be None on Species: {}".format(self))
        obj.setCompartment(self.compartment)
        obj.setBoundaryCondition(self.boundaryCondition)
        obj.setHasOnlySubstanceUnits(self.hasOnlySubstanceUnits)
        if self.substanceUnit is not None:
            obj.setUnits(Unit.get_unit_string(self.substanceUnit))
        if self.initialAmount is not None:
            obj.setInitialAmount(self.initialAmount)
        if self.initialConcentration is not None:
            obj.setInitialConcentration(self.initialConcentration)
        if self.conversionFactor is not None:
            obj.setConversionFactor(self.conversionFactor)


##########################################################################
# InitialAssignments
##########################################################################
class InitialAssignment(Value):
    """ InitialAssignments.

    The unit attribute is only for the case where a parameter must be created (which has the unit).
    In case of an initialAssignment of a value the units have to be defined in the math.
    """
    def __init__(self, sid, value, unit="-", name=None, sboTerm=None, metaId=None, port=None):
        super(InitialAssignment, self).__init__(sid, value, name=name, sboTerm=sboTerm, metaId=metaId, port=port)
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
            logging.warning('Rule with sid already exists in model: {}. Rule not updated with "{}"'.format(sid, rule.value))
            obj = model.getRule(sid)
        return obj

    def create_sbml(self, model):
        """ Create Rule in model.

        :param model:
        :return:
        """
        logging.error("Rule cannot be created, use either <AssignmentRule> or <RateRule>.")
        raise NotImplementedError

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

    for sid, stoichiometry in reactants.items():
        rt = r.createReactant()
        rt.setSpecies(sid)
        rt.setStoichiometry(abs(stoichiometry))
        rt.setConstant(True)

    for sid, stoichiometry in products.items():
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
# Constraint
##########################################################################
class Constraint(Sbase):
    """ Constraint.

    The Constraint object is a mechanism for stating the assumptions under which a model is designed to operate.
    The constraints are statements about permissible values of different quantities in a model.

    The message must be well formated XHTML, e.g.,
        message='<body xmlns="http://www.w3.org/1999/xhtml">ATP must be non-negative</body>'
    """
    def __init__(self, sid, math, message=None,
                 name=None, sboTerm=None, metaId=None):
        super(Constraint, self).__init__(sid, name=name, sboTerm=sboTerm, metaId=metaId)

        self.math = math
        self.message = message

    def create_sbml(self, model: libsbml.Model):
        """ Create libsbml InitialAssignment.

        Creates a required parameter if not existing.

        :param model:
        :return:
        """
        constraint = model.createConstraint()  # type: libsbml.Constraint
        self.set_fields(constraint, model)
        return constraint

    def set_fields(self, obj: libsbml.Constraint, model: libsbml.Model):
        """ Set fields on given object.

        :param obj: constraint
        :param model: libsbml.Model instance
        :return:
        """
        super(Constraint, self).set_fields(obj)

        if self.math is not None:
            ast_math = libsbml.parseL3FormulaWithModel(self.math, model)
            obj.setMath(ast_math)
        if self.message is not None:
            check(obj.setMessage(self.message), message="Setting message on constraint: '{}'".format(self.message))


##########################################################################
# Events
##########################################################################
class Event(Sbase):
    """ Event.

    Trigger have the format of a logical expression:
        time%200 == 0
    Assignments have the format
        sid = value

    """

    def __init__(self, sid, trigger, assignments={},
                 trigger_persistent=True, trigger_initialValue=False, useValuesFromTriggerTime=True,
                 priority=None, delay=None,
                 name=None, sboTerm=None, metaId=None):
        super(Event, self).__init__(sid, name=name, sboTerm=sboTerm, metaId=metaId)

        self.trigger = trigger

        # assignments
        if type(assignments) is not dict:
            logging.warn("Event assignment must be dict with sid: assignment, but: {}".format(assignments))
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
        """ Set fields on given object.

        :param obj: event
        :param model:
        :return:
        """
        super(Event, self).set_fields(obj)

        obj.setUseValuesFromTriggerTime(True)
        t = obj.createTrigger()
        t.setInitialValue(self.trigger_initialValue)  # False ! not supported by Copasi -> lame fix via time
        t.setPersistent(self.trigger_persistent)  # True ! not supported by Copasi -> careful with usage

        ast_trigger = libsbml.parseL3FormulaWithModel(self.trigger, model)
        t.setMath(ast_trigger)

        if self.priority is not None:
            ast_priority = libsbml.parseL3FormulaWithModel(self.priority, model)
            obj.setPriority(ast_priority)
        if self.delay is not None:
            ast_delay = libsbml.parseL3FormulaWithModel(self.delay, model)
            obj.setDelay(ast_delay)

        for key, math in self.assignments.items():
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

'''
def getDeficiencyEventId(deficiency):
    logging.warn('Will be removed.', DeprecationWarning)
    return 'EDEF_{:0>2d}'.format(deficiency)


def createDeficiencyEvent(model, deficiency):
    logging.warn('Will be removed.', DeprecationWarning)
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
    logging.warn('Will be removed.', DeprecationWarning)
    """ Simulation Events (Peaks & Challenges). """
    for edata in elist:
        createEventFromEventData(model, edata)


def createEventFromEventData(model, edata):
    logging.warn('Will be removed.', DeprecationWarning)
    e = model.createEvent()
    e.setId(edata.eid)
    e.setName(edata.key)
    e.setUseValuesFromTriggerTime(True)
    t = e.createTrigger()
    t.setInitialValue(False)
    t.setPersistent(True)
    astnode = libsbml.parseL3FormulaWithModel(edata.trigger, model)
    t.setMath(astnode)
'''

