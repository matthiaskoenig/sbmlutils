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
from sbmlutils.annotation.annotator import ModelAnnotator, Annotation
from sbmlutils.annotation.sbo import SBO_EXCHANGE_REACTION
from collections import namedtuple
from sbmlutils.equation import Equation


SBML_LEVEL = 3  # default SBML level
SBML_VERSION = 1  # default SBML version
PORT_SUFFIX = "_port"
PREFIX_EXCHANGE_REACTION = 'EX_'

PACKAGE_COMP = "comp"
PACKAGE_FBC = "fbc"
PACKAGE_DISTRIB = "distrib"
PACKAGE_LAYOUT = "layout"

ALLOWED_PACKAGES = {
    PACKAGE_COMP,
    PACKAGE_FBC,
    PACKAGE_DISTRIB,
    PACKAGE_LAYOUT,
}

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
    'Reaction',
    'ExchangeReaction',
    'Uncertainty',
    'UncertParameter',
    'UncertSpan',
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
        logging.error("Model units should be provided for a model, i.e., set the 'model_units' "
                      "field on model.")
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


# -----------------------------------------------------------------------------
# Base classes
# -----------------------------------------------------------------------------
class Sbase(object):
    def __init__(self, sid=None, name=None, sboTerm=None, metaId=None,
                 annotations=None,
                 port=None, uncertainties=None):
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.annotations = annotations
        self.port = port
        self.uncertainties = uncertainties

    def __str__(self):
        tokens = str(self.__class__).split('.')
        class_name = tokens[-1][:-2]
        name = self.name
        if name is None:
            name = ''
        else:
            name = ' ' + name
        return '<{}[{}]{}>'.format(class_name, self.sid, name)

    def set_fields(self, obj: libsbml.SBase):
        if self.sid is not None:
            if not libsbml.SyntaxChecker.isValidSBMLSId(self.sid):
                logging.error(
                    "The id `{self.sid}` is not a valid SBML SId on `{obj}`. "
                    "The SId syntax is defined as:"
                    "\tletter ::= 'a'..'z','A'..'Z'"
                    "\tdigit  ::= '0'..'9'"
                    "\tidChar ::= letter | digit | '_'"
                    "\tSId    ::= ( letter | '_' ) idChar*"
                )
            obj.setId(self.sid)
        if self.name is not None:
            obj.setName(self.name)
        if self.sboTerm is not None:
            obj.setSBOTerm(self.sboTerm)
        if self.metaId is not None:
            obj.setMetaId(self.metaId)

        if self.annotations:
            for a_tuple in self.annotations:
                ModelAnnotator.annotate_sbase(
                    sbase=obj,
                    annotation=Annotation.from_tuple(a_tuple)
                )

        self.create_uncertainties(obj)

    def create_port(self, model):
        """ Create port if existing. """
        if self.port is None:
            return

        if isinstance(self.port, bool):
            if self.port is True:
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
                pass

        else:
            # use the port object
            if (not self.port.portRef) and (not self.port.idRef) and (not self.port.unitRef) and (not self.port.metaIdRef):
                # if no reference set id reference to current object
                self.port.idRef = self.sid
            self.port.create_sbml(model)

    def create_uncertainties(self, obj):
        if not self.uncertainties:
            return

        for uncertainty in self.uncertainties:  # type: Uncertainty
            uncertainty.create_sbml(obj)


class Value(Sbase):
    """ Helper class.
    The value field is a helper storage field which is used differently by different
    subclasses.
    """
    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None,
                 annotations=None,
                 port=None, uncertainties=None):
        super(Value, self).__init__(sid, name=name, sboTerm=sboTerm, metaId=metaId,
                                    annotations=annotations,
                                    port=port, uncertainties=uncertainties)
        self.value = value

    def set_fields(self, obj):
        super(Value, self).set_fields(obj)


class ValueWithUnit(Value):
    """ Helper class.
    The value field is a helper storage field which is used differently by different
    subclasses.
    """
    def __init__(self, sid, value, unit="-",
                 name=None, sboTerm=None, metaId=None, annotations=None,
                 port=None, uncertainties=None):
        super(ValueWithUnit, self).__init__(sid, value, name=name, sboTerm=sboTerm, metaId=metaId,
                                            port=port, annotations=annotations, uncertainties=uncertainties)
        self.unit = unit

    def set_fields(self, obj):
        super(ValueWithUnit, self).set_fields(obj)
        if self.unit is not None:
            obj.setUnits(Unit.get_unit_string(self.unit))


##########################################################################
# Units
##########################################################################
class Unit(Sbase):
    def __init__(self, sid, definition, name=None, sboTerm=None, metaId=None,
                 port=None, uncertainties=None):
        super(Unit, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId,
                                   port=port, uncertainties=uncertainties)
        self.definition = definition

    def create_sbml(self, model):
        """ Creates the defined unit definitions.

        (kind, exponent, scale, multiplier)

        :param model:
        :return:
        """
        obj = model.createUnitDefinition()  # type: libsbml.UnitDefinition

        for data in self.definition:
            kind = data[0]
            exponent = data[1]
            scale = 0
            multiplier = 1.0
            if len(data) > 2:
                scale = data[2]
            if len(data) > 3:
                multiplier = data[3]

            Unit._create(obj, kind, exponent, scale, multiplier)

        self.set_fields(obj)
        self.create_port(model)
        self.create_uncertainties(obj)
        return obj

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

    def __init__(self, sid, value, name=None, sboTerm=None, metaId=None,
                 port=None, uncertainties=None):
        super(Function, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId,
                                       port=port, uncertainties=uncertainties)
        self.formula = value

    def create_sbml(self, model):
        obj = model.createFunctionDefinition()  # type: libsbml.FunctionDefinition
        self.set_fields(obj, model)

        self.create_port(model)
        self.create_uncertainties(obj)
        return obj

    def set_fields(self, obj, model):
        super(Function, self).set_fields(obj)
        ast_node = ast_node_from_formula(model, self.formula)
        obj.setMath(ast_node)


##########################################################################
# Parameters
##########################################################################
class Parameter(ValueWithUnit):

    def __init__(self, sid, value=None, unit=None, constant=True,
                 name=None, sboTerm=None, metaId=None,
                 port=None, uncertainties=None):
        super(Parameter, self).__init__(sid=sid, value=value, unit=unit, name=name,
                                        sboTerm=sboTerm, metaId=metaId,
                                        port=port, uncertainties=uncertainties)
        self.constant = constant

    def create_sbml(self, model):
        obj = model.createParameter()  # type: libsbml.Parameter
        self.set_fields(obj)

        self.create_port(model)
        self.create_uncertainties(obj)
        return obj

    def set_fields(self, obj):
        super(Parameter, self).set_fields(obj)
        obj.setConstant(self.constant)
        if self.value is not None:
            obj.setValue(self.value)


##########################################################################
# Compartments
##########################################################################
class Compartment(ValueWithUnit):

    def __init__(self, sid, value, unit=None, constant=True,
                 spatialDimensions=3, name=None,
                 sboTerm=None, metaId=None, annotations=None,
                 port=None, uncertainties=None):
        super(Compartment, self).__init__(sid=sid, value=value, unit=unit, name=name, sboTerm=sboTerm, metaId=metaId,
                                          annotations=annotations, port=port, uncertainties=uncertainties)
        self.constant = constant
        self.spatialDimensions = spatialDimensions

    def create_sbml(self, model):
        obj = model.createCompartment()  # type: libsbml.Compartment
        self.set_fields(obj)

        if type(self.value) is str:
            if self.constant:
                # InitialAssignment._create(model, sid=self.sid, formula=self.value)
                InitialAssignment(self.sid, self.value).create_sbml(model)
            else:
                AssignmentRule(self.sid, self.value).create_sbml(model)
                # AssignmentRule._create(model, sid=self.sid, formula=self.value)
        else:
            obj.setSize(self.value)

        self.create_port(model)
        self.create_uncertainties(obj)
        return obj

    def set_fields(self, obj):
        super(Compartment, self).set_fields(obj)
        obj.setConstant(self.constant)
        obj.setSpatialDimensions(self.spatialDimensions)


##########################################################################
# Species
##########################################################################
class Species(Sbase):
    """ Species. """

    def __init__(self, sid, compartment, initialAmount=None, initialConcentration=None,
                 substanceUnit=None, hasOnlySubstanceUnits=False,
                 constant=False, boundaryCondition=False,
                 charge=None, chemicalFormula=None,
                 conversionFactor=None,
                 name=None, sboTerm=None, metaId=None, annotations=None,
                 port=None, uncertainties=None):
        super(Species, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId,
                                      annotations=annotations,
                                      port=port, uncertainties=uncertainties)

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
        self.charge = charge
        self.chemicalFormula = chemicalFormula
        self.conversionFactor = conversionFactor

    def create_sbml(self, model):
        obj = model.createSpecies()  # type: libsbml.Species
        self.set_fields(obj)
        # substance unit must be set on the given substance unit
        obj.setSubstanceUnits(model.getSubstanceUnits())
        if self.substanceUnit is not None:
            obj.setSubstanceUnits(self.substanceUnit)
        else:
            obj.setSubstanceUnits(model.getSubstanceUnits())

        self.create_port(model)
        self.create_uncertainties(obj)
        return obj

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

        # fbc
        if (self.charge is not None) or (self.chemicalFormula is not None):
            obj_fbc = obj.getPlugin("fbc")  # type: libsbml.FbcSpeciesPlugin
            if obj_fbc is None:
                logging.error("FBC SPlugin not found for species, "
                              "no fbc: {}".format(obj))
            else:
                if self.charge is not None:
                    obj_fbc.setCharge(int(self.charge))
                if self.chemicalFormula is not None:
                    obj_fbc.setChemicalFormula(self.chemicalFormula)


##########################################################################
# InitialAssignments
##########################################################################
class InitialAssignment(Value):
    """ InitialAssignments.

    The unit attribute is only for the case where a parameter must be created (which has the unit).
    In case of an initialAssignment of a value the units have to be defined in the math.
    """
    def __init__(self, sid, value, unit="-", name=None, sboTerm=None, metaId=None,
                 annotations=None,
                 port=None, uncertainties=None):
        super(InitialAssignment, self).__init__(sid, value, name=name, sboTerm=sboTerm, metaId=metaId,
                                                annotations=annotations,
                                                port=port, uncertainties=uncertainties)
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

        obj = model.createInitialAssignment()  # type: libsbml.InitialAssignment
        self.set_fields(obj)
        obj.setSymbol(sid)
        ast_node = ast_node_from_formula(model, self.value)
        obj.setMath(ast_node)

        self.create_port(model)
        self.create_uncertainties(obj)
        return obj


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
        obj = Rule._rule_factory(model, self, rule_type="AssignmentRule")  # type: libsbml.AssignmentRule
        self.set_fields(obj)
        self.create_port(model)
        self.create_uncertainties(obj)
        return obj

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
        obj = Rule._rule_factory(model, self, rule_type="RateRule")
        self.set_fields(obj)
        self.create_port(model)
        self.create_uncertainties(obj)
        return obj

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
# Uncertainty
##########################################################################
class UncertParameter(object):
    """UncertParameter
    """
    def __init__(self, type, value=None, var=None, unit=None):
        if (value is None) and (var is None):
            raise ValueError("Either 'value' or 'var' have to be set in UncertParameter.")
        self.type = type
        self.value = value
        self.var = var
        self.unit = unit


class UncertSpan(object):
    def __init__(self, type, valueLower=None, varLower=None, valueUpper=None, varUpper=None, unit=None):
        if (valueLower is None) and (varLower is None):
            raise ValueError("Either 'valueLower' or 'varLower' have to be set in UncertSpan.")
        if (valueUpper is None) and (varUpper is None):
            raise ValueError("Either 'valueLower' or 'varLower' have to be set in UncertSpan.")

        self.type = type
        self.valueLower = valueLower
        self.varLower = varLower
        self.valueUpper = valueUpper
        self.varUpper = varUpper
        self.unit = unit


class Uncertainty(Sbase):
    """ Uncertainty.

    Uncertainty information for Sbase.
    """
    def __init__(self, sid=None, formula=None, uncertParameters=[],
                 name=None, sboTerm=None, metaId=None,
                 annotations=None,
                 port=None):
        super(Uncertainty, self).__init__(sid, name=name, sboTerm=sboTerm, metaId=metaId,
                                          annotations=annotations, port=port)

        # Object on which the uncertainty is written
        self.formula = formula
        self.uncertParameters = uncertParameters

    def create_sbml(self, sbase):
        """ Create libsbml Uncertainty.

        :param model:
        :return:
        """
        sbase_distrib = sbase.getPlugin("distrib")  # type: libsbml.DistribSBasePlugin
        uncertainty = sbase_distrib.createUncertainty()  # type: libsbml.Uncertainty

        for uncertParameter in self.uncertParameters:
            up = None
            if uncertParameter.type in [
                libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
                libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
                libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
                libsbml.DISTRIB_UNCERTTYPE_RANGE,
            ]:

                up = uncertainty.createUncertSpan()  # type: libsbml.UncertSpan
                up.setType(uncertParameter.type)
                if uncertParameter.valueLower is not None:
                    up.setValueLower(uncertParameter.valueLower)
                if uncertParameter.valueUpper is not None:
                    up.setValueUpper(uncertParameter.valueUpper)
                if uncertParameter.varLower is not None:
                    up.setVarLower(uncertParameter.varLower)
                if uncertParameter.varUpper is not None:
                    up.setValueLower(uncertParameter.varUpper)

            elif uncertParameter.type in [
                libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION,
                libsbml.DISTRIB_UNCERTTYPE_KURTOSIS,
                libsbml.DISTRIB_UNCERTTYPE_MEAN,
                libsbml.DISTRIB_UNCERTTYPE_MEDIAN,
                libsbml.DISTRIB_UNCERTTYPE_MODE,
                libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE,
                libsbml.DISTRIB_UNCERTTYPE_SKEWNESS,
                libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR,
                libsbml.DISTRIB_UNCERTTYPE_VARIANCE,
            ]:
                up = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
                up.setType(uncertParameter.type)
                if uncertParameter.value is not None:
                    up.setValue(uncertParameter.value)
                if uncertParameter.var is not None:
                    up.setValue(uncertParameter.var)
            else:
                logging.error("Unsupported UncertParameter or UncertSpan type: %s", uncertParameter.type)

            if up and uncertParameter.unit:
                up.setUnits(Unit.get_unit_string(self.unit))

        # create a distribution uncertainty
        if self.formula:
            model = sbase.getModel()
            up = uncertainty.createUncertParameter()  # type: libsbml.UncertParameter
            up.setType(libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)
            for key in ["normal", "uniform", "bernoulli",
                        "binomial", "cauchy", "chisquare",
                        "exponential", "gamma", "laplace",
                        "lognormal", "poisson", "raleigh"
                        ]:
                if key in self.formula:
                    up.setDefinitionURL("http://www.sbml.org/sbml/symbols/distrib/{}".format(key))
                    ast = libsbml.parseL3FormulaWithModel(self.formula, model)
                    if not ast:
                        logging.error("Formula could not be parsed in uncertainty: {}".format(self.formula))
                        up.setMath(ast)

        return uncertainty


