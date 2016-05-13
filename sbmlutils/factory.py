"""
Definition of general helper functions to create the various
objects in the SBML. 
These functions are called with the information dictionaries 
during the generation of cell and tissue model.

The objects send to the create_... functions have to be dictionaries with
certain keys (TODO: better via classes)

"""
# TODO: support SBOTerms & MetaIds via keyword

from __future__ import print_function, division

import warnings
import libsbml
from libsbml import UNIT_KIND_DIMENSIONLESS, UnitKind_toString

SBML_LEVEL = 3
SBML_VERSION = 1

#####################################################################
# Information storage classes
#####################################################################
class Creator(object):
    def __init__(self, familyName, givenName, email, organization, site=None):
        self.familyName = familyName
        self.givenName = givenName
        self.email = email
        self.organization = organization
        self.site = site


class Sbase(object):
    def __init__(self, sid, name=None, sboTerm=None, metaId=None):
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId


class Value(Sbase):
    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None):
        super(Value, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.value = value


class ValueWithUnit(Value):
    def __init__(self, sid, value, unit="-", name=None, sboTerm=None, metaId=None):
        super(ValueWithUnit, self).__init__(sid=sid, value=value, name=name, sboTerm=sboTerm, metaId=metaId)
        self.unit = unit

#####################################################################


def ast_node_from_formula(model, formula):
    ast_node = libsbml.parseL3FormulaWithModel(formula, model)
    if not ast_node:
        warnings.warn("Formula could not be parsed: '{}'".format(formula))
        warnings.warn(libsbml.getLastParseL3Error())
    return ast_node


def create_objects(model, obj_iter):
    """ Create the objects in the model.

    Calls the respective create_sbml function of the object.
    """
    created = {}
    for obj in obj_iter:
        obj.create_sbml(model)
        created[obj.getId()] = obj
    return created

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

            _create_unit(unit_def, kind, exponent, scale, multiplier)
        return unit_def


def _create_unit(unit_def, kind, exponent, scale=0, multiplier=1.0):
    unit = unit_def.createUnit()
    unit.setKind(kind)
    unit.setExponent(exponent)
    unit.setScale(scale)
    unit.setMultiplier(multiplier)
    return unit


def set_main_units(model, main_units):
    """ Sets the main units for the model. """
    for key in ('time', 'extent', 'substance', 'length', 'area', 'volume'):
        unit = main_units[key]
        unit = get_unit_string(unit)
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
    pass

    def create_sbml(self, model):
        obj = _create_function(model,
            sid=self.sid,
            formula=self.value,
            name=self.name)
        return obj


def _create_function(model, sid, formula, name):
    f = model.createFunctionDefinition()
    # f = libsbml.FunctionDefinition()

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
    def __init__(self, sid, value=None, unit=None, constant=True, name=None):
        super(Parameter, self).__init__(sid=sid, value=value, unit=unit, name=name)
        self.constant = constant

    def create_sbml(self, model):
        obj = _create_parameter(model,
                  sid=self.sid,
                  value=self.value,
                  unit=self.unit,
                  constant=p.constant,
                  name =self.name)
        return obj


def _create_parameter(model, sid, unit, name, value, constant):
    p = model.createParameter()
    p.setId(sid)
    if unit is not None:
        p.setUnits(get_unit_string(unit))
    if name is not None:
        p.setName(name)
    if value is not None:
        p.setValue(value)
    p.setConstant(constant)
    return p


##########################################################################
# Compartments
##########################################################################
class Compartment(ValueWithUnit):
    def __init__(self, sid, value, unit, constant, spatialDimension=3, name=None):
        super(Compartment, self).__init__(sid=sid, value=value, unit=unit, name=name)
        self.constant = constant
        self.spatialDimension = spatialDimension


def create_compartments(model, compartments):
    sbml_compartments = {}
    for data in get_values(compartments):
        sid = data[A_ID]
        sbml_compartments[sid] = _create_compartment(model,
            sid=sid,
            name=data.get(A_NAME, None),
            dims=data[A_SPATIAL_DIMENSION],
            unit=data.get(A_UNIT, None),
            constant=data.get(A_CONSTANT, True),
            value=data[A_VALUE])
    return sbml_compartments


def _create_compartment(model, sid, name, dims, unit, constant, value):
    c = model.createCompartment()
    c.setId(sid)
    if name is not None:
        c.setName(name)
    c.setSpatialDimensions(dims)
    if unit is not None:
        c.setUnits(get_unit_string(unit))
    c.setConstant(constant)
    if type(value) is str:
        if constant:
            _create_initial_assignment(model, sid=sid, formula=value)
        else:
            _create_assignment_rule(model, sid=sid, formula=value)
    else:
        c.setSize(value)
    return c


##########################################################################
# Species
##########################################################################

class Species(ValueWithUnit):
    def __init__(self, sid, value, unit, compartment, boundaryCondition, name=None):
        super(Species, self).__init__(sid=sid, value=value, unit=unit, name=name)
        self.compartment = compartment
        self.boundaryCondition = boundaryCondition


def create_species(model, species):
    sbml_species = {}
    for data in get_values(species):
        sid = data[A_ID]
        sbml_species[sid] = _create_specie(model,
                                           sid=data[A_ID],
                                           name=data.get(A_NAME, None),
                                           value=data[A_VALUE],
                                           unit=data.get(A_UNIT, None),
                                           compartment=data[A_COMPARTMENT],
                                           boundaryCondition=data.get(A_BOUNDARY_CONDITION, False),
                                           constant=data.get(A_CONSTANT, False),
                                           hasOnlySubstanceUnits=data.get(A_HAS_ONLY_SUBSTANCE_UNITS, False))
    return sbml_species


def _create_specie(model, sid, name, value, unit, compartment,
                   boundaryCondition, constant, hasOnlySubstanceUnits):
    s = model.createSpecies()
    s.setId(sid)
    if name:
        s.setName(name)
    if unit:
        s.setUnits(get_unit_string(unit))
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

    return s


##########################################################################
# InitialAssignments
##########################################################################
class Assignment(ValueWithUnit):
    pass


def create_initial_assignments(model, assignments):
    sbml_assignments = {}
    for data in get_values(assignments):
        sid = data[A_ID]
        # Create parameter if not existing
        if (not model.getParameter(sid)) and (not model.getSpecies(sid)):
            _create_parameter(model, sid, unit=data.get(A_UNIT, None), name=data.get(A_NAME, None),
                              value=None, constant=True)
        sbml_assignments[sid] = _create_initial_assignment(model, sid=sid, formula=data[A_VALUE])


def _create_initial_assignment(model, sid, formula):
    a = model.createInitialAssignment()
    a.setSymbol(sid)
    ast_node = ast_node_from_formula(model, formula)
    a.setMath(ast_node)
    return a


##########################################################################
# Rules
##########################################################################
class Rule(ValueWithUnit):
    pass


class RateRule(ValueWithUnit):
    pass


def create_assignment_rules(model, rules):
    return _create_rules(model, rules, rule_type="AssignmentRule")


def create_rate_rules(model, rules):
    return _create_rules(model, rules, rule_type="RateRule")


def _create_rules(model, rules, rule_type):
    assert rule_type in ["AssignmentRule", "RateRule"]
    sbml_rules = {}
    for data in get_values(rules):
        check_valid(data, 'rule')
        sid = data[A_ID]
        name = data.get(A_NAME, None)
        # Create parameter if symbol is neither parameter or species, or compartment
        if (not model.getParameter(sid)) and (not model.getSpecies(sid)) and (not model.getCompartment(sid)):
            _create_parameter(model, sid, unit=data.get(A_UNIT, None), name=name, value=None, constant=False)
        # Make sure the parameter is const=False
        p = model.getParameter(sid)
        if p is not None:
            p.setConstant(False)
        # Add rule if not existing
        if not model.getRule(sid):
            if rule_type == "RateRule":
                sbml_rules[sid] = _create_rate_rule(model, sid=sid, formula=data[A_VALUE])
            elif rule_type == "AssignmentRule":
                sbml_rules[sid] = _create_assignment_rule(model, sid=sid, formula=data[A_VALUE])
    return sbml_rules


def _create_rate_rule(model, sid, formula):
    rule = model.createRateRule()
    return _create_rule(model, rule, sid, formula)


def _create_assignment_rule(model, sid, formula):
    rule = model.createAssignmentRule()
    return _create_rule(model, rule, sid, formula)


def _create_rule(model, rule, sid, formula):
    rule.setVariable(sid)
    ast_node = ast_node_from_formula(model, formula)
    rule.setMath(ast_node)
    return rule


##########################################################################
# Reactions
##########################################################################
def create_reaction(model, rid, name, fast=False, reversible=True, reactants={}, products={},
                    formula=None, compartment=None):
    """ Create basic reaction structure. """
    r = model.createReaction()
    r.setId(rid)
    r.setName(name)
    r.setFast(fast)
    r.setReversible(reversible)

    for sid, stoichiometry in reactants.iteritems():
        rt = r.createReactant()
        rt.setSpecies(sid)
        rt.setStoichiometry(abs(stoichiometry))
        rt.setConstant(True)

    for sid, stoichiometry in products.iteritems():
        rt = r.createProduct()
        rt.setSpecies(sid)
        rt.setStoichiometry(abs(stoichiometry))
        rt.setConstant(True)

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
    for key, value in edata.assignments.iteritems():
        astnode = libsbml.parseL3FormulaWithModel(value, model)
        ea = e.createEventAssignment()
        ea.setVariable(key)
        ea.setMath(astnode)


##########################################################################
# FBC
##########################################################################

def set_flux_bounds(reaction, lb, ub):
    """ Set flux bounds on given reaction. """
    rplugin = reaction.getPlugin("fbc")
    rplugin.setLowerFluxBound(lb)
    rplugin.setUpperFluxBound(ub)


def create_objective(mplugin, oid, otype, fluxObjectives, active=True):
    objective = mplugin.createObjective()
    objective.setId(oid)
    objective.setType(otype)
    if active:
        mplugin.setActiveObjectiveId("R3_maximize")
    for rid, coefficient in fluxObjectives.iteritems():
        fluxObjective = objective.createFluxObjective()
        fluxObjective.setReaction(rid)
        fluxObjective.setCoefficient(coefficient)
    return objective