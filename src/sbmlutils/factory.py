"""Factory for creating SBML objects.

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
from collections import namedtuple
from typing import Any, Dict, List, Optional, Tuple, Union

import libsbml
import numpy as np
from libsbml import DISTRIB_UNCERTTYPE_MEAN as UNCERTTYPE_MEAN
from libsbml import DISTRIB_UNCERTTYPE_RANGE as UNCERTTYPE_RANGE
from libsbml import DISTRIB_UNCERTTYPE_STANDARDDEVIATION as UNCERTTYPE_STANDARDDEVIATION

from sbmlutils.equation import Equation
from sbmlutils.metadata import BQB, BQM
from sbmlutils.metadata.annotator import Annotation, ModelAnnotator
from sbmlutils.metadata.sbo import SBO
from sbmlutils.utils import deprecated
from sbmlutils.validation import check


# FIXME: make complete import of all DISTRIB constants

__all__ = [
    "UNCERTTYPE_MEAN",
    "UNCERTTYPE_STANDARDDEVIATION",
    "UNCERTTYPE_RANGE",
    "SBML_LEVEL",
    "SBML_VERSION",
    "PORT_SUFFIX",
    "PORT_UNIT_SUFFIX",
    "Notes",
    "ModelUnits",
    "Creator",
    "Compartment",
    "Unit",
    "Function",
    "Species",
    "Parameter",
    "InitialAssignment",
    "AssignmentRule",
    "RateRule",
    "Event",
    "Constraint",
    "Reaction",
    "Formula",
    "Equation",
    "ExchangeReaction",
    "Uncertainty",
    "UncertParameter",
    "UncertSpan",
    "Objective",
    "ExternalModelDefinition",
    "ModelDefinition",
    "Submodel",
    "Deletion",
    "ReplacedElement",
    "ReplacedBy",
    "Port",
]

logger = logging.getLogger(__name__)

SBML_LEVEL = 3  # default SBML level
SBML_VERSION = 1  # default SBML version
PORT_SUFFIX = "_port"
PORT_UNIT_SUFFIX = "_unit_port"
PREFIX_EXCHANGE_REACTION = "EX_"

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


def create_objects(
    model: libsbml.Model, obj_iter: List[Any], key: str = None, debug: bool = False
) -> Dict[str, libsbml.SBase]:
    """Create the objects in the model.

    This function calls the respective create_sbml function of all objects
    in the order of the objects.

    :param model: SBMLModel instance
    :param obj_iter: iterator of given model object classes like Parameter, ...
    :param key: object key
    :param debug: print list of created objects
    :return: dictionary of SBML objects
    """
    sbml_objects: Dict[str, libsbml.Sbase] = {}
    try:
        for obj in obj_iter:
            if obj is None:
                logger.error(
                    f"Trying to create None object, "
                    f"check for incorrect terminating ',' on objects: "
                    f"'{sbml_objects}'"
                )
            if debug:
                print(obj)
            sbml_obj: libsbml.Sbase = obj.create_sbml(model)
            # FIXME: what happens for objects without id?
            sbml_objects[sbml_obj.getId()] = sbml_obj
    except Exception as err:
        logger.error(f"Error creation SBML objects '{key}: {obj_iter}'")
        logger.error(err)
        raise err

    return sbml_objects


def ast_node_from_formula(model: libsbml.Model, formula: str) -> libsbml.ASTNode:
    """Parse the ASTNode from given formula string with model.

    :param model: SBMLModel instance
    :param formula: formula str
    :return: astnode
    """
    # sanitize formula (allow double and int assignments)
    if not isinstance(formula, str):
        formula = str(formula)

    ast_node = libsbml.parseL3FormulaWithModel(formula, model)
    if not ast_node:
        logger.error("Formula could not be parsed: '{}'".format(formula))
        logger.error(libsbml.getLastParseL3Error())
    return ast_node


"""
---------------------------------------------------------------------------------------
Core information
---------------------------------------------------------------------------------------
"""
UnitType = Optional[Union[str, libsbml.UnitDefinition, "Unit"]]
AnnotationsType = Optional[List[Union[Annotation, Tuple[Union[BQB, BQM], str]]]]
PortType = Any  # Union[bool, Port]


class Notes:
    """SBML notes."""

    def __init__(self, notes: Union[Dict[str, str], List[str], str]):
        """Initialize notes object."""
        tokens = ["<body xmlns='http://www.w3.org/1999/xhtml'>"]
        if isinstance(notes, (dict, list)):
            tokens.extend(notes)
        else:
            tokens.append(notes)

        tokens.append("</body>")
        notes_str = "\n".join(tokens)
        self.xml: libsbml.XMLNode = libsbml.XMLNode.convertStringToXMLNode(notes_str)
        if self.xml is None:
            raise ValueError(f"XMLNode could not be generated for:\n{notes}")

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.xml.toXMLString())


def set_notes(sbase: libsbml.SBase, notes: Union[Notes, str]) -> None:
    """Set notes information on SBase.

    :param sbase: SBase
    :param notes: notes information (xml string)
    :return:
    """
    if not isinstance(notes, Notes):
        notes = Notes(notes)

    check(sbase.setNotes(notes.xml), message=f"Setting notes on '{sbase}'")


class ModelUnits:
    """Class for storing model units information.

    The ModelUnits define globally the units for `time`, `extent`, `substance`,
    `length`, `area` and `volume`.

    The following SBML Level 3 base units can be used.

       ampere         farad  joule     lux     radian     volt
       avogadro       gram   katal     metre   second     watt
       becquerel      gray   kelvin    mole    siemens    weber
       candela        henry  kilogram  newton  sievert
       coulomb        hertz  litre     ohm     steradian
       dimensionless  item   lumen     pascal  tesla
    """

    def __init__(
        self,
        time: UnitType = None,
        extent: UnitType = None,
        substance: UnitType = None,
        length: UnitType = None,
        area: UnitType = None,
        volume: UnitType = None,
    ):
        self.time = time
        self.extent = extent
        self.substance = substance
        self.length = length
        self.area = area
        self.volume = volume

    @staticmethod
    def set_model_units(model: libsbml.Model, model_units: "ModelUnits") -> None:
        """Set the main units in model from dictionary.

        Setting the model units is important for understanding the model
        dynamics.
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
            logger.error(
                "Providing model units as dict is deprecated, use 'ModelUnits' instead."
            )
            model_units = ModelUnits(**model_units)

        if not model_units:
            logger.warning(
                "Model units should be set for a model. These can be stored "
                "using the 'model_units' on a model definition."
            )
        else:
            for key in ("time", "extent", "substance", "length", "area", "volume"):

                if getattr(model_units, key) is None:
                    msg = f"The information for '{key}' is missing in model_units."
                    if key in ["time", "extent", "substance", "volume"]:
                        # strongly recommended fields
                        logger.warning(msg)
                    else:
                        # optional fields
                        logger.info(msg)

                    continue

                unit = getattr(model_units, key)
                unit = Unit.get_unit_string(unit)
                # set the values
                if key == "time":
                    model.setTimeUnits(unit)
                elif key == "extent":
                    model.setExtentUnits(unit)
                elif key == "substance":
                    model.setSubstanceUnits(unit)
                elif key == "length":
                    model.setLengthUnits(unit)
                elif key == "area":
                    model.setAreaUnits(unit)
                elif key == "volume":
                    model.setVolumeUnits(unit)


class Creator:
    """Creator in ModelHistory."""

    def __init__(
        self,
        familyName: str,
        givenName: str,
        email: str,
        organization: str,
        site: Optional[str] = None,
    ):
        self.familyName = familyName
        self.givenName = givenName
        self.email = email
        self.organization = organization
        self.site = site


class Sbase:
    """Base class of all SBML objects."""

    def __init__(
        self,
        sid: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.notes = notes
        self.port = port
        self.uncertainties = uncertainties
        self.replacedBy = replacedBy
        self.annotations: AnnotationsType = annotations

    def __str__(self) -> str:
        """Get string representation."""
        tokens = str(self.__class__).split(".")
        class_name = tokens[-1][:-2]
        name = self.name
        if name is None:
            name = ""
        else:
            name = " " + name
        return f"<{class_name}[{self.sid}]{name}>"

    @staticmethod
    def _process_annotations(annotation_objects: AnnotationsType) -> List[Annotation]:
        """Process annotation information.

        Various annotation formats are supported which have to be unified at some
        point. This function is performing the annotation normalization.
        """
        annotations: List[Annotation] = []
        if annotation_objects is not None:
            for annotation_obj in annotation_objects:
                annotation: Annotation
                if isinstance(annotation_obj, Annotation):
                    annotation = annotation_obj
                elif isinstance(annotation_obj, (tuple, list, set)):
                    annotation = Annotation.from_tuple(annotation_obj)  # type: ignore
                annotations.append(annotation)
        return annotations

    def _set_fields(self, obj: libsbml.SBase, model: libsbml.Model) -> None:
        if self.sid is not None:
            if not libsbml.SyntaxChecker.isValidSBMLSId(self.sid):
                logger.error(
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

        if self.notes is not None:
            set_notes(obj, self.notes)

        # annotation handling
        processed_annotations: List[Annotation] = []
        if self.annotations:
            # annotations can have been added after initial processing
            processed_annotations = Sbase._process_annotations(self.annotations)

        if self.sboTerm is not None:
            sbo_annotation = Annotation(
                qualifier=BQB.IS, resource=f"sbo/{self.sboTerm.replace('_', ':')}"
            )
            # check if SBO annotation exists
            sbo_exists = False
            for annotation in processed_annotations:
                if (
                    annotation.qualifier == sbo_annotation.qualifier
                    and annotation.term == sbo_annotation.term
                ):
                    sbo_exists = True
                    continue
            if not sbo_exists:
                processed_annotations = [sbo_annotation] + processed_annotations

        for annotation in processed_annotations:
            ModelAnnotator.annotate_sbase(sbase=obj, annotation=annotation)

        self.create_uncertainties(obj, model)
        self.create_replaced_by(obj, model)

    def create_port(self, model: libsbml.Model) -> Optional[libsbml.Port]:
        """Create port if existing."""
        if self.port is None:
            return None

        p: libsbml.Port = None
        if isinstance(self.port, bool):
            if self.port is True:
                # manually create port for the id
                cmodel = model.getPlugin("comp")
                p = cmodel.createPort()
                if isinstance(self, Unit):
                    port_sid = f"{self.sid}{PORT_UNIT_SUFFIX}"
                else:
                    port_sid = f"{self.sid}{PORT_SUFFIX}"
                p.setId(port_sid)
                p.setName(port_sid)
                p.setMetaId(port_sid)
                p.setSBOTerm(599)  # port

                if isinstance(self, Unit):
                    p.setUnitRef(self.sid)
                else:
                    p.setIdRef(self.sid)
        else:
            # use the port object
            if (
                (not self.port.portRef)
                and (not self.port.idRef)
                and (not self.port.unitRef)
                and (not self.port.metaIdRef)
            ):
                # if no reference set id reference to current object
                self.port.idRef = self.sid
            p = self.port.create_sbml(model)

        return p

    def create_uncertainties(
        self, obj: libsbml.SBase, model: libsbml.Model
    ) -> Optional[List[libsbml.Uncertainty]]:
        """Create distrib:Uncertainty objects."""
        if not self.uncertainties:
            return None

        objects = []

        # FIXME: check that distrib package is activated

        for uncertainty in self.uncertainties:  # type: Uncertainty
            objects.append(uncertainty.create_sbml(obj, model))
        return objects

    def create_replaced_by(
        self, obj: libsbml.SBase, model: libsbml.Model
    ) -> Optional[libsbml.ReplacedBy]:
        """Create comp:ReplacedBy."""
        if not self.replacedBy:
            return None

        return self.replacedBy.create_sbml(obj, model)


class Value(Sbase):
    """Helper class.

    The value field is a helper storage field which is used differently by different
    subclasses.
    """

    def __init__(
        self,
        sid: Optional[str],
        value: Union[str, float],
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Value, self).__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.value = value

    def _set_fields(self, obj: libsbml.SBase, model: libsbml.Model) -> None:
        super(Value, self)._set_fields(obj, model)


class ValueWithUnit(Value):
    """Helper class.

    The value field is a helper storage field which is used differently by different
    subclasses.
    """

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.sid} = {self.value} [{self.unit}]"

    def __init__(
        self,
        sid: str,
        value: Union[str, float],
        unit: UnitType = "-",
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(ValueWithUnit, self).__init__(
            sid,
            value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            port=port,
            annotations=annotations,
            notes=notes,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.unit = unit

    def _set_fields(self, obj: libsbml.SBase, model: libsbml.Model) -> None:
        super(ValueWithUnit, self)._set_fields(obj, model)
        if self.unit is not None:
            if obj.getTypeCode() in [
                libsbml.SBML_ASSIGNMENT_RULE,
                libsbml.SBML_RATE_RULE,
            ]:
                # AssignmentRules and RateRules have no units
                pass
            else:
                unit_str = Unit.get_unit_string(self.unit)
                check(obj.setUnits(unit_str), f"Set unit '{unit_str}' on {obj}")


class Unit(Sbase):
    """Unit.

    Corresponds to the information in the libsbml.UnitDefinition.
    """

    def __init__(
        self,
        sid: str,
        definition: Any,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Unit, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.definition = definition

    def create_sbml(self, model: libsbml.Model) -> libsbml.UnitDefinition:
        """Create libsbml.UnitDefinition.

        (kind, exponent, scale, multiplier)
        """
        obj: libsbml.UnitDefinition = model.createUnitDefinition()

        for data in self.definition:
            kind = data[0]
            exponent = data[1]
            scale = 0
            multiplier = 1.0
            if len(data) > 2:
                scale = data[2]
            if len(data) > 3:
                multiplier = data[3]

            Unit._create_unit(obj, kind, exponent, scale, multiplier)

        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    def _set_fields(self, obj: libsbml.UnitDefinition, model: libsbml.Model) -> None:
        """Set fields on libsbml.UnitDefinition."""
        super(Unit, self)._set_fields(obj, model)

    @staticmethod
    def _create_unit(
        udef: libsbml.UnitDefinition,
        kind: str,
        exponent: float,
        scale: int = 0,
        multiplier: float = 1.0,
    ) -> libsbml.Unit:
        """Create libsbml.Unit."""
        unit: libsbml.Unit = udef.createUnit()
        unit.setKind(kind)
        unit.setExponent(exponent)
        unit.setScale(scale)
        unit.setMultiplier(multiplier)
        return unit

    @staticmethod
    def get_unit_string(unit: UnitType) -> Optional[str]:
        """Get string representation for unit.

        Units can be either integer libsbml codes which are converted to the correct
        strings or these strings:

           ampere         farad  joule     lux     radian     volt
           avogadro       gram   katal     metre   second     watt
           becquerel      gray   kelvin    mole    siemens    weber
           candela        henry  kilogram  newton  sievert
           coulomb        hertz  litre     ohm     steradian
           dimensionless  item   lumen     pascal  tesla

        In addition custom units are possible.
        """
        if isinstance(unit, Unit):
            return unit.sid
        elif isinstance(unit, (int, str)):
            if isinstance(unit, int):
                # libsbml unit
                unit_str = str(libsbml.UnitKind_toString(unit))
            if isinstance(unit, str):
                unit_str = unit
            if unit_str == "meter":
                return "metre"
            elif unit_str == "liter":
                return "litre"
            elif unit_str == "-":
                return "dimensionless"
            return unit_str
        else:
            return None


class Function(Sbase):
    """SBML FunctionDefinitions.

    FunctionDefinitions consist of a lambda expression in the value field, e.g.,
        lambda(x,y, piecewise(x,gt(x,y),y) )  #  definition of minimum function
        lambda(x, sin(x) )
    """

    def __init__(
        self,
        sid: str,
        value: str,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Function, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.formula = value

    def create_sbml(self, model: libsbml.Model) -> libsbml.FunctionDefinition:
        """Create FunctionDefinition SBML in model."""
        fd: libsbml.FunctionDefinition = model.createFunctionDefinition()
        self._set_fields(fd, model)

        self.create_port(model)
        return fd

    def _set_fields(
        self, obj: libsbml.FunctionDefinition, model: libsbml.Model
    ) -> None:
        super(Function, self)._set_fields(obj, model)
        ast_node = ast_node_from_formula(model, self.formula)
        obj.setMath(ast_node)


class Parameter(ValueWithUnit):
    """Parameter."""

    def __init__(
        self,
        sid: str,
        value: Optional[Union[str, float]] = None,
        unit: UnitType = None,
        constant: bool = True,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Parameter, self).__init__(
            sid=sid,
            value=value,  # type: ignore
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.constant = constant

    def create_sbml(self, model: libsbml.Model) -> libsbml.Parameter:
        """Create Parameter SBML in model."""
        obj: libsbml.Parameter = model.createParameter()
        self._set_fields(obj, model)
        if self.value is None:
            obj.setValue(np.NaN)

        elif type(self.value) is str:
            try:
                # check if number
                value = float(self.value)
                logger.warning(
                    f"When setting a numeric value use float not str: '{self}'."
                )
                obj.setValue(value)
            except ValueError:
                if self.constant:
                    InitialAssignment(self.sid, self.value).create_sbml(model)  # type: ignore
                else:
                    AssignmentRule(self.sid, self.value).create_sbml(model)  # type: ignore
        else:
            # numerical value
            obj.setValue(float(self.value))

        self.create_port(model)
        return obj

    def _set_fields(self, obj: libsbml.Parameter, model: libsbml.Model) -> None:
        """Set fields."""
        super(Parameter, self)._set_fields(obj, model)
        obj.setConstant(self.constant)


class Compartment(ValueWithUnit):
    """Compartment."""

    def __init__(
        self,
        sid: str,
        value: Union[str, float],
        unit: UnitType = None,
        constant: bool = True,
        spatialDimensions: float = 3,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Compartment, self).__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.constant = constant
        self.spatialDimensions = spatialDimensions

    def create_sbml(self, model: libsbml.Model) -> libsbml.Compartment:
        """Create Compartment SBML in model."""
        obj: libsbml.Compartment = model.createCompartment()
        self._set_fields(obj, model)

        if self.value is None:
            obj.setSize(np.NaN)
        elif type(self.value) is str:
            try:
                # check if number
                value = float(self.value)
                logger.warning(
                    f"When setting a numeric value use float not str: '{self}'."
                )
                obj.setSize(value)
            except ValueError:
                if self.constant:
                    InitialAssignment(self.sid, self.value).create_sbml(model)  # type: ignore
                else:
                    AssignmentRule(self.sid, self.value).create_sbml(model)  # type: ignore
        else:
            obj.setSize(float(self.value))

        self.create_port(model)
        return obj

    def _set_fields(self, obj: libsbml.Compartment, model: libsbml.Model) -> None:
        """Set fields on Compartment."""
        super(Compartment, self)._set_fields(obj, model)
        obj.setConstant(self.constant)
        obj.setSpatialDimensions(self.spatialDimensions)


class Species(Sbase):
    """Species."""

    def __init__(
        self,
        sid: str,
        compartment: str,
        initialAmount: Optional[float] = None,
        initialConcentration: Optional[float] = None,
        substanceUnit: UnitType = None,
        hasOnlySubstanceUnits: bool = False,
        constant: bool = False,
        boundaryCondition: bool = False,
        charge: Optional[float] = None,
        chemicalFormula: Optional[str] = None,
        conversionFactor: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Species, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        if (initialAmount is None) and (initialConcentration is None):
            raise ValueError(
                f"Either initialAmount or initialConcentration required "
                f"for species: '{sid}'"
            )
        if initialAmount and initialConcentration:
            raise ValueError(
                f"Either initialAmount or initialConcentration can be set on "
                f"species, but not both: {sid}"
            )
        self._substanceUnit = None  # type: ignore
        self.substanceUnit = substanceUnit
        self.initialAmount = initialAmount
        self.initialConcentration = initialConcentration
        self.compartment = compartment
        self.constant = constant
        self.boundaryCondition = boundaryCondition
        self.hasOnlySubstanceUnits = hasOnlySubstanceUnits
        self.charge = charge
        self.chemicalFormula = chemicalFormula
        self.conversionFactor = conversionFactor

    @property
    def substanceUnit(self) -> Optional[UnitType]:
        """Get substanceUnit."""
        return self._substanceUnit

    @substanceUnit.setter
    def substanceUnit(self, value: Optional[UnitType]) -> None:
        """Set substanceUnit."""
        self._substanceUnit = Unit.get_unit_string(value)

    def create_sbml(self, model: libsbml.Model) -> libsbml.Species:
        """Create Species SBML in model."""
        s: libsbml.Species = model.createSpecies()
        self._set_fields(s, model)
        # substance unit must be set on the given substance unit
        s.setSubstanceUnits(model.getSubstanceUnits())
        if self.substanceUnit is not None:
            s.setSubstanceUnits(self.substanceUnit)
        else:
            s.setSubstanceUnits(model.getSubstanceUnits())

        self.create_port(model)
        return s

    def _set_fields(self, obj: libsbml.Species, model: libsbml.Model) -> None:
        """Set fields on libsbml.Species."""
        super(Species, self)._set_fields(obj, model)
        obj.setConstant(self.constant)
        if self.compartment is None:
            raise ValueError(f"Compartment cannot be None on Species: '{self}'")
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
            obj_fbc: libsbml.FbcSpeciesPlugin = obj.getPlugin("fbc")
            if obj_fbc is None:
                logger.error(
                    "FbcSpeciesPlugin does not exist, add `packages = ['fbc']` "
                    "to model definition."
                )
            else:
                if self.charge is not None:
                    obj_fbc.setCharge(int(self.charge))
                if self.chemicalFormula is not None:
                    obj_fbc.setChemicalFormula(self.chemicalFormula)


class InitialAssignment(Value):
    """InitialAssignments.

    The unit attribute is only for the case where a parameter must be created
    (which has the unit). In case of an initialAssignment of a value the units
    have to be defined in the math.
    """

    def __init__(
        self,
        sid: str,
        value: Union[str, float],
        unit: UnitType = "-",
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(InitialAssignment, self).__init__(
            sid,
            value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.unit = unit

    def create_sbml(self, model: libsbml.Model) -> libsbml.InitialAssignment:
        """Create InitialAssignment.

        Creates a required parameter if the symbol for the
        initial assignment does not exist in the model.
        """
        sid = self.sid
        # Create parameter if not existing
        if (
            (not model.getParameter(sid))
            and (not model.getSpecies(sid))
            and (not model.getCompartment(sid))
        ):
            Parameter(
                sid=sid, value=None, unit=self.unit, constant=True, name=self.name  # type: ignore
            ).create_sbml(model)

        obj: libsbml.InitialAssignment = model.createInitialAssignment()
        self._set_fields(obj, model)
        obj.setSymbol(sid)
        ast_node = ast_node_from_formula(model, str(self.value))
        obj.setMath(ast_node)

        self.create_port(model)
        return obj


class Rule(ValueWithUnit):
    """Rule."""

    rule_types = ["AssignmentRule", "RateRule"]

    def __repr__(self) -> str:
        """Get string representation."""
        return super(Rule, self).__repr__()

    @staticmethod
    def _rule_factory(
        model: libsbml.Model, rule: libsbml.Rule, rule_type: str, value: float = None
    ) -> Union["RateRule", "AssignmentRule", libsbml.Rule]:
        """Create libsbml rule of given rule_type.

        :param model:
        :param rule:
        :param rule_type:
        :return:
        """
        if rule_type not in Rule.rule_types:
            raise ValueError(
                f"rule_type '{rule_type}' is not supported, use one of: "
                f"{Rule.rule_types}"
            )
        sid = rule.sid

        # Create parameter if symbol is neither parameter or species, or compartment
        if (
            (not model.getParameter(sid))
            and (not model.getSpecies(sid))
            and (not model.getCompartment(sid))
        ):

            Parameter(
                sid, unit=rule.unit, name=rule.name, value=value, constant=False
            ).create_sbml(model)

        # Make sure the parameter is const=False
        p: libsbml.Parameter = model.getParameter(sid)
        if p is not None:
            if p.getConstant() is True:
                logger.warning(
                    f"Parameter affected by AssignmentRule or RateRule "
                    f"should be set 'constant=False', but '{p.getId()}' "
                    f"is 'constant={p.getConstant()}'."
                )
                p.setConstant(False)

        # Add rule if not existing
        obj: Union[RateRule, AssignmentRule]
        if not model.getRule(sid):
            if rule_type == "RateRule":
                obj = RateRule._create(model, sid=sid, formula=rule.value)
            elif rule_type == "AssignmentRule":
                obj = AssignmentRule._create(model, sid=sid, formula=rule.value)
        else:
            logger.warning(
                f"Rule with sid already exists in model: {sid}. "
                f"Rule not updated with '{rule.value}'"
            )
            return model.getRule(sid)
        return obj

    def create_sbml(self, model: libsbml.Model) -> None:
        """Create Rule in model.

        :param model:
        :return:
        """
        logger.error(
            "Rule cannot be created, use either <AssignmentRule> or <RateRule>."
        )
        raise NotImplementedError

    @staticmethod
    def _create_rule(
        model: libsbml.Model,
        rule: Union[libsbml.RateRule, libsbml.AssignmentRule, libsbml.Rule],
        sid: str,
        formula: str,
    ) -> Union[libsbml.RateRule, libsbml.AssignmentRule, libsbml.Rule]:
        """Set information in rule."""
        rule.setVariable(sid)
        ast_node = ast_node_from_formula(model, formula)
        rule.setMath(ast_node)
        return rule


class AssignmentRule(Rule):
    """AssignmentRule."""

    def __repr__(self) -> str:
        """Representation."""
        return "<AssignmentRule({})>".format(super(AssignmentRule, self).__repr__())

    def create_sbml(self, model: libsbml.Model) -> libsbml.AssignmentRule:
        """Create AssignmentRule in model.

        :param model:
        :return:
        """
        obj: libsbml.AssignmentRule = Rule._rule_factory(
            model, self, rule_type="AssignmentRule"
        )
        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    @staticmethod
    def _create(model: libsbml.Model, sid: str, formula: str) -> libsbml.AssignmentRule:
        """Create libsbml AssignmentRule."""
        rule: libsbml.AssignmentRule = model.createAssignmentRule()
        return Rule._create_rule(model, rule, sid, formula)


class RateRule(Rule):
    """RateRule."""

    def create_sbml(self, model: libsbml.Model) -> libsbml.RateRule:
        """Create RateRule in model."""
        obj: libsbml.RateRule = Rule._rule_factory(model, self, rule_type="RateRule")
        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    @staticmethod
    def _create(model: libsbml.Model, sid: str, formula: str) -> libsbml.RateRule:
        """Create libsbml.RateRule."""
        rule: libsbml.RateRule = model.createRateRule()
        return Rule._create_rule(model, rule, sid, formula)


Formula = namedtuple("Formula", "value unit")


class Reaction(Sbase):
    """Reaction.

    Class for creating libsbml.Reaction.

    Equations are of the form
    '1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]'

    The equation consists of
    - substrates concatenated via '+' on the left side
      (with optional stoichiometric coefficients)
    - separation characters separating the left and right equation sides:
      '<=>' or '<->' for reversible reactions,
      '=>' or '->' for irreversible reactions (irreversible reactions
      are written from left to right)
    - products concatenated via '+' on the right side
      (with optional stoichiometric coefficients)
    - optional list of modifiers within brackets [] separated by ','

    Examples of valid equations are:
        '1.0 S1 + 2 S2 => 2.0 P1 + 2 P2 [M1, M2]',
        'c__gal1p => c__gal + c__phos',
        'e__h2oM <-> c__h2oM',
        '3 atp + 2.0 phos + ki <-> 16.98 tet',
        'c__gal1p => c__gal + c__phos [c__udp, c__utp]',
        'A_ext => A []',
        '=> cit',
        'acoa =>',
    """

    def __init__(
        self,
        sid: str,
        equation: Union[Equation, str],
        formula: Optional[Union[Formula, Tuple[str, UnitType], str]] = None,
        pars: Optional[List[Parameter]] = None,
        rules: Optional[List[Rule]] = None,
        compartment: Optional[str] = None,
        fast: bool = False,
        reversible: Optional[bool] = None,
        lowerFluxBound: Optional[str] = None,
        upperFluxBound: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Reaction, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        if pars is None:
            pars = list()
        if rules is None:
            rules = list()

        self.equation = Reaction._process_equation(equation=equation)
        self.compartment = compartment
        self.reversible = reversible
        self.pars = pars
        self.rules = rules
        self.formula = Reaction._process_formula(formula=formula)
        self.fast = fast
        self.lowerFluxBound = lowerFluxBound
        self.upperFluxBound = upperFluxBound

    @staticmethod
    def _process_equation(equation: Union[Equation, str]) -> Equation:
        """Process reaction equation."""
        if isinstance(equation, Equation):
            return equation
        else:
            return Equation(equation=equation)

    @staticmethod
    def _process_formula(
        formula: Optional[Union[Formula, Tuple[str, UnitType], str]]
    ) -> Optional[Formula]:
        """Process reaction formula (kinetic law)."""
        if formula is None:
            return None
        elif isinstance(formula, Formula):
            return formula
        elif isinstance(formula, (tuple, list)):
            return Formula(*formula)
        elif isinstance(formula, str):
            return Formula(value=formula, unit=None)
        else:
            raise ValueError(f"Unsupported formula: '{formula}'")

    def create_sbml(self, model: libsbml.Model) -> libsbml.Reaction:
        """Create Reaction SBML in model."""
        # parameters and rules
        create_objects(model, self.pars, key="parameters")
        create_objects(model, self.rules, key="rules")

        # reaction
        r: libsbml.Reaction = model.createReaction()
        self._set_fields(r, model)

        # equation
        for reactant in self.equation.reactants:
            rref: libsbml.SpeciesReference = r.createReactant()
            rref.setSpecies(reactant.sid)
            rref.setStoichiometry(reactant.stoichiometry)
            rref.setConstant(True)

        for product in self.equation.products:
            pref: libsbml.SpeciesReference = r.createProduct()
            pref.setSpecies(product.sid)
            pref.setStoichiometry(product.stoichiometry)
            pref.setConstant(True)

        for modifier in self.equation.modifiers:
            mref: libsbml.ModifierSpeciesReference = r.createModifier()
            mref.setSpecies(modifier)

        # kinetics
        if self.formula:
            Reaction.set_kinetic_law(model, r, self.formula.value)

        # add fbc bounds
        if self.upperFluxBound or self.lowerFluxBound:
            r_fbc: libsbml.FbcReactionPlugin = r.getPlugin("fbc")
            if self.upperFluxBound:
                r_fbc.setUpperFluxBound(self.upperFluxBound)
            if self.lowerFluxBound:
                r_fbc.setLowerFluxBound(self.lowerFluxBound)

        self.create_port(model)
        return r

    def _set_fields(self, obj: libsbml.Reaction, model: libsbml.Model) -> None:
        """Set fields in libsbml.Reaction."""
        super(Reaction, self)._set_fields(obj, model)

        if self.compartment:
            obj.setCompartment(self.compartment)
        obj.setReversible(self.equation.reversible)
        obj.setFast(self.fast)

    @staticmethod
    def set_kinetic_law(
        model: libsbml.Model, reaction: libsbml.Reaction, formula: str
    ) -> libsbml.KineticLaw:
        """Set the kinetic law in reaction based on given formula."""
        law: libsbml.KineticLaw = reaction.createKineticLaw()
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            logger.error(libsbml.getLastParseL3Error())
        check(law.setMath(ast_node), "set math in kinetic law")
        return law


class Event(Sbase):
    """Event.

    Trigger have the format of a logical expression:
        time%200 == 0
    Assignments have the format
        sid = value

    """

    def __init__(
        self,
        sid: str,
        trigger: str,
        assignments: Optional[Dict[str, Union[str, float]]] = None,
        trigger_persistent: bool = True,
        trigger_initialValue: bool = False,
        useValuesFromTriggerTime: bool = True,
        priority: Optional[str] = None,
        delay: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Event, self).__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        self.trigger = trigger
        self.assignments = assignments if assignments else {}
        if type(assignments) is not dict:
            logger.warning(
                f"Event assignment must be dict with sid: assignment, but: "
                f"'{type(assignments)}'"
            )
        self.trigger_persistent = trigger_persistent
        self.trigger_initialValue = trigger_initialValue
        self.useValuesFromTriggerTime = useValuesFromTriggerTime

        self.priority = priority
        self.delay = delay

    def create_sbml(self, model: libsbml.Model) -> libsbml.Event:
        """Create Event SBML in model."""
        event: libsbml.Event = model.createEvent()
        self._set_fields(event, model)

        return event

    def _set_fields(self, obj: libsbml.Event, model: libsbml.Model) -> None:
        """Set fields in libsbml.Event."""
        super(Event, self)._set_fields(obj, model)

        obj.setUseValuesFromTriggerTime(True)
        t = obj.createTrigger()
        t.setInitialValue(
            self.trigger_initialValue
        )  # False ! not supported by Copasi -> lame fix via time
        t.setPersistent(
            self.trigger_persistent
        )  # True ! not supported by Copasi -> careful with usage

        ast_trigger = libsbml.parseL3FormulaWithModel(self.trigger, model)
        t.setMath(ast_trigger)

        if self.priority is not None:
            ast_priority = libsbml.parseL3FormulaWithModel(self.priority, model)
            priority: libsbml.Priority = obj.createPriority()
            priority.setMath(ast_priority)

        if self.delay is not None:
            ast_delay = libsbml.parseL3FormulaWithModel(self.delay, model)
            obj.setDelay(ast_delay)

        for key, math in self.assignments.items():
            ast_assign = libsbml.parseL3FormulaWithModel(str(math), model)
            ea = obj.createEventAssignment()
            ea.setVariable(key)
            ea.setMath(ast_assign)

    @staticmethod
    def _trigger_from_time(t: float) -> str:
        """Create trigger from given time point."""
        return f"(time >= {t})"

    @staticmethod
    def _assignments_dict(species: List[str], values: List[str]) -> Dict[str, str]:
        return dict(zip(species, values))


"""
---------------------------------------------------------------------------------------
distrib information
---------------------------------------------------------------------------------------
"""


class UncertParameter:
    """UncertParameter.

    FIXME: This is an SBase!
    """

    def __init__(
        self,
        type: str,
        value: Optional[float] = None,
        var: Optional[str] = None,
        unit: UnitType = None,
    ):
        if (value is None) and (var is None):
            raise ValueError(
                "Either 'value' or 'var' have to be set in UncertParameter."
            )
        self.type: str = type
        self.value: Optional[float] = value
        self.var: Optional[str] = var
        self.unit: UnitType = unit


class UncertSpan:
    """UncertSpan.

    FIXME: This is an SBase!
    """

    def __init__(
        self,
        type: str,
        valueLower: Optional[float] = None,
        varLower: Optional[str] = None,
        valueUpper: Optional[float] = None,
        varUpper: Optional[str] = None,
        unit: UnitType = None,
    ):
        if (valueLower is None) and (varLower is None):
            raise ValueError(
                "Either 'valueLower' or 'varLower' have to be set in UncertSpan."
            )
        if (valueUpper is None) and (varUpper is None):
            raise ValueError(
                "Either 'valueLower' or 'varLower' have to be set in UncertSpan."
            )

        self.type = type
        self.valueLower = valueLower
        self.varLower = varLower
        self.valueUpper = valueUpper
        self.varUpper = varUpper
        self.unit = unit


class Uncertainty(Sbase):
    """Uncertainty.

    Uncertainty information for Sbase.
    """

    def __init__(
        self,
        sid: Optional[str] = None,
        formula: Optional[str] = None,
        uncertParameters: Optional[List[UncertParameter]] = None,
        uncertSpans: Optional[List[UncertSpan]] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Uncertainty, self).__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            replacedBy=replacedBy,
        )

        # Object on which the uncertainty is written
        self.formula = formula
        self.uncertParameters: List[UncertParameter] = (
            uncertParameters if uncertParameters else []
        )
        self.uncertSpans: List[UncertSpan] = uncertSpans if uncertSpans else []

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.Uncertainty:
        """Create libsbml Uncertainty.

        :param sbase:
        :param model:
        :return:
        """
        sbase_distrib: libsbml.DistribSBasePlugin = sbase.getPlugin("distrib")
        uncertainty: libsbml.Uncertainty = sbase_distrib.createUncertainty()

        self._set_fields(uncertainty, model)

        uncertSpan: UncertSpan
        for uncertSpan in self.uncertSpans:
            if uncertSpan.type in [
                libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
                libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
                libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
                libsbml.DISTRIB_UNCERTTYPE_RANGE,
            ]:
                up_span: libsbml.UncertSpan = uncertainty.createUncertSpan()
                up_span.setType(uncertSpan.type)
                if uncertSpan.valueLower is not None:
                    up_span.setValueLower(uncertSpan.valueLower)
                if uncertSpan.valueUpper is not None:
                    up_span.setValueUpper(uncertSpan.valueUpper)
                if uncertSpan.varLower is not None:
                    up_span.setVarLower(uncertSpan.varLower)
                if uncertSpan.varUpper is not None:
                    up_span.setValueLower(uncertSpan.varUpper)
                if uncertSpan.unit:
                    up_span.setUnits(Unit.get_unit_string(uncertSpan.unit))
            else:
                logger.error(
                    f"Unsupported type for UncertSpan: '{uncertSpan.type}' "
                    f"in '{uncertSpan}'."
                )

        uncertParameter: UncertParameter
        for uncertParameter in self.uncertParameters:
            if uncertParameter.type in [
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
                up_p: libsbml.UncertParameter = (
                    uncertainty.createUncertParameter()
                )  # type: ignore
                up_p.setType(uncertParameter.type)
                if uncertParameter.value is not None:
                    up_p.setValue(uncertParameter.value)
                if uncertParameter.var is not None:
                    up_p.setValue(uncertParameter.var)
                if uncertParameter.unit:
                    up_p.setUnits(Unit.get_unit_string(uncertParameter.unit))
            else:
                logger.error(
                    f"Unsupported type for UncertParameter: "
                    f"'{uncertParameter.type}' in '{uncertParameter}'."
                )

        # create a distribution uncertainty
        if self.formula:
            model = sbase.getModel()
            up_dist: libsbml.UncertParameter = uncertainty.createUncertParameter()
            up_dist.setType(libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)
            for key in [
                "normal",
                "uniform",
                "bernoulli",
                "binomial",
                "cauchy",
                "chisquare",
                "exponential",
                "gamma",
                "laplace",
                "lognormal",
                "poisson",
                "raleigh",
            ]:
                if key in self.formula:
                    up_dist.setDefinitionURL(
                        "http://www.sbml.org/sbml/symbols/distrib/{}".format(key)
                    )
                    ast = libsbml.parseL3FormulaWithModel(self.formula, model)
                    if ast is None:
                        logger.error(libsbml.getLastParseL3Error())
                    else:
                        check(up_dist.setMath(ast), "set math in distrib formula")

        return uncertainty


"""
---------------------------------------------------------------------------------------
fbc information
---------------------------------------------------------------------------------------
"""


class ExchangeReaction(Reaction):
    """Exchange reactions define substances which can be exchanged.

     This is important for FBC models.

     EXCHANGE_IMPORT (-INF, 0): is defined as negative flux through the exchange
     reaction, i.e. the upper bound must be 0, the lower bound some negative value,
        e.g. -INF

    EXCHANGE_EXPORT (0, INF): is defined as positive flux through the exchange reaction,
        i.e. the lower bound must be 0, the upper bound some positive value,
        e.g. INF
    """

    PREFIX = "EX_"

    def __init__(
        self,
        species_id: str,
        compartment: str = None,
        fast: bool = False,
        reversible: bool = None,
        lowerFluxBound: str = None,
        upperFluxBound: str = None,
        name: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(ExchangeReaction, self).__init__(
            sid=ExchangeReaction.PREFIX + species_id,
            equation="{} ->".format(species_id),
            sboTerm=SBO.EXCHANGE_REACTION,
            name=name,
            compartment=compartment,
            fast=fast,
            reversible=reversible,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            lowerFluxBound=lowerFluxBound,
            upperFluxBound=upperFluxBound,
            uncertainties=uncertainties,
            port=port,
            replacedBy=replacedBy,
        )


class Constraint(Sbase):
    """Constraint.

    The Constraint object is a mechanism for stating the assumptions under which a model is designed to operate.
    The constraints are statements about permissible values of different quantities in a model.

    The message must be well formated XHTML, e.g.,
        message='<body xmlns="http://www.w3.org/1999/xhtml">ATP must be non-negative</body>'
    """

    def __init__(
        self,
        sid: str,
        math: str,
        message: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(Constraint, self).__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.math = math
        self.message = message

    def create_sbml(self, model: libsbml.Model) -> libsbml.Constraint:
        """Create Constraint SBML in model."""
        constraint: libsbml.Constraint = model.createConstraint()
        self._set_fields(constraint, model)
        return constraint

    def _set_fields(self, obj: libsbml.Constraint, model: libsbml.Model) -> None:
        """Set fields on libsbml.Constraint."""
        super(Constraint, self)._set_fields(obj, model)

        if self.math is not None:
            ast_math = libsbml.parseL3FormulaWithModel(self.math, model)
            obj.setMath(ast_math)
        if self.message is not None:
            check(
                obj.setMessage(self.message),
                message=f"Setting message on constraint: '{self.message}'",
            )


class Objective(Sbase):
    """Objective."""

    objective_types = [
        libsbml.OBJECTIVE_TYPE_MAXIMIZE,
        libsbml.OBJECTIVE_TYPE_MINIMIZE,
        "maximize",
        "minimize",
        "max",
        "min",
    ]

    def __init__(
        self,
        sid: str,
        objectiveType: str = libsbml.OBJECTIVE_TYPE_MAXIMIZE,
        active: bool = True,
        fluxObjectives: Optional[Dict[str, float]] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[Union[str, Notes]] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        """Create an Objective."""
        super(Objective, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.objectiveType = objectiveType
        self.active = active
        self.fluxObjectives = fluxObjectives if fluxObjectives else {}

        if self.objectiveType not in Objective.objective_types:
            raise ValueError(
                f"Unsupported objective type '{objectiveType}'. Supported are "
                f"{Objective.objective_types}"
            )
        else:
            if self.objectiveType in {"min", "minimize"}:
                self.objectiveType = libsbml.OBJECTIVE_TYPE_MINIMIZE
            elif self.objectiveType in {"max", "maximize"}:
                self.objectiveType = libsbml.OBJECTIVE_TYPE_MAXIMIZE

    def create_sbml(self, model: libsbml.Model) -> libsbml.Objective:
        """Create Objective."""
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        obj: libsbml.Objective = model_fbc.createObjective()
        obj.setId(self.sid)
        obj.setType(self.objectiveType)

        if self.active:
            model_fbc.setActiveObjectiveId(self.sid)
        for rid, coefficient in self.fluxObjectives.items():
            # FIXME: check for rid
            fluxObjective: libsbml.FluxObjective = obj.createFluxObjective()
            fluxObjective.setReaction(rid)
            fluxObjective.setCoefficient(coefficient)

        self._set_fields(obj, model)
        return obj

    def _set_fields(self, obj: libsbml.Objective, model: libsbml.Model) -> None:
        """Set fields in libsbml.Objective."""
        super(Objective, self)._set_fields(obj, model)


@deprecated
def create_objective(
    model_fbc: libsbml.FbcModelPlugin,
    oid: str,
    otype: str,
    fluxObjectives: Dict[str, float],
    active: bool = True,
) -> libsbml.Objective:
    """Create flux optimization objective.

    Helper function which will be removed in future releases.
    Directly add the Objective to the list of objects instead.
    """
    objective: libsbml.Objective = model_fbc.createObjective()
    objective.setId(oid)
    objective.setType(otype)
    if active:
        model_fbc.setActiveObjectiveId(oid)
    for rid, coefficient in fluxObjectives.items():
        flux_objective = objective.createFluxObjective()
        flux_objective.setReaction(rid)
        flux_objective.setCoefficient(coefficient)

    return objective


class ModelDefinition(Sbase):
    """ModelDefinition."""

    def __init__(
        self,
        sid: str,
        name: str = None,
        sboTerm: str = None,
        metaId: str = None,
        units: List[Unit] = None,
        compartments: List[Compartment] = None,
        species: List[Species] = None,
    ):
        """Create a ModelDefinition."""
        super(ModelDefinition, self).__init__(
            sid=sid, name=name, sboTerm=sboTerm, metaId=metaId
        )
        self.units = units
        self.compartments = compartments
        self.species = species

    def create_sbml(self, model: libsbml.Model) -> libsbml.ModelDefinition:
        """Create ModelDefinition."""
        doc: libsbml.SBMLDocument = model.getSBMLDocument()
        doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
        model_definition: libsbml.ModelDefinition = doc_comp.createModelDefinition()
        self._set_fields(model_definition, model)
        return model_definition

    def _set_fields(self, obj: libsbml.ModelDefinition, model: libsbml.Model) -> None:
        """Set fields on ModelDefinition."""
        super(ModelDefinition, self)._set_fields(obj, model)
        for attr in [
            "externalModelDefinitions",
            "modelDefinitions",
            "submodels",
            "units",
            "functions",
            "parameters",
            "compartments",
            "species",
            "assignments",
            "rules",
            "rate_rules",
            "reactions",
            "events",
            "constraints",
            "ports",
            "replacedElements",
            "deletions",
            "objectives",
            "layouts",
        ]:
            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                if objects:
                    create_objects(obj, obj_iter=objects, key=attr)
                else:
                    logger.debug(f"Not defined: <{attr}>")


class ExternalModelDefinition(Sbase):
    """ExternalModelDefinition."""

    def __init__(
        self,
        sid: str,
        source: str,
        modelRef: str,
        md5: str = None,
        name: str = None,
        sboTerm: str = None,
        metaId: str = None,
    ):
        """Create an ExternalModelDefinition."""
        super(ExternalModelDefinition, self).__init__(
            sid=sid, name=name, sboTerm=sboTerm, metaId=metaId
        )
        self.source = source
        self.modelRef = modelRef
        self.md5 = md5

    def create_sbml(self, model: libsbml.Model) -> libsbml.ExternalModelDefinition:
        """Create ExternalModelDefinition."""
        doc = model.getSBMLDocument()
        cdoc = doc.getPlugin("comp")
        extdef = cdoc.createExternalModelDefinition()
        self._set_fields(extdef, model)
        return extdef

    def _set_fields(
        self, obj: libsbml.ExternalModelDefinition, model: libsbml.Model
    ) -> None:
        """Set fields on ExternalModelDefinition."""
        super(ExternalModelDefinition, self)._set_fields(obj, model)
        obj.setModelRef(self.modelRef)
        obj.setSource(self.source)
        if self.md5 is not None:
            obj.setMd5(self.md5)


class Submodel(Sbase):
    """Submodel."""

    def __init__(
        self,
        sid: str,
        modelRef: str = None,
        timeConversionFactor: str = None,
        extentConversionFactor: str = None,
        name: str = None,
        sboTerm: str = None,
        metaId: str = None,
    ):
        """Create a Submodel."""
        super(Submodel, self).__init__(
            sid=sid, name=name, sboTerm=sboTerm, metaId=metaId
        )
        self.modelRef = modelRef
        self.timeConversionFactor = timeConversionFactor
        self.extentConversionFactor = extentConversionFactor

    def create_sbml(self, model: libsbml.Model) -> libsbml.Submodel:
        """Create SBML Submodel."""
        cmodel = model.getPlugin("comp")
        submodel = cmodel.createSubmodel()
        self._set_fields(submodel, model)

        submodel.setModelRef(self.modelRef)
        if self.timeConversionFactor:
            submodel.setTimeConversionFactor(self.timeConversionFactor)
        if self.extentConversionFactor:
            submodel.setExtentConversionFactor(self.extentConversionFactor)

        return submodel

    def _set_fields(self, obj: libsbml.Submodel, model: libsbml.Model) -> None:
        super(Submodel, self)._set_fields(obj, model)


class SbaseRef(Sbase):
    """SBaseRef."""

    def __init__(
        self,
        sid: str,
        portRef: Optional[str] = None,
        idRef: Optional[str] = None,
        unitRef: Optional[str] = None,
        metaIdRef: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        """Create an SBaseRef."""
        super(SbaseRef, self).__init__(
            sid=sid, name=name, sboTerm=sboTerm, metaId=metaId
        )
        self.portRef = portRef
        self.idRef = idRef
        self.unitRef = unitRef
        self.metaIdRef = metaIdRef

    def _set_fields(self, obj: libsbml.SBaseRef, model: libsbml.Model) -> None:
        super(SbaseRef, self)._set_fields(obj, model)

        obj.setId(self.sid)
        if self.portRef is not None:
            obj.setPortRef(self.portRef)
        if self.idRef is not None:
            obj.setIdRef(self.idRef)
        if self.unitRef is not None:
            unit_str = Unit.get_unit_string(self.unitRef)
            obj.setUnitRef(unit_str)
        if self.metaIdRef is not None:
            obj.setMetaIdRef(self.metaIdRef)


class ReplacedElement(SbaseRef):
    """ReplacedElement."""

    def __init__(
        self,
        sid: str,
        elementRef: str,
        submodelRef: str,
        deletion: Optional[str] = None,
        conversionFactor: Optional[str] = None,
        portRef: Optional[str] = None,
        idRef: Optional[str] = None,
        unitRef: Optional[str] = None,
        metaIdRef: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        """Create a ReplacedElement."""
        super(ReplacedElement, self).__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
        )
        self.elementRef = elementRef
        self.submodelRef = submodelRef
        self.deletion = deletion
        self.conversionFactor = conversionFactor

    def create_sbml(self, model: libsbml.Model) -> libsbml.ReplacedElement:
        """Create SBML ReplacedElement."""
        # resolve port element
        e = model.getElementBySId(self.elementRef)
        if not e:
            # fallback to units (only working if no name shadowing)
            e = model.getUnitDefinition(self.elementRef)
            if not e:
                raise ValueError(
                    f"Neither SBML element nor UnitDefinition found for elementRef: "
                    f"'{self.elementRef}' in '{self}'"
                )

        eplugin = e.getPlugin("comp")
        obj = eplugin.createReplacedElement()
        self._set_fields(obj, model)

        return obj

    def _set_fields(self, obj: libsbml.ReplacedElement, model: libsbml.Model) -> None:
        super(ReplacedElement, self)._set_fields(obj, model)
        obj.setSubmodelRef(self.submodelRef)
        if self.deletion:
            obj.setDeletion(self.deletion)
        if self.conversionFactor:
            obj.setConversionFactor(self.conversionFactor)


class ReplacedBy(SbaseRef):
    """ReplacedBy."""

    def __init__(
        self,
        sid: str,
        elementRef: str,
        submodelRef: str,
        portRef: Optional[str] = None,
        idRef: Optional[str] = None,
        unitRef: Optional[str] = None,
        metaIdRef: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        """Create a ReplacedElement."""
        super(ReplacedBy, self).__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
        )
        self.elementRef = elementRef
        self.submodelRef = submodelRef

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.ReplacedBy:
        """Create SBML ReplacedBy."""
        sbase_comp: libsbml.CompSBasePlugin = sbase.getPlugin("comp")
        rby: libsbml.ReplacedBy = sbase_comp.createReplacedBy()
        self._set_fields(rby, model)

        return rby

    def _set_fields(self, rby: libsbml.ReplacedBy, model: libsbml.Model) -> None:
        """Set fields in ReplacedBy."""
        super(ReplacedBy, self)._set_fields(rby, model)
        rby.setSubmodelRef(self.submodelRef)


class Deletion(SbaseRef):
    """Deletion."""

    def __init__(
        self,
        sid: str,
        submodelRef: str,
        portRef: Optional[str] = None,
        idRef: Optional[str] = None,
        unitRef: Optional[str] = None,
        metaIdRef: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        """Initialize Deletion."""
        super(Deletion, self).__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
        )
        self.submodelRef = submodelRef

    def create_sbml(self, model: libsbml.Model) -> libsbml.Deletion:
        """Create SBML Deletion."""
        cmodel: libsbml.CompModelPlugin = model.getPlugin("comp")
        submodel: libsbml.Submodel = cmodel.getSubmodel(self.submodelRef)
        deletion: libsbml.Deletion = submodel.createDeletion()
        self._set_fields(deletion, model)

        return deletion

    def _set_fields(self, obj: libsbml.Deletion, model: libsbml.Model) -> None:
        """Set fields on Deletion."""
        super(Deletion, self)._set_fields(obj, model)


##########################################################################
# Ports
##########################################################################
# Ports are stored in an optional child ListOfPorts object, which, if
# present, must contain one or more Port objects.  All of the Ports
# present in the ListOfPorts collectively define the 'port interface' of
# the Model.
PORT_TYPE_PORT = "port"
PORT_TYPE_INPUT = "input port"
PORT_TYPE_OUTPUT = "output port"


class Port(SbaseRef):
    """Port."""

    def __init__(
        self,
        sid: str,
        portRef: Optional[str] = None,
        idRef: Optional[str] = None,
        unitRef: Optional[str] = None,
        metaIdRef: Optional[str] = None,
        portType: Optional[str] = PORT_TYPE_PORT,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        """Create a Port."""
        super(Port, self).__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
        )
        self.portType = portType

    def create_sbml(self, model: libsbml.Model) -> libsbml.Port:
        """Create SBML for Port."""
        cmodel = model.getPlugin("comp")
        p = cmodel.createPort()
        self._set_fields(p, model)

        if self.sboTerm is None:
            if self.portType == PORT_TYPE_PORT:
                # SBO:0000599 - port
                sbo = 599
            elif self.portType == PORT_TYPE_INPUT:
                # SBO:0000600 - input port
                sbo = 600
            elif self.portType == PORT_TYPE_OUTPUT:
                # SBO:0000601 - output port
                sbo = 601
            p.setSBOTerm(sbo)

        return p

    def _set_fields(self, obj: libsbml.Port, model: libsbml.Model) -> None:
        """Set fields on Port."""
        super(Port, self)._set_fields(obj, model)