##########################################################################
# Reactions
##########################################################################
Formula = namedtuple('Formula', 'value unit')


class Reaction(Sbase):
    """ Reaction class."""
    def __init__(self, sid, equation, formula=None, pars=[], rules=[],
                 name=None, compartment=None, fast=False, reversible=None,
                 sboTerm=None, metaId=None, annotations=None,
                 lowerFluxBound=None, upperFluxBound=None, uncertainties=None, port=None):
        super(Reaction, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId,
                                       port=port, uncertainties=uncertainties)

        self.equation = Equation(equation)
        self.compartment = compartment
        self.reversible = reversible
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

    def create_sbml(self, model: libsbml.Model):

        # parameters and rules
        create_objects(model, self.pars, key='parameters')
        create_objects(model, self.rules, key='rules')

        # reaction
        r = model.createReaction()  # type: libsbml.Reaction
        self.set_fields(r)

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
            Reaction.set_kinetic_law(model, r, self.formula.value)

        # add fbc bounds
        if self.upperFluxBound or self.lowerFluxBound:
            r_fbc = r.getPlugin("fbc")  # type: libsbml.FbcReactionPlugin
            if self.upperFluxBound:
                r_fbc.setUpperFluxBound(self.upperFluxBound)
            if self.lowerFluxBound:
                r_fbc.setLowerFluxBound(self.lowerFluxBound)

        self.create_port(model)
        self.create_uncertainties(r)
        return r

    def set_fields(self, obj):
        super(Reaction, self).set_fields(obj)

        if self.compartment:
            obj.setCompartment(self.compartment)
        obj.setReversible(self.equation.reversible)
        obj.setFast(self.fast)

    @staticmethod
    def set_kinetic_law(model, reaction, formula):
        """ Sets the kinetic law in reaction based on given formula. """
        law = reaction.createKineticLaw()
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            logging.error(libsbml.getLastParseL3Error())
        check(law.setMath(ast_node), 'set math in kinetic law')
        return law


class ExchangeReaction(Reaction):
    """ Exchange reactions define substances which can be exchanged.
     This is important for FBC models.

     EXCHANGE_IMPORT (-INF, 0): is defined as negative flux through the exchange reaction,
        i.e. the upper bound must be 0, the lower bound some negative value,
        e.g. -INF

    EXCHANGE_EXPORT (0, INF): is defined as positive flux through the exchange reaction,
        i.e. the lower bound must be 0, the upper bound some positive value,
        e.g. INF
     """
    PREFIX = 'EX_'

    def __init__(self, species_id,
                 name=None, compartment=None, fast=False, reversible=None,
                 metaId=None, annotations=None,
                 lowerFluxBound=None, upperFluxBound=None,
                 uncertainties=None, port=None):

        super(ExchangeReaction, self).__init__(
            sid=ExchangeReaction.PREFIX + species_id,
            equation="{} ->".format(species_id),
            sboTerm=SBO_EXCHANGE_REACTION,
            name=name,
            compartment=compartment,
            fast=fast,
            reversible=reversible,
            metaId=metaId,
            annotations=annotations,
            lowerFluxBound=lowerFluxBound,
            upperFluxBound=upperFluxBound,
            uncertainties=uncertainties,
            port=port
        )


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

