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

# attribute ids
A_ID = 'id'
A_NAME = 'name'
A_UNIT = 'unit'
A_VALUE = 'value'
A_CONSTANT = 'constant'
A_SPATIAL_DIMENSION = 'spatialDimension'
A_COMPARTMENT = 'compartment'
A_BOUNDARY_CONDITION = 'boundaryCondition'
A_HAS_ONLY_SUBSTANCE_UNITS = 'hasOnlySubstanceUnits'


def get_values(data_struct):
    if isinstance(data_struct, dict):
        values = data_struct.values()
    elif isinstance(data_struct, list):
        values = data_struct
    else:
        raise Exception("data_struct type not supported.")
    return values


def check_valid(data, dtype):
    """
    Check if the information for a certain data type is valid.
    """
    # TODO: implement checks based on the keys
    if dtype is 'rule':
        assert(data.has_key(A_ID))


def ast_node_from_formula(model, formula):
    ast_node = libsbml.parseL3FormulaWithModel(formula, model)
    if not ast_node:
        warnings.warn('Formula could not be parsed:', formula)
        warnings.warn(libsbml.getLastParseL3Error())
    return ast_node


##########################################################################
# Units
##########################################################################
def create_unit_definitions(model, definitions):
    for sid, units in definitions.iteritems():
        _create_unit_definition(model, sid, units)


def _create_unit_definition(model, sid, units):
    """ Creates the defined unit definitions.
    (kind, exponent, scale, multiplier)
    """
    unit_def = model.createUnitDefinition()
    unit_def.setId(sid)
    for data in units:
        kind = data[0]
        exponent = data[1]
        scale = 0
        multiplier = 1.0
        if len(data) > 2:
            scale = data[2]
        if len(data) > 3:
            multiplier = data[3]

        _create_unit(unit_def, kind, exponent, scale, multiplier)


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
def create_functions(model, functions):
    sbml_functions = {}
    for data in get_values(functions):
        sid = data[A_ID]
        sbml_functions[sid] = _create_function(model,
            sid=sid,
            formula=data[A_VALUE],
            name=data.get(A_NAME, None))
    return sbml_functions


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
def create_parameters(model, parameters):
    sbml_parameters = {}
    for data in get_values(parameters):
        sid = data[A_ID]
        sbml_parameters[sid] = _create_parameter(model,
            sid=sid,
            unit=data.get(A_UNIT, None),
            name=data.get(A_NAME, None),
            value=data.get(A_VALUE, None),
            constant=data.get(A_CONSTANT, True))
    return sbml_parameters


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