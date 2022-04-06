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
import datetime
import inspect
import json
import shutil
import tempfile
from collections import namedtuple
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type, Union

import libsbml
import numpy as np
import xmltodict  # type: ignore
from numpy import NaN
from pint import UndefinedUnitError, UnitRegistry
from pydantic import BaseModel
from pymetadata.core.creator import Creator

from sbmlutils.console import console
from sbmlutils.equation import Equation
from sbmlutils.io import write_sbml
from sbmlutils.log import get_logger
from sbmlutils.metadata import *
from sbmlutils.metadata import annotator
from sbmlutils.metadata.annotator import Annotation
from sbmlutils.notes import Notes, NotesFormat
from sbmlutils.report import sbmlreport
from sbmlutils.utils import FrozenClass, create_metaid, deprecated
from sbmlutils.validation import check


try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


logger = get_logger(__name__)

ureg = UnitRegistry()
Q_ = ureg.Quantity
ureg.define("item = 1 dimensionless")

# FIXME: make complete import of all DISTRIB constants

__all__ = [
    "SBML_LEVEL",
    "SBML_VERSION",
    "PORT_SUFFIX",
    "PORT_UNIT_SUFFIX",
    "ModelUnits",
    "Units",
    "Creator",
    "Compartment",
    "UnitDefinition",
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
    "ModelDict",
    "Model",
    "Document",
    "FactoryResult",
    "create_model",
    "UnitType",
    "NaN",
]


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
    model: libsbml.Model, obj_iter: List[Any], key: str = None
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


UnitType = Optional["UnitDefinition"]
AnnotationsType = Optional[List[Union[Annotation, Tuple[Union[BQB, BQM], str]]]]

PortType = Any  # Union[bool, Port]


def set_notes(
    sbase: libsbml.SBase, notes: str, format: NotesFormat = NotesFormat.MARKDOWN
) -> None:
    """Set notes information on SBase.

    :param sbase: SBase
    :param notes: notes information (xml string)
    :return:
    """
    _notes = Notes(notes, format=format)
    check(sbase.setNotes(_notes.xml), message=f"Setting notes on '{sbase}'")


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
                    msg = f"'{key}' should be set in 'model_units'."
                    if key in ["time", "extent", "substance", "volume"]:
                        # strongly recommended fields
                        logger.warning(msg)
                    else:
                        # optional fields
                        logger.info(msg)

                    continue

                unit: Union[str, UnitDefinition] = getattr(model_units, key)
                uid = UnitDefinition.get_uid_for_unit(unit=unit)
                # set the values
                if key == "time":
                    model.setTimeUnits(uid)
                elif key == "extent":
                    model.setExtentUnits(uid)
                elif key == "substance":
                    model.setSubstanceUnits(uid)
                elif key == "length":
                    model.setLengthUnits(uid)
                elif key == "area":
                    model.setAreaUnits(uid)
                elif key == "volume":
                    model.setVolumeUnits(uid)


def date_now() -> libsbml.Date:
    """Get current time stamp for history.

    :return: current libsbml Date
    """
    time = datetime.datetime.now()
    timestr = time.strftime("%Y-%m-%dT%H:%M:%S")
    return libsbml.Date(timestr)


def set_model_history(sbase: libsbml.SBase, creators: List[Creator]) -> None:
    """Set the model history from given creators.

    :param sbase: SBML model
    :param creators: list of creators
    :return:
    """
    if not sbase.isSetMetaId():
        sbase.setMetaId(create_metaid(sbase=sbase))

    # create and set model history
    h = _create_history(creators)
    check(sbase.setModelHistory(h), "set model history")


def _create_history(
    creators: List[Creator], set_timestamps: bool = False
) -> libsbml.ModelHistory:
    """Create the model history.

    Sets the create and modified date to the current time.
    Creators are a list or dictionary with values as

    :param creators:
    :param set_timestamps:
    :return:
    """
    h = libsbml.ModelHistory()

    for creator in creators:
        c = libsbml.ModelCreator()
        if creator.familyName:
            c.setFamilyName(creator.familyName)
        if creator.givenName:
            c.setGivenName(creator.givenName)
        if creator.email:
            c.setEmail(creator.email)
        if creator.organization:
            c.setOrganization(creator.organization)
        check(h.addCreator(c), "add creator")

    # create time is now
    if set_timestamps:
        datetime = date_now()
        check(h.setCreatedDate(datetime), "set creation date")
        check(h.setModifiedDate(datetime), "set modified date")
    else:
        datetime = libsbml.Date("1900-01-01T00:00:00")
        check(h.setCreatedDate(datetime), "set creation date")
        check(h.setModifiedDate(datetime), "set modified date")

    return h


class Sbase:
    """Base class of all SBML objects."""

    def __init__(
        self,
        sid: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
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
        info: str = ""
        if self.sid and not self.name:
            info = f" {self.sid}"
        elif self.sid and self.name:
            info = f" {self.sid}|{self.name}"
        elif not self.sid and self.name:
            info = f" {self.name}"

        return f"<{class_name}{info}>"

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

    def get_notes_xml(self) -> Optional[str]:
        """Get notes xml string."""
        if self.notes:
            notes_str: Optional[str] = str(Notes(self.notes).xml)
            return notes_str

        return None

    def _set_fields(self, obj: libsbml.SBase, model: Optional[libsbml.Model]) -> None:
        if self.sid is not None:
            if not libsbml.SyntaxChecker.isValidSBMLSId(self.sid):
                logger.error(
                    f"The id `{self.sid}` is not a valid SBML SId on `{obj}`. "
                    f"The SId syntax is defined as:"
                    f"\tletter ::= 'a'..'z','A'..'Z'"
                    f"\tdigit  ::= '0'..'9'"
                    f"\tidChar ::= letter | digit | '_'"
                    f"\tSId    ::= ( letter | '_' ) idChar*"
                )
            obj.setId(self.sid)
        if self.name is not None:
            obj.setName(self.name)
        else:
            if not isinstance(
                self, (Document, Port, ReplacedBy, ReplacedElement, AssignmentRule)
            ):
                logger.warning(f"'name' should be set on '{self}'")
        if self.sboTerm is not None:
            if isinstance(self.sboTerm, SBO):
                sbo = self.sboTerm.value.replace("_", ":")
            elif isinstance(self.sboTerm, str):
                sbo = self.sboTerm.replace("_", ":")
            else:
                sbo = self.sboTerm
            obj.setSBOTerm(sbo)
        else:
            if not isinstance(
                self,
                (
                    Document,
                    Port,
                    UnitDefinition,
                    Model,
                    ReplacedBy,
                    ReplacedElement,
                    AssignmentRule,
                    RateRule,
                    ExternalModelDefinition,
                    Submodel,
                ),
            ):
                logger.warning(f"'sboTerm' should be set on '{self}'")
        if self.metaId is not None:
            obj.setMetaId(self.metaId)

        if self.notes is not None and self.notes.strip():
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
            annotator.ModelAnnotator.annotate_sbase(sbase=obj, annotation=annotation)

        if model:
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
                if isinstance(self, UnitDefinition):
                    port_sid = f"{self.sid}{PORT_UNIT_SUFFIX}"
                else:
                    port_sid = f"{self.sid}{PORT_SUFFIX}"
                p.setId(port_sid)
                p.setName(f"Port of {self.sid}")
                p.setMetaId(port_sid)
                sbo = SBO.PORT.value.replace("_", ":")
                p.setSBOTerm(sbo)

                if isinstance(self, UnitDefinition):
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
        notes: Optional[str] = None,
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


class UnitDefinition(Sbase):
    """Unit.

    Corresponds to the information in the libsbml.UnitDefinition.
    """

    pint2sbml = {
        "dimensionless": libsbml.UNIT_KIND_DIMENSIONLESS,
        "ampere": libsbml.UNIT_KIND_AMPERE,
        # None: libsbml.UNIT_KIND_BECQUEREL,
        # "becquerel": libsbml.UNIT_KIND_BECQUEREL,
        "candela": libsbml.UNIT_KIND_CANDELA,
        "degree_Celsius": libsbml.UNIT_KIND_CELSIUS,
        "coulomb": libsbml.UNIT_KIND_COULOMB,
        "farad": libsbml.UNIT_KIND_FARAD,
        "gram": libsbml.UNIT_KIND_GRAM,
        "gray": libsbml.UNIT_KIND_GRAY,
        "hertz": libsbml.UNIT_KIND_HERTZ,
        "item": libsbml.UNIT_KIND_ITEM,
        "kelvin": libsbml.UNIT_KIND_KELVIN,
        "kilogram": libsbml.UNIT_KIND_KILOGRAM,
        "liter": libsbml.UNIT_KIND_LITRE,
        "meter": libsbml.UNIT_KIND_METRE,
        "mole": libsbml.UNIT_KIND_MOLE,
        "newton": libsbml.UNIT_KIND_NEWTON,
        "ohm": libsbml.UNIT_KIND_OHM,
        "second": libsbml.UNIT_KIND_SECOND,
        "volt": libsbml.UNIT_KIND_VOLT,
    }
    # see https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
    prefixes = {
        "yocto": 1e-24,
        "zepto": 1e-21,
        "atto": 1e-18,
        "femto": 1e-15,
        "pico": 1e-12,
        "nano": 1e-9,
        "micro": 1e-6,
        "milli": 1e-3,
        "centi": 1e-2,
        "deci": 1e-1,
        "deca": 1e1,
        "hecto": 1e2,
        "kilo": 1e3,
        "mega": 1e6,
        "giga": 1e9,
        "tera": 1e12,
        "peta": 1e15,
        "exa": 1e18,
        "zetta": 1e21,
        "yotta": 1e24,
    }

    def __init__(
        self,
        sid: str,
        definition: str = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
        port: Any = None,
        uncertainties: Optional[List["Uncertainty"]] = None,
        replacedBy: Optional[Any] = None,
    ):
        super(UnitDefinition, self).__init__(
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

        self.definition = definition if definition is not None else sid
        if not self.name:
            self.name = self.definition

    def create_sbml(self, model: libsbml.Model) -> Optional[libsbml.UnitDefinition]:
        """Create libsbml.UnitDefinition."""
        if isinstance(self.definition, int):
            # libsbml unit type
            return None

        obj: libsbml.UnitDefinition = model.createUnitDefinition()

        # parse the string into pint
        # quantity = Q_(self.definition).to_compact().to_reduced_units().to_base_units()
        # quantity = Q_(self.definition).to_base_units()
        quantity = Q_(self.definition)
        magnitude, units = quantity.to_tuple()
        # console.log(magnitude, units)

        if units:
            for k, item in enumerate(units):
                # console.rule()
                # console.log(item)
                prefix, unit_name, suffix = ureg.parse_unit_name(item[0])[0]
                exponent = item[1]
                # first unit gets the multiplier
                multiplier = 1.0
                if k == 0:
                    multiplier = magnitude

                if prefix:
                    multiplier = multiplier * self.__class__.prefixes[prefix]

                multiplier = np.power(multiplier, 1 / abs(exponent))

                scale = 0
                # resolve the kind (this is already a unit known by libsbml)
                kind = self.__class__.pint2sbml.get(unit_name, None)
                if kind is None:
                    # we have to bring the unit to base units
                    uq = Q_(unit_name).to_base_units()
                    # console.log("uq:", uq)
                    multiplier = multiplier * uq.magnitude
                    kind = self.__class__.pint2sbml.get(str(uq.units), None)
                    if kind is None:
                        msg = (
                            f"Unit '{uq.units}' in definition "
                            f"'{self.definition}' could not be converted to SBML."
                        )
                        logger.error(msg)
                        raise ValueError(msg)

                # console.log(f"({multiplier} * 10^{scale} {libsbml.UnitKind_toString(kind)})^{exponent}")
                self._create_unit(obj, kind, exponent, scale, multiplier)
        else:
            # only magnitude (units canceled)
            kind = self.__class__.pint2sbml["dimensionless"]
            self._create_unit(obj, kind, 1.0, 0, magnitude)

        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    def _set_fields(self, obj: libsbml.UnitDefinition, model: libsbml.Model) -> None:
        """Set fields on libsbml.UnitDefinition."""
        super(UnitDefinition, self)._set_fields(obj, model)

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
        # print(f"({multiplier} * 10^{scale} {libsbml.UnitKind_toString(kind)})^exponent")
        return unit

    @staticmethod
    def get_uid_for_unit(unit: Union["UnitDefinition", str]) -> Optional[str]:
        """Get unit id for given definition string."""
        uid: Optional[str]
        if unit is None:
            uid = None
        elif isinstance(unit, UnitDefinition):
            uid = unit.sid
        else:
            raise ValueError(
                f"unit must be a 'UnitDefinition', but '{unit}' is "
                f"'{type(unit)}. Best practise is to use a `class U(Units)` for "
                f"units definitions."
            )
        return uid


class Units:
    """Base class for unit definitions."""

    # libsbml units
    dimensionless = UnitDefinition(
        "dimensionless", libsbml.UNIT_KIND_DIMENSIONLESS, name="dimensionless"
    )
    ampere = UnitDefinition("ampere", libsbml.UNIT_KIND_AMPERE, name="ampere")
    becquerel = UnitDefinition(
        "becquerel", libsbml.UNIT_KIND_BECQUEREL, name="becquerel"
    )
    candela = UnitDefinition("candela", libsbml.UNIT_KIND_CANDELA, name="candela")
    degree_Celsius = UnitDefinition(
        "degree_Celsius", libsbml.UNIT_KIND_CELSIUS, name="degree_Celsius"
    )
    coulomb = UnitDefinition("coulomb", libsbml.UNIT_KIND_COULOMB, name="coulomb")
    farad = UnitDefinition("farad", libsbml.UNIT_KIND_FARAD, name="farad")
    gram = UnitDefinition("gram", libsbml.UNIT_KIND_GRAM, name="gram")
    gray = UnitDefinition("gray", libsbml.UNIT_KIND_GRAY, name="gray")
    hertz = UnitDefinition("hertz", libsbml.UNIT_KIND_HERTZ, name="hertz")
    item = UnitDefinition("item", libsbml.UNIT_KIND_ITEM, name="item")
    kelvin = UnitDefinition("kelvin", libsbml.UNIT_KIND_KELVIN, name="kelvin")
    kilogram = UnitDefinition("kilogram", libsbml.UNIT_KIND_KILOGRAM, name="kilogram")
    liter = UnitDefinition("litre", libsbml.UNIT_KIND_LITRE, name="liter")
    litre = UnitDefinition("litre", libsbml.UNIT_KIND_LITRE, name="liter")
    meter = UnitDefinition("metre", libsbml.UNIT_KIND_METRE, name="meter")
    metre = UnitDefinition("metre", libsbml.UNIT_KIND_METRE, name="metre")
    mole = UnitDefinition("mole", libsbml.UNIT_KIND_MOLE, name="mole")
    newton = UnitDefinition("newton", libsbml.UNIT_KIND_NEWTON, name="newton")
    ohm = UnitDefinition("ohm", libsbml.UNIT_KIND_OHM, name="ohm")
    second = UnitDefinition("second", libsbml.UNIT_KIND_SECOND, name="second")
    volt = UnitDefinition("volt", libsbml.UNIT_KIND_VOLT, name="volt")

    @classmethod
    def attributes(cls) -> List[Tuple[str, Union[str, "UnitDefinition"]]]:
        """Get the attributes list."""
        attributes = inspect.getmembers(cls, lambda a: not (inspect.isroutine(a)))
        return [
            a for a in attributes if not (a[0].startswith("__") and a[0].endswith("__"))
        ]

    @classmethod
    def create_unit_definitions(cls, model: libsbml.Model) -> None:
        """Create the libsbml.UnitDefinitions in the model."""

        unit_definition: UnitDefinition
        uid: str
        for uid, definition in cls.attributes():
            if isinstance(definition, str):
                unit_definition = UnitDefinition(sid=uid, definition=definition)
            elif isinstance(definition, UnitDefinition):
                unit_definition = definition
            else:
                raise ValueError(
                    f"Units attributes must be a unit string or UnitDefinition, "
                    f"but '{type(definition)} for '{definition}'."
                )
            # create and register libsbml.UnitDefinition in libsbml.Model
            # print("Create:", uid)
            try:
                _: libsbml.UnitDefinition = unit_definition.create_sbml(model=model)
            except UndefinedUnitError as err:
                console.print_exception(show_locals=False)
                logger.error(
                    f"Unit definition '{unit_definition.definition}' is not valid "
                    f"pint syntax, {err}."
                )
                raise err


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
        unit: UnitType = Units.dimensionless,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
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
        if self.unit and not isinstance(self.unit, UnitDefinition):
            logger.warning(
                f"'unit' must be of type UnitDefinition, but '{self.unit}' "
                f"in '{self}' is '{type(self.unit)}'."
            )

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
                uid = UnitDefinition.get_uid_for_unit(unit=self.unit)
                check(obj.setUnits(uid), f"Set unit '{uid}' on {obj}")


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
        notes: Optional[str] = None,
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
        notes: Optional[str] = None,
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
        notes: Optional[str] = None,
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
        notes: Optional[str] = None,
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
        self.substanceUnits = substanceUnit
        self.initialAmount = initialAmount
        self.initialConcentration = initialConcentration
        self.compartment = compartment
        self.constant = constant
        self.boundaryCondition = boundaryCondition
        self.hasOnlySubstanceUnits = hasOnlySubstanceUnits
        self.charge = charge
        self.chemicalFormula = chemicalFormula
        self.conversionFactor = conversionFactor

    def create_sbml(self, model: libsbml.Model) -> libsbml.Species:
        """Create Species SBML in model."""
        s: libsbml.Species = model.createSpecies()
        self._set_fields(s, model)
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

        obj.setSubstanceUnits(model.getSubstanceUnits())
        if self.substanceUnits is not None:
            obj.setSubstanceUnits(
                UnitDefinition.get_uid_for_unit(unit=self.substanceUnits)
            )
        else:
            # Fallback to model units
            obj.setSubstanceUnits(model.getSubstanceUnits())

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
        unit: UnitType = Units.dimensionless,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
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
                sid,
                unit=rule.unit,
                name=rule.name,
                value=value,
                constant=False,
                # sboTerm=rule.sboTerm : FIXME not working due to duplicate meta ids
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
        notes: Optional[str] = None,
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
        # else:
        #    logger.info(f"'compartment' should be set on '{self}'}")
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
        notes: Optional[str] = None,
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
        notes: Optional[str] = None,
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
                    up_span.setUnits(
                        UnitDefinition.get_uid_for_unit(unit=uncertSpan.unit)
                    )
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
                    up_p.setUnits(
                        UnitDefinition.get_uid_for_unit(unit=uncertParameter.unit)
                    )
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
        notes: Optional[str] = None,
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
        notes: Optional[str] = None,
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
        notes: Optional[str] = None,
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

    # FIXME: handle as model

    def __init__(
        self,
        sid: str,
        name: str = None,
        sboTerm: str = None,
        metaId: str = None,
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
        units: Optional[Type[Units]] = None,
        compartments: Optional[List[Compartment]] = None,
        species: Optional[List[Species]] = None,
    ):
        """Create a ModelDefinition."""
        super(ModelDefinition, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
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
            # "units",
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
            # create units
            # FIXME:
            # if hasattr(self, "units"):
            #     self.units.create_unit_definitions(obj)

            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                if objects:
                    create_objects(obj, obj_iter=objects, key=attr)


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
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
    ):
        """Create an ExternalModelDefinition."""
        super(ExternalModelDefinition, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
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
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
    ):
        """Create a Submodel."""
        super(Submodel, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
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
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
    ):
        """Create an SBaseRef."""
        super(SbaseRef, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
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
            unit_str = UnitDefinition.get_uid_for_unit(unit=self.unitRef)
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
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
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
            annotations=annotations,
            notes=notes,
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
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
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
            annotations=annotations,
            notes=notes,
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
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
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
            annotations=annotations,
            notes=notes,
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
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
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
            annotations=annotations,
            notes=notes,
        )
        self.portType = portType

    def create_sbml(self, model: libsbml.Model) -> libsbml.Port:
        """Create SBML for Port."""
        cmodel = model.getPlugin("comp")
        p = cmodel.createPort()
        self._set_fields(p, model)

        if self.sboTerm is None:
            if self.portType == PORT_TYPE_PORT:
                sbo = SBO.PORT
            elif self.portType == PORT_TYPE_INPUT:
                sbo = SBO.INPUT_PORT
            elif self.portType == PORT_TYPE_OUTPUT:
                sbo = SBO.OUTPUT_PORT
            p.setSBOTerm(sbo.value.replace("_", ":"))

        return p

    def _set_fields(self, obj: libsbml.Port, model: libsbml.Model) -> None:
        """Set fields on Port."""
        super(Port, self)._set_fields(obj, model)


class ModelDict(TypedDict, total=False):
    """ModelDict.

    The ModelDict allows to define the Model as dictionary and then
    use:

      md: ModelDict
      Model(**md)

    For model construction. If possible use the Model object directly.
    """

    sid: str
    name: Optional[str]
    sboTerm: Optional[str]
    metaId: Optional[str]
    annotations: AnnotationsType
    notes: Optional[str]
    packages: Optional[List[str]]
    creators: Optional[List[Creator]]
    model_units: Optional[ModelUnits]
    objects: Optional[List[Sbase]]
    external_model_definitions: Optional[List[ExternalModelDefinition]]
    model_definitions: Optional[List[ModelDefinition]]
    submodels: Optional[List[Submodel]]
    units: Optional[Type[Units]]
    functions: Optional[List[Function]]
    compartments: Optional[List[Compartment]]
    species: Optional[List[Species]]
    parameters: Optional[List[Parameter]]
    assignments: Optional[List[InitialAssignment]]
    rules: Optional[List[Rule]]
    rate_rules: Optional[List[RateRule]]
    reactions: Optional[List[Reaction]]
    events: Optional[List[Event]]
    constraints: Optional[List[Constraint]]
    ports: Optional[List[Port]]
    replaced_elements: Optional[List[ReplacedElement]]
    deletions: Optional[List[Deletion]]
    objectives: Optional[List[Objective]]
    layouts: Optional[List]


class Model(Sbase, FrozenClass, BaseModel):
    """Model."""

    sid: str
    name: Optional[str]
    sboTerm: Optional[str]
    metaId: Optional[str]
    annotations: AnnotationsType
    notes: Optional[str]
    port: Optional[PortType]
    packages: Optional[List[str]]
    creators: Optional[List[Creator]]
    model_units: Optional[ModelUnits]
    external_model_definitions: Optional[List[ExternalModelDefinition]]
    model_definitions: Optional[List[ModelDefinition]]
    submodels: Optional[List[Submodel]]
    units: Optional[Type[Units]]
    functions: Optional[List[Function]]
    compartments: Optional[List[Compartment]]
    species: Optional[List[Species]]
    parameters: Optional[List[Parameter]]
    assignments: Optional[List[InitialAssignment]]
    rules: Optional[List[Rule]]
    rate_rules: Optional[List[RateRule]]
    reactions: Optional[List[Reaction]]
    events: Optional[List[Event]]
    constraints: Optional[List[Constraint]]
    ports: Optional[List[Port]]
    replaced_elements: Optional[List[ReplacedElement]]
    deletions: Optional[List[Deletion]]
    objectives: Optional[List[Objective]]
    layouts: Optional[List]

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True

    _keys = {
        "sid": None,
        "name": None,
        "sboTerm": None,
        "metaId": None,
        "annotations": list,
        "notes": None,
        "port": None,
        "packages": list,
        "creators": None,
        "model_units": None,
        "external_model_definitions": list,
        "model_definitions": list,
        "submodels": list,
        "units": None,
        "functions": list,
        "compartments": list,
        "species": list,
        "parameters": list,
        "assignments": list,
        "rules": list,
        "rate_rules": list,
        "reactions": list,
        "events": list,
        "constraints": list,
        "ports": list,
        "replaced_elements": list,
        "deletions": list,
        "objectives": list,
        "layouts": list,
    }

    def get_sbml(self) -> str:
        """Create SBML model."""
        return Document(model=self).get_sbml()

    @staticmethod
    def merge_models(models: List["Model"]) -> "Model":
        """Merge information from multiple models."""
        if isinstance(models, Model):
            return models
        if not models:
            raise ValueError("No models are provided.")
        model = Model("template")
        units_base_classes: List[Type[Units]] = (
            [model.units] if model.units else [Units]
        )
        creators = set()
        for m2 in models:
            for key, value in m2.__dict__.items():
                kind = m2._keys.get(key, None)
                # lists of higher modules are extended
                if kind in [list, tuple]:
                    # create new list
                    if not hasattr(model, key) or getattr(model, key) is None:
                        setattr(model, key, [])
                    # now add elements by copy
                    if getattr(model, key):
                        if value:
                            getattr(model, key).extend(deepcopy(value))
                    else:
                        if value:
                            setattr(model, key, deepcopy(value))

                # units are collected and class created dynamically at the end
                elif key == "units":
                    if m2.units:
                        units_base_classes.append(m2.units)
                elif key == "creators":
                    if m2.creators:
                        for c in m2.creators:
                            creators.add(c)
                # !everything else is overwritten
                else:
                    setattr(model, key, value)

        # Handle merging of units
        attr_dict = {}
        for base_class in units_base_classes:
            for a in base_class.attributes():
                attr_dict[a[0]] = a[1]

        if units_base_classes:
            model.units = type("U", (Units,), attr_dict)

        model.creators = list(creators)

        return model

    def __init__(
        self,
        sid: str,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
        packages: Optional[List[str]] = None,
        creators: Optional[List[Creator]] = None,
        model_units: Optional[ModelUnits] = None,
        units: Optional[Type[Units]] = None,
        objects: Optional[List[Sbase]] = None,
        external_model_definitions: Optional[List[ExternalModelDefinition]] = None,
        model_definitions: Optional[List[ModelDefinition]] = None,
        submodels: Optional[List[Submodel]] = None,
        functions: Optional[List[Function]] = None,
        compartments: Optional[List[Compartment]] = None,
        species: Optional[List[Species]] = None,
        parameters: Optional[List[Parameter]] = None,
        assignments: Optional[List[InitialAssignment]] = None,
        rules: Optional[List[Rule]] = None,
        rate_rules: Optional[List[RateRule]] = None,
        reactions: Optional[List[Reaction]] = None,
        events: Optional[List[Event]] = None,
        constraints: Optional[List[Constraint]] = None,
        ports: Optional[List[Port]] = None,
        replaced_elements: Optional[List[ReplacedElement]] = None,
        deletions: Optional[List[Deletion]] = None,
        objectives: Optional[List[Objective]] = None,
        layouts: Optional[List] = None,
    ):
        super(Model, self).__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
        )

        self.packages = packages
        self.creators = creators
        self.model_units = model_units
        self.units = units if units else Units
        self.units_dict = None
        self.external_model_definitions = external_model_definitions
        self.model_definitions = model_definitions

        self.submodels = submodels if submodels else []
        self.functions = functions if functions else []
        self.compartments = compartments if compartments else []
        self.species = species if species else []
        self.parameters = parameters if parameters else []
        self.assignments = assignments if assignments else []
        self.rules = rules if rules else []
        self.rate_rules = rate_rules if rate_rules else []
        self.reactions = reactions if reactions else []
        self.events = events if events else []
        self.constraints = constraints if constraints else []
        self.ports = ports if ports else []
        self.replaced_elements = replaced_elements if replaced_elements else []
        self.deletions = deletions if deletions else []
        self.objectives = objectives if objectives else []

        self.layouts = layouts

        if objects:
            for sbase in objects:
                if isinstance(sbase, Submodel):
                    self.submodels.append(sbase)
                elif isinstance(sbase, Function):
                    self.functions.append(sbase)
                elif isinstance(sbase, Compartment):
                    self.compartments.append(sbase)
                elif isinstance(sbase, Species):
                    self.species.append(sbase)
                elif isinstance(sbase, Parameter):
                    self.parameters.append(sbase)
                elif isinstance(sbase, InitialAssignment):
                    self.assignments.append(sbase)
                elif isinstance(sbase, AssignmentRule):
                    self.rules.append(sbase)
                elif isinstance(sbase, RateRule):
                    self.rate_rules.append(sbase)
                elif isinstance(sbase, Reaction):
                    self.reactions.append(sbase)
                elif isinstance(sbase, Event):
                    self.events.append(sbase)
                elif isinstance(sbase, Constraint):
                    self.constraints.append(sbase)
                elif isinstance(sbase, Port):
                    self.ports.append(sbase)
                elif isinstance(sbase, ReplacedElement):
                    self.replaced_elements.append(sbase)
                elif isinstance(sbase, Deletion):
                    self.deletions.append(sbase)
                elif isinstance(sbase, Objective):
                    self.objectives.append(sbase)

        self._freeze()  # no new attributes after this point

    def create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.Model:
        """Create Model.

        To create the complete SBMLDocument with the model use:

          doc = Document(model=model).create_sbml()
        """
        model: libsbml.Model = doc.createModel()
        self._set_fields(model, model)

        # history
        if self.creators:
            set_model_history(model, self.creators)

        # units
        if self.units:
            self.units.create_unit_definitions(model=model)

        # model units
        if self.model_units:
            ModelUnits.set_model_units(model, self.model_units)

        # lists ofs
        for attr in [
            "external_model_definitions",
            "model_definitions",
            "submodels",
            # "units",
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
            "replaced_elements",
            "deletions",
            "objectives",
            "layouts",
        ]:
            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                if objects:
                    create_objects(model, obj_iter=objects, key=attr)

        return model


class Document(Sbase):
    """Document."""

    def __init__(
        self,
        model: Model,
        sid: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
        annotations: AnnotationsType = None,
        notes: Optional[str] = None,
        sbml_level: int = SBML_LEVEL,
        sbml_version: int = SBML_VERSION,
    ):
        self.model = model
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.notes = notes
        self.annotations: AnnotationsType = annotations
        self.sbml_level = sbml_level
        self.sbml_version = sbml_version
        self.doc: libsbml.SBMLDocument = None

        sbmlutils_notes = """
        Created with [https://github.com/matthiaskoenig/sbmlutils](https://github.com/matthiaskoenig/sbmlutils).
        [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5525390.svg)](https://doi.org/10.5281/zenodo.5525390)
        """
        if self.notes is None:
            self.notes = sbmlutils_notes
        else:
            self.notes += sbmlutils_notes

    def create_sbml(self) -> libsbml.SBMLDocument:
        """Create SBML model."""
        logger.info(f"Create SBML for model '{self.model.sid}'")

        # create core model
        sbmlns = libsbml.SBMLNamespaces(self.sbml_level, self.sbml_version)

        # add all the packages
        # FIXME: only add packages which are required for the model
        supported_packages = {"fbc", "comp", "distrib"}
        sbmlns.addPackageNamespace("comp", 1)
        if self.model.packages:
            for package in self.model.packages:
                if package not in supported_packages:
                    raise ValueError(
                        f"Supported packages are: '{supported_packages}', "
                        f"but package '{package}' found."
                    )
                if package == "fbc":
                    sbmlns.addPackageNamespace("fbc", 2)
                if package == "distrib":
                    sbmlns.addPackageNamespace("distrib", 1)

        self.doc = libsbml.SBMLDocument(sbmlns)
        self._set_fields(self.doc, None)

        # create model
        sbml_model: libsbml.Model = self.model.create_sbml(self.doc)

        self.doc.setPackageRequired("comp", True)
        if self.model.packages:
            if "fbc" in self.model.packages:
                self.doc.setPackageRequired("fbc", False)
                fbc_plugin = sbml_model.getPlugin("fbc")
                fbc_plugin.setStrict(False)
            if "distrib" in self.model.packages:
                self.doc.setPackageRequired("distrib", True)

        return self.doc

    def get_sbml(self) -> str:
        """Return SBML string of the model.

        :return: SBML string
        """
        if self.doc is None:
            self.create_sbml()
        return str(libsbml.writeSBMLToString(self.doc))

    def get_json(self) -> str:
        """Get JSON representation."""
        o = xmltodict.parse(self.get_sbml())
        return json.dumps(o, indent=2)


@dataclass
class FactoryResult:
    """Results structure when creating SBML models with sbmlutils."""

    sbml_path: Path
    model: "Model"


def create_model(
    models: Union["Model", List["Model"]],
    output_dir: Optional[Path] = None,
    filename: str = None,
    mid: str = None,
    suffix: str = None,
    annotations: Path = None,
    create_report: bool = True,
    validate: bool = True,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
    sbml_level: int = SBML_LEVEL,
    sbml_version: int = SBML_VERSION,
    tmp: bool = False,
) -> FactoryResult:
    """Create SBML model from module information.

    This is the entry point for creating models.
    The model information is provided as a list of importable python modules.
    If no filename is provided the filename is created from the id and suffix.
    Additional model annotations can be provided.

    :param models: iterable of Model instances
    :param output_dir: directory in which to create SBML file
    :param tmp: boolean flag to create files in a temporary directory (for testing)
    :param filename: filename to write to with suffix, if not provided mid and suffix are used
    :param mid: model id to use for filename
    :param suffix: suffix for SBML filename
    :param annotations: Path to annotations file
    :param create_report: boolean switch to create SBML report
    :param validate: validates the SBML file
    :param log_errors: boolean flag to log errors
    :param units_consistency: boolean flag to check units consistency
    :param modeling_practice: boolean flag to check modeling practise
    :param internal_consistency: boolean flag to check internal consistency
    :param sbml_level: set SBML level for model generation
    :param sbml_version: set SBML version for model generation

    :return: FactoryResult
    """
    console.rule(title="Create SBML", style="white")
    if output_dir is None and tmp is False:
        raise TypeError("create_model() missing 1 required argument: 'output_dir'")

    # preprocess
    if isinstance(models, Model):
        models = [models]

    model = Model.merge_models(models)
    doc: libsbml.SBMLDocument = Document(
        model=model,
        sbml_level=sbml_level,
        sbml_version=sbml_version,
    ).create_sbml()

    if not filename:
        # create filename
        if mid is None:
            mid = model.sid
        if suffix is None:
            suffix = ""
        filename = f"{mid}{suffix}.xml"

    if tmp:
        output_dir = Path(tempfile.mkdtemp())
    else:
        if not output_dir:
            raise ValueError("'output_dir' must be provided")
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
            logger.warning(f"'output_dir' should be a Path: {output_dir}")

        if not output_dir.exists():
            logger.warning(f"'output_dir' does not exist and is created: {output_dir}")
            output_dir.mkdir(parents=True)

    sbml_path = output_dir / filename

    # write sbml
    try:
        write_sbml(
            doc=doc,
            filepath=sbml_path,
            validate=validate,
            log_errors=log_errors,
            units_consistency=units_consistency,
            modeling_practice=modeling_practice,
            internal_consistency=internal_consistency,
        )

        # annotate
        if annotations is not None:
            # overwrite the normal file
            annotator.annotate_sbml(
                source=sbml_path,
                annotations_path=annotations,
                filepath=sbml_path
                # type: ignore
            )

        # create report
        if create_report:
            # file is already validated, no validation on report needed
            sbmlreport.create_report(
                sbml_path=sbml_path, validate=False  # type: ignore
            )
    finally:
        if tmp:
            shutil.rmtree(str(output_dir))

    console.rule(style="white")
    return FactoryResult(sbml_path=sbml_path, model=model)  # type: ignore
