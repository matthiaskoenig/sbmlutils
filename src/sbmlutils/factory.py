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

from __future__ import annotations

import datetime
import inspect
import json
import logging
from collections import namedtuple
from collections.abc import Iterable, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import (
    Any,
    ClassVar,
    TypeAlias,
)

import libsbml
import numpy as np
import xmltodict
from numpy import nan as NaN
from pint import UndefinedUnitError, UnitRegistry
from pydantic import BaseModel, ConfigDict
from pymetadata.core.creator import Creator

from sbmlutils.console import console
from sbmlutils.converters.odefac import SBML2ODE
from sbmlutils.io import sbml_to_antimony, write_sbml
from sbmlutils.metadata import (
    BQB,
    BQM,
    SBO,
    annotator,
)
from sbmlutils.metadata.annotator import Annotation
from sbmlutils.notes import Notes, NotesFormat
from sbmlutils.reaction_equation import EquationPart, ReactionEquation
from sbmlutils.utils import FrozenClass, create_metaid
from sbmlutils.validation import ValidationOptions, check

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


logger = logging.getLogger(__name__)

ureg = UnitRegistry()
Q_ = ureg.Quantity
ureg.define("item = 1 dimensionless")

# FIXME: make complete import of all DISTRIB constants

__all__ = [
    "PORT_SUFFIX",
    "PORT_UNIT_SUFFIX",
    "SBML_LEVEL",
    "SBML_VERSION",
    "AlgebraicRule",
    "AssignmentRule",
    "Compartment",
    "Constraint",
    "Creator",
    "Deletion",
    "Document",
    "Event",
    "ExchangeReaction",
    "ExternalModelDefinition",
    "FactoryResult",
    "FluxObjective",
    "Formula",
    "Function",
    "GeneProduct",
    "InitialAssignment",
    "KeyValuePair",
    "Model",
    "ModelDefinition",
    "ModelDict",
    "ModelUnits",
    "NaN",
    "Objective",
    "Package",
    "Parameter",
    "Port",
    "PortType",
    "RateRule",
    "Reaction",
    "ReactionEquation",
    "ReplacedBy",
    "ReplacedElement",
    "Species",
    "Submodel",
    "UncertParameter",
    "UncertSpan",
    "Uncertainty",
    "UnitDefinition",
    "UnitType",
    "Units",
    "UserDefinedConstraint",
    "UserDefinedConstraintComponent",
    "ValidationOptions",
    "create_model",
]


SBML_LEVEL = 3  # default SBML level
SBML_VERSION = 1  # default SBML version
PORT_SUFFIX = "_port"
PORT_UNIT_SUFFIX = "_unit_port"
PREFIX_EXCHANGE_REACTION = "EX_"


def create_objects(
    model: libsbml.Model, obj_iter: list[Any], key: str | None = None
) -> dict[str, libsbml.SBase]:
    """Create the objects in the model.

    This function calls the respective create_sbml function of all objects
    in the order of the objects.

    :param model: SBMLModel instance
    :param obj_iter: iterator of given model object classes like Parameter, ...
    :param key: object key
    :return: dictionary of SBML objects
    """
    sbml_objects: dict[str, libsbml.SBase] = {}

    for obj in obj_iter:
        if obj is None:
            logger.error(
                "Trying to create None object, check for incorrect terminating ',' on objects: '%s'",
                sbml_objects,
            )

        try:
            sbml_obj: libsbml.SBase = obj.create_sbml(model)
        except Exception as err:
            logger.error("Error creating SBML object for '%s'", obj)
            logger.error(err)
            raise err
        # FIXME: what happens for objects without id?
        sbml_objects[sbml_obj.getId()] = sbml_obj

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
        logger.error("Formula could not be parsed: '%s'", formula)
        logger.error(libsbml.getLastParseL3Error())
    return ast_node


UnitType: TypeAlias = "UnitDefinition | None"

#: an annotation is either a full RDF annotation or a `(qualifier, resource)` tuple
AnnotationType: TypeAlias = "Annotation | tuple[BQB | BQM, str]"
#: annotations are accepted as any sequence, an `Sbase` stores them as a list, so
#: that annotations can be appended after the object was created
AnnotationsType: TypeAlias = "Sequence[AnnotationType]"
OptionalAnnotationsType: TypeAlias = "Sequence[AnnotationType] | None"


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
        """Construct ModelUnits."""
        self.time = time
        self.extent = extent
        self.substance = substance
        self.length = length
        self.area = area
        self.volume = volume

    @staticmethod
    def set_model_units(model: libsbml.Model, model_units: ModelUnits) -> None:
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

                unit: str | UnitDefinition = getattr(model_units, key)
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


def set_model_history(
    sbase: libsbml.SBase, creators: list[Creator], set_timestamps: bool = True
) -> None:
    """Set the model history from given creators.

    :param sbase: SBML model
    :param creators: list of creators
    :param set_timestamps: boolean flag to set timestamps on history.
    :return:
    """
    if not sbase.isSetMetaId():
        sbase.setMetaId(create_metaid(sbase=sbase))

    # create and set model history
    h = _create_history(creators=creators, set_timestamps=set_timestamps)
    check(sbase.setModelHistory(h), "set model history")


def _create_history(
    creators: Iterable[Creator], set_timestamps: bool = True
) -> libsbml.ModelHistory:
    """Create the model history.

    Sets the create and modified date to the current time.
    The `set_timestamps` flag allows to set no timestamps.
    """
    h: libsbml.ModelHistory = libsbml.ModelHistory()

    for creator in creators:
        c: libsbml.ModelCreator = libsbml.ModelCreator()
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


def date_now() -> libsbml.Date:
    """Get current time stamp for history.

    :return: current libsbml Date
    """
    time = datetime.datetime.now()
    timestr = time.strftime("%Y-%m-%dT%H:%M:%S")
    return libsbml.Date(timestr)


class Sbase:
    """Base class of all SBML objects."""

    def __init__(
        self,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.notes = notes
        self.keyValuePairs = keyValuePairs
        self.port = port
        self.uncertainties = uncertainties
        self.replacedBy = replacedBy
        self.annotations: list[AnnotationType] = (
            list(annotations) if annotations else []
        )

    fields: ClassVar[list[str]] = [
        "sid",
        "name",
        "sboTerm",
        "metaId",
        "notes",
        "keyValuePairs",
        "port",
        "uncertainties",
        "replacedBy",
        "annotations",
    ]

    def __str__(self) -> str:
        """Get string."""
        field_str = ", ".join(
            [
                str(getattr(self, f))
                for f in self.fields
                if getattr(self, f)
                if f not in {"notes", "annotations"}
            ]
        )
        return f"{self.__class__.__name__}({field_str})"

    @staticmethod
    def _process_annotations(annotation_objects: AnnotationsType) -> list[Annotation]:
        """Process annotation information.

        Various annotation formats are supported which have to be unified at some
        point. This function is performing the annotation normalization.
        """
        annotations: list[Annotation] = []
        if annotation_objects is not None:
            for annotation_obj in annotation_objects:
                annotation: Annotation
                if isinstance(annotation_obj, Annotation):
                    annotation = annotation_obj
                elif isinstance(annotation_obj, (tuple, list, set)):
                    annotation = Annotation.from_tuple(annotation_obj)
                annotations.append(annotation)
        return annotations

    def get_notes_xml(self) -> str | None:
        """Get notes xml string."""
        if self.notes:
            notes_str: str | None = str(Notes(self.notes).xml)
            return notes_str

        return None

    def _set_fields(self, sbase: Any, model: Any) -> None:
        """Set the fields of the created libsbml object.

        Args:
            sbase: the libsbml object created by `create_sbml`; every subclass
                creates exactly one libsbml type and narrows the parameter to
                it, so the base declares it as `Any`
            model: the `libsbml.Model` the object belongs to, `None` for a
                `Document`, which is the only object without a model
        """
        if self.sid is not None:
            if not libsbml.SyntaxChecker.isValidSBMLSId(self.sid):
                logger.error(
                    "The id `%s` is not a valid SBML SId on `%s`. The SId syntax is defined as:	letter ::= 'a'..'z','A'..'Z'	digit  ::= '0'..'9'	idChar ::= letter | digit | '_'	SId    ::= ( letter | '_' ) idChar*",
                    self.sid,
                    sbase,
                )
            sbase.setId(self.sid)
        if self.name is not None:
            sbase.setName(self.name)
        else:
            if not isinstance(
                self, (Document, Port, ReplacedBy, ReplacedElement, AssignmentRule)
            ):
                logger.warning("'name' should be set on '%s'", self)
        if self.sboTerm is not None:
            if isinstance(self.sboTerm, SBO):
                sbo = self.sboTerm.curie
            elif isinstance(self.sboTerm, str):
                sbo = self.sboTerm.replace("_", ":")
            else:
                sbo = self.sboTerm
            sbase.setSBOTerm(sbo)
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
                logger.warning("'sboTerm' should be set on '%s'", self)
        if self.metaId is not None:
            sbase.setMetaId(self.metaId)

        if self.notes is not None and self.notes.strip():
            set_notes(sbase, self.notes)

        # annotation handling
        processed_annotations: list[Annotation] = []
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
                processed_annotations = [sbo_annotation, *processed_annotations]

        for annotation in processed_annotations:
            annotator.ModelAnnotator.annotate_sbase(sbase=sbase, annotation=annotation)

        if model:
            self.create_uncertainties(sbase, model)
            self.create_replaced_by(sbase, model)

        if self.keyValuePairs is not None:
            self.create_key_value_pairs(sbase)

    def create_port(self, model: libsbml.Model) -> libsbml.Port | None:
        """Create port if existing."""
        if self.port is None:
            return None

        p: libsbml.Port | None = None
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
                sbo = SBO.PORT.curie
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
    ) -> list[libsbml.Uncertainty] | None:
        """Create distrib:Uncertainty objects."""
        if not self.uncertainties:
            return None

        objects = []

        # FIXME: check that distrib package is activated
        for uncertainty in self.uncertainties:  # type: Uncertainty
            objects.append(uncertainty.create_sbml(obj, model))
        return objects

    def create_replaced_by(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.ReplacedBy | None:
        """Create comp:ReplacedBy."""
        if not self.replacedBy:
            return None

        return self.replacedBy.create_sbml(sbase, model)

    def create_key_value_pairs(
        self, sbase: libsbml.SBase
    ) -> list[libsbml.KeyValuePair] | None:
        """Create fbc:keyValuePair."""
        if not self.keyValuePairs:
            return None

        kvps: list[libsbml.KeyValuePair] = []
        for kvp in self.keyValuePairs:
            kvps.append(kvp.create_sbml(sbase))
        return kvps


class KeyValuePair(Sbase):
    """KeyValuePair."""

    def __init__(
        self,
        key: str,
        value: str | None,
        uri: str | None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        notes: str | None = None,
        annotations: OptionalAnnotationsType = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Create a KeyValuePair."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.key = key
        self.value = value
        self.uri = uri

    def create_sbml(self, sbase: libsbml.SBase) -> libsbml.KeyValuePair:
        """Create KeyValuePair on object."""
        sbase_fbc: libsbml.FbcSBasePlugin = sbase.getPlugin("fbc")
        kvp_list: libsbml.ListOfKeyValuePairs = sbase_fbc.getListOfKeyValuePairs()
        kvp_list.setXmlns("http://sbml.org/fbc/keyvaluepair")
        kvp: libsbml.KeyValuePair = kvp_list.createKeyValuePair()
        check(kvp.setKey(self.key), "Set Key on KeyValuePair")
        if self.value is not None:
            check(kvp.setValue(self.value), f"Set `value={self.value}` on KeyValuePair")
        if self.uri is not None:
            check(kvp.setValue(self.value), f"Set `uri={self.uri}` on KeyValuePair")

        return kvp


class Value(Sbase):
    """Helper class.

    The value field is a helper storage field which is used differently by different
    subclasses.
    """

    def __init__(
        self,
        sid: str | None,
        value: str | float | None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.value = value

    def _set_fields(self, sbase: Any, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)


class UnitDefinition(Sbase):
    """Unit.

    Corresponds to the information in the libsbml.UnitDefinition.
    """

    # definition: str = (None,)

    _pint2sbml: ClassVar[dict[str, int]] = {
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
        "henry": libsbml.UNIT_KIND_HENRY,
        "hertz": libsbml.UNIT_KIND_HERTZ,
        "item": libsbml.UNIT_KIND_ITEM,
        "joule": libsbml.UNIT_KIND_JOULE,
        "kelvin": libsbml.UNIT_KIND_KELVIN,
        "kilogram": libsbml.UNIT_KIND_KILOGRAM,
        "liter": libsbml.UNIT_KIND_LITRE,
        "meter": libsbml.UNIT_KIND_METRE,
        "mole": libsbml.UNIT_KIND_MOLE,
        "newton": libsbml.UNIT_KIND_NEWTON,
        "ohm": libsbml.UNIT_KIND_OHM,
        "pascal": libsbml.UNIT_KIND_PASCAL,
        "second": libsbml.UNIT_KIND_SECOND,
        "siemens": libsbml.UNIT_KIND_SIEMENS,
        "sievert": libsbml.UNIT_KIND_SIEVERT,
        "volt": libsbml.UNIT_KIND_VOLT,
        "watt": libsbml.UNIT_KIND_WATT,
    }
    # see https://github.com/hgrecco/pint/blob/master/pint/default_en.txt
    _prefixes: ClassVar[dict[str, float]] = {
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
        definition: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        replacedBy: Any | None = None,
    ):
        """Construct UnitDefinition."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            replacedBy=replacedBy,
        )

        self.definition = definition if definition is not None else sid
        if not self.name:
            self.name = self.definition

    def create_sbml(self, model: libsbml.Model) -> libsbml.UnitDefinition | None:
        """Create libsbml.UnitDefinition."""
        if isinstance(self.definition, int):
            # libsbml unit type
            return None

        obj: libsbml.UnitDefinition = model.createUnitDefinition()

        # parse the string into pint
        quantity = Q_(self.definition)
        magnitude, units_tuple = quantity.to_tuple()
        # pint types the units as a fixed length tuple, it is empty for a number
        units: list[Sequence[Any]] = list(units_tuple)

        if units:
            for k, item in enumerate(units):
                prefix, unit_name, _suffix = ureg.parse_unit_name(item[0])[0]
                exponent = float(item[1])
                # first unit gets the multiplier
                multiplier = 1.0
                if k == 0:
                    multiplier = magnitude

                if prefix:
                    multiplier = multiplier * self.__class__._prefixes[prefix]

                multiplier = np.power(multiplier, 1 / abs(exponent))

                scale = 0
                # resolve the kind (this is already a unit known by libsbml)
                kind = self.__class__._pint2sbml.get(unit_name, None)
                if kind is None:
                    # we have to bring the unit to base units
                    uq = Q_(unit_name).to_base_units()
                    # console.log("uq:", uq)
                    multiplier = multiplier * uq.magnitude
                    kind = self.__class__._pint2sbml.get(str(uq.units), None)
                    if kind is None:
                        msg = (
                            f"Unit '{uq.units}' in definition "
                            f"'{self.definition}' could not be converted to SBML."
                        )
                        logger.error(msg)
                        raise ValueError(msg)

                self._create_unit(obj, kind, exponent, scale, multiplier)
        else:
            # only magnitude (units canceled)
            kind = self.__class__._pint2sbml["dimensionless"]
            self._create_unit(obj, kind, 1.0, 0, magnitude)

        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    def _set_fields(self, sbase: libsbml.UnitDefinition, model: libsbml.Model) -> None:
        """Set fields on libsbml.UnitDefinition."""
        super()._set_fields(sbase, model)

    @staticmethod
    def _create_unit(
        udef: libsbml.UnitDefinition,
        kind: int,
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
    def get_uid_for_unit(unit: UnitDefinition | str) -> str | None:
        """Get unit id for given definition string."""
        uid: str | None
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
    def attributes(cls) -> list[tuple[str, str | UnitDefinition]]:
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
            try:
                _: libsbml.UnitDefinition | None = unit_definition.create_sbml(
                    model=model
                )
            except UndefinedUnitError as err:
                console.print_exception(show_locals=False)
                logger.error(
                    "Unit definition '%s' is not valid pint syntax, %s.",
                    unit_definition.definition,
                    err,
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
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        super().__init__(
            sid,
            value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            port=port,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.unit = unit
        if self.unit and not isinstance(self.unit, UnitDefinition):
            logger.warning(
                "'unit' must be of type UnitDefinition, but '%s' in '%s' is '%s'.",
                self.unit,
                self,
                type(self.unit),
            )

    def _set_fields(self, sbase: Any, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)
        if self.unit is not None:
            if sbase.getTypeCode() in [
                libsbml.SBML_ASSIGNMENT_RULE,
                libsbml.SBML_RATE_RULE,
                libsbml.SBML_ALGEBRAIC_RULE,
            ]:
                # AssignmentRules, RateRules and AlgebraicRules have no units
                pass
            else:
                uid = UnitDefinition.get_uid_for_unit(unit=self.unit)
                check(sbase.setUnits(uid), f"Set unit '{uid}' on {sbase}")


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
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct Function."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
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
        self, sbase: libsbml.FunctionDefinition, model: libsbml.Model
    ) -> None:
        super()._set_fields(sbase, model)
        ast_node = ast_node_from_formula(model, self.formula)
        sbase.setMath(ast_node)


class Parameter(ValueWithUnit):
    """Parameter."""

    #: the identifier is required, unlike on `Sbase`
    sid: str

    def __init__(
        self,
        sid: str,
        value: str | float | None = None,
        unit: UnitType = None,
        constant: bool = True,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct Parameter."""
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
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
            obj.setValue(np.nan)

        elif type(self.value) is str:
            try:
                # check if number
                value = float(self.value)
                logger.warning(
                    "When setting a numeric value use float not str: '%s'.", self
                )
                obj.setValue(value)
            except ValueError:
                if self.constant:
                    InitialAssignment(self.sid, self.value).create_sbml(model)
                else:
                    AssignmentRule(self.sid, self.value).create_sbml(model)
        else:
            # numerical value
            obj.setValue(float(self.value))

        self.create_port(model)
        return obj

    def _set_fields(self, sbase: libsbml.Parameter, model: libsbml.Model) -> None:
        """Set fields."""
        super()._set_fields(sbase, model)
        sbase.setConstant(self.constant)


class Compartment(ValueWithUnit):
    """Compartment."""

    #: the identifier is required, unlike on `Sbase`
    sid: str

    def __init__(
        self,
        sid: str,
        value: str | float,
        unit: UnitType = None,
        constant: bool = True,
        spatialDimensions: float = 3,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct Compartment."""
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
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
            obj.setSize(np.nan)
        elif type(self.value) is str:
            try:
                # check if number
                value = float(self.value)
                logger.warning(
                    "When setting a numeric value use float not str: '%s'.", self
                )
                obj.setSize(value)
            except ValueError:
                if self.constant:
                    InitialAssignment(self.sid, self.value).create_sbml(model)
                else:
                    AssignmentRule(self.sid, self.value).create_sbml(model)
        else:
            obj.setSize(float(self.value))

        self.create_port(model)
        return obj

    def _set_fields(self, sbase: libsbml.Compartment, model: libsbml.Model) -> None:
        """Set fields on Compartment."""
        super()._set_fields(sbase, model)
        sbase.setConstant(self.constant)
        sbase.setSpatialDimensions(self.spatialDimensions)


class Species(Sbase):
    """Species."""

    def __init__(
        self,
        sid: str,
        compartment: str,
        initialAmount: float | None = None,
        initialConcentration: float | None = None,
        substanceUnit: UnitType = None,
        hasOnlySubstanceUnits: bool = False,  # default: concentrations
        constant: bool = False,
        boundaryCondition: bool = False,
        charge: float | None = None,
        chemicalFormula: str | None = None,
        conversionFactor: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct Species."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        # overkill for fbc networks
        # if (initialAmount is None) and (initialConcentration is None):
        #     logger.warning(
        #         f"Either initialAmount or initialConcentration should be set "
        #         f"for species: `{sid}`."
        #     )
        if initialAmount and initialConcentration:
            raise ValueError(
                f"Either initialAmount or initialConcentration can be set on "
                f"species, but not both: `{sid}`."
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

    def _set_fields(self, sbase: libsbml.Species, model: libsbml.Model) -> None:
        """Set fields on libsbml.Species."""
        super()._set_fields(sbase, model)
        sbase.setConstant(self.constant)
        if self.compartment is None:
            raise ValueError(f"Compartment cannot be None on Species: '{self}'")
        sbase.setCompartment(self.compartment)
        sbase.setBoundaryCondition(self.boundaryCondition)
        sbase.setHasOnlySubstanceUnits(self.hasOnlySubstanceUnits)

        sbase.setSubstanceUnits(model.getSubstanceUnits())
        if self.substanceUnits is not None:
            sbase.setSubstanceUnits(
                UnitDefinition.get_uid_for_unit(unit=self.substanceUnits)
            )
        else:
            # Fallback to model units
            sbase.setSubstanceUnits(model.getSubstanceUnits())

        if self.initialAmount is not None:
            sbase.setInitialAmount(self.initialAmount)
        if self.initialConcentration is not None:
            sbase.setInitialConcentration(self.initialConcentration)
        if self.conversionFactor is not None:
            sbase.setConversionFactor(self.conversionFactor)

        # fbc
        if (self.charge is not None) or (self.chemicalFormula is not None):
            obj_fbc: libsbml.FbcSpeciesPlugin = sbase.getPlugin("fbc")
            if obj_fbc is None:
                logger.error(
                    "FbcSpeciesPlugin does not exist, add `packages = ['fbc']` "
                    "to model definition."
                )
            else:
                if self.charge is not None:
                    obj_fbc.setCharge(self.charge)
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
        symbol: str,
        value: str | float,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct InitialAssignment."""
        super().__init__(
            sid,
            value,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.symbol = symbol
        self.unit = unit

    def create_sbml(self, model: libsbml.Model) -> libsbml.InitialAssignment:
        """Create InitialAssignment.

        Creates a required parameter if the symbol for the
        initial assignment does not exist in the model.
        """
        # Create parameter if not existing
        if (
            (not model.getParameter(self.symbol))
            and (not model.getSpecies(self.symbol))
            and (not model.getCompartment(self.symbol))
            and (not model.getSpeciesReference(self.symbol))
        ):
            Parameter(
                sid=self.symbol,
                value=None,
                unit=self.unit,
                constant=True,
                name=self.name,
            ).create_sbml(model)

        # Check if rule exists
        if model.getInitialAssignmentBySymbol(self.symbol):
            logger.error(
                "InitialAssignment for symbol '%s' already exists in model: . InitialAssignment will be overwritten '%s'",
                self.symbol,
                self.value,
            )

        obj: libsbml.InitialAssignment = model.createInitialAssignment()
        self._set_fields(obj, model)
        obj.setSymbol(self.symbol)
        ast_node = ast_node_from_formula(model, str(self.value))
        obj.setMath(ast_node)

        self.create_port(model)
        return obj


class RuleWithVariable:
    """Rule."""

    variable: str
    value: str | float
    unit: UnitType
    sid: str | None
    name: str | None

    def check_model_for_rule(self, model: libsbml.Model) -> None:
        """Check model for rule requirements.

        Creates a required parameter if the symbol for the
        initial assignment does not exist in the model.
        """
        # Create parameter if not existing
        if (
            (not model.getParameter(self.variable))
            and (not model.getSpecies(self.variable))
            and (not model.getCompartment(self.variable))
            and (not model.getSpeciesReference(self.variable))
        ):
            Parameter(
                sid=self.variable,
                value=None,
                unit=self.unit,
                constant=False,
                name=self.name,
            ).create_sbml(model)

        # Make sure the parameter is const=False
        p: libsbml.Parameter = model.getParameter(self.variable)
        if p is not None and p.getConstant() is True:
            logger.warning(
                "Parameter affected by AssignmentRule must be 'constant=False', but '%s' is 'constant=%s'.",
                p.getId(),
                p.getConstant(),
            )
            p.setConstant(False)

        # Check if rule exists
        if model.getRuleByVariable(self.variable):
            logger.error(
                "Rule with target variable `%s` already exists in model: . Existing rule will be overwritten with `%s`.",
                self.variable,
                self.value,
            )


class AssignmentRule(ValueWithUnit, RuleWithVariable):
    """AssignmentRule.

    The unit attribute is only for the case where a parameter must be created
    (which has the unit). In case of an initialAssignment of a value the units
    have to be defined in the math.
    """

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.variable} = {self.value} [{self.unit}]"

    def __init__(
        self,
        variable: str,
        value: str | float,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct AssignmentRule."""
        super().__init__(
            sid=sid if sid else f"AssignmentRule_{variable}",
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.variable: str = variable

    def create_sbml(self, model: libsbml.Model) -> libsbml.AssignmentRule:
        """Create AssignmentRule."""
        self.check_model_for_rule(model)
        obj: libsbml.AssignmentRule = model.createAssignmentRule()
        self._set_fields(obj, model)
        obj.setVariable(self.variable)
        ast_node: libsbml.ASTNode = ast_node_from_formula(model, str(self.value))
        obj.setMath(ast_node)
        self.create_port(model)
        return obj


class RateRule(ValueWithUnit, RuleWithVariable):
    """RateRule."""

    def __repr__(self) -> str:
        """Get string representation."""
        return f"d{self.variable}/dt = {self.value} [{self.unit}]"

    def __init__(
        self,
        variable: str,
        value: str | float,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct RateRule."""
        super().__init__(
            sid=sid if sid else f"RateRule_{variable}",
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.variable: str = variable

    def create_sbml(self, model: libsbml.Model) -> libsbml.RateRule:
        """Create RateRule."""
        self.check_model_for_rule(model)
        obj: libsbml.RateRule = model.createRateRule()
        self._set_fields(obj, model)
        obj.setVariable(self.variable)
        ast_node: libsbml.ASTNode = ast_node_from_formula(model, str(self.value))
        obj.setMath(ast_node)
        self.create_port(model)
        return obj


class AlgebraicRule(ValueWithUnit, RuleWithVariable):
    """AlgebraicRule."""

    def __repr__(self) -> str:
        """Get string representation."""
        return f"0 = {self.value} [{self.unit}]"

    def __init__(
        self,
        sid: str,
        value: str | float,
        unit: UnitType = Units.dimensionless,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct AlgebraicRule."""
        super().__init__(
            sid=sid,
            value=value,
            unit=unit,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

    def create_sbml(self, model: libsbml.Model) -> libsbml.AlgebraicRule:
        """Create AlgebraicRule."""
        rule: libsbml.AlgebraicRule = model.createAlgebraicRule()
        self._set_fields(rule, model)
        ast_node: libsbml.ASTNode = ast_node_from_formula(model, str(self.value))
        rule.setMath(ast_node)
        self.create_port(model)
        return rule


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
        equation: ReactionEquation | str,
        formula: Formula | tuple[str, UnitType] | str | None = None,
        pars: list[Parameter] | None = None,
        rules: list[AssignmentRule] | None = None,
        compartment: str | None = None,
        fast: bool = False,
        reversible: bool | None = None,
        lowerFluxBound: str | None = None,
        upperFluxBound: str | None = None,
        geneProductAssociation: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct Reaction."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        self.equation = Reaction._process_equation(equation=equation)
        self.compartment = compartment
        self.reversible = reversible
        self.pars = pars if pars else []
        self.rules = rules if rules else []
        self.formula = Reaction._process_formula(formula=formula)
        self.fast = fast
        self.lowerFluxBound = lowerFluxBound
        self.upperFluxBound = upperFluxBound
        self.geneProductAssociation = geneProductAssociation

    @staticmethod
    def _process_equation(equation: ReactionEquation | str) -> ReactionEquation:
        """Process reaction equation."""
        if isinstance(equation, ReactionEquation):
            return equation
        return ReactionEquation.from_str(str(equation))

    @staticmethod
    def _process_formula(
        formula: Formula | tuple[str, UnitType] | str | None,
    ) -> Formula | None:
        """Process reaction formula (kinetic law)."""
        if formula is None:
            return None
        if isinstance(formula, Formula):
            return formula
        if isinstance(formula, (tuple, list)):
            return Formula(*formula)
        if isinstance(formula, str):
            return Formula(value=formula, unit=None)
        raise ValueError(f"Unsupported formula: '{formula}'")

    def create_sbml(self, model: libsbml.Model) -> libsbml.Reaction:
        """Create Reaction SBML in model."""
        # parameters and rules
        create_objects(model, self.pars, key="parameters")
        create_objects(model, self.rules, key="rules")

        # reaction
        r: libsbml.Reaction = model.createReaction()
        self._set_fields(r, model)
        r_fbc: libsbml.FbcReactionPlugin = r.getPlugin("fbc")

        def set_speciesref_fields(
            sref: libsbml.SpeciesReference, part: EquationPart
        ) -> None:
            """Set the fields on the SpeciesReference."""
            if part.species is not None:
                sref.setSpecies(part.species)
            if part.sid is not None:
                sref.setId(part.sid)
            if part.constant is not None:
                sref.setConstant(part.constant)
            if part.stoichiometry is not None:
                sref.setStoichiometry(part.stoichiometry)
            if part.metaId is not None:
                sref.setMetaId(part.metaId)
            if part.sboTerm is not None:
                sref.setSBOTerm(part.sboTerm)

        # equation
        for reactant in self.equation.reactants:
            rref: libsbml.SpeciesReference = r.createReactant()
            set_speciesref_fields(sref=rref, part=reactant)

        for product in self.equation.products:
            pref: libsbml.SpeciesReference = r.createProduct()
            set_speciesref_fields(sref=pref, part=product)

        for modifier in self.equation.modifiers:
            mref: libsbml.ModifierSpeciesReference = r.createModifier()
            mref.setSpecies(modifier)

        # kinetics
        if self.formula:
            Reaction.set_kinetic_law(model, r, self.formula.value)

        # add fbc bounds
        if self.upperFluxBound or self.lowerFluxBound:
            if self.upperFluxBound:
                r_fbc.setUpperFluxBound(self.upperFluxBound)
            if self.lowerFluxBound:
                r_fbc.setLowerFluxBound(self.lowerFluxBound)

        # add gpa
        if self.geneProductAssociation:
            # parse the string and create the respective GPA
            gpa: libsbml.GeneProductAssociation = r_fbc.createGeneProductAssociation()

            # check all genes are in model
            gpr_clean = (
                self.geneProductAssociation.replace("(", " ")
                .replace(")", " ")
                .replace("and", " ")
                .replace("AND", "")
                .replace("or", "")
                .replace("OR", "")
            )
            gps: list[str] = [g for g in gpr_clean.split(" ") if g]
            model_fbc: libsbml.FbcModelPlugin = r.getModel().getPlugin("fbc")
            for gp in gps:
                if not model_fbc.getGeneProduct(gp):
                    logger.error("GeneProduct missing in model: `%s`", gp)

            check(
                gpa.setAssociation(
                    self.geneProductAssociation,
                    True,  # bool usingId=False,
                    False,  # bool addMissingGP=True
                ),
                f"set gpa: `{self.geneProductAssociation}`",
            )

        self.create_port(model)
        return r

    def _set_fields(self, sbase: libsbml.Reaction, model: libsbml.Model) -> None:
        """Set fields in libsbml.Reaction."""
        super()._set_fields(sbase, model)

        if self.compartment:
            sbase.setCompartment(self.compartment)
        # else:
        #    logger.info(f"'compartment' should be set on '{self}'}")
        sbase.setReversible(self.equation.reversible)
        sbase.setFast(self.fast)

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
        assignments: dict[str, str | float] | None = None,
        trigger_persistent: bool = True,
        trigger_initialValue: bool = False,
        useValuesFromTriggerTime: bool = True,
        priority: str | None = None,
        delay: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct Event."""
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )

        self.trigger = trigger
        self.assignments = assignments if assignments else {}
        if type(assignments) is not dict:
            logger.warning(
                "Event assignment must be dict with sid: assignment, but: '%s'",
                type(assignments),
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

    def _set_fields(self, sbase: libsbml.Event, model: libsbml.Model) -> None:
        """Set fields in libsbml.Event."""
        super()._set_fields(sbase, model)

        sbase.setUseValuesFromTriggerTime(True)
        t = sbase.createTrigger()
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
            priority: libsbml.Priority = sbase.createPriority()
            priority.setMath(ast_priority)

        if self.delay is not None:
            ast_delay = libsbml.parseL3FormulaWithModel(self.delay, model)
            sbase.setDelay(ast_delay)

        for key, math in self.assignments.items():
            ast_assign = libsbml.parseL3FormulaWithModel(str(math), model)
            ea = sbase.createEventAssignment()
            ea.setVariable(key)
            ea.setMath(ast_assign)

    @staticmethod
    def _trigger_from_time(t: float) -> str:
        """Create trigger from given time point."""
        return f"(time >= {t})"

    @staticmethod
    def _assignments_dict(species: list[str], values: list[str]) -> dict[str, str]:
        return dict(zip(species, values, strict=False))


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
        message: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Constraint constructor."""
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
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

    def _set_fields(self, sbase: libsbml.Constraint, model: libsbml.Model) -> None:
        """Set fields on libsbml.Constraint."""
        super()._set_fields(sbase, model)

        if self.math is not None:
            ast_math = libsbml.parseL3FormulaWithModel(self.math, model)
            sbase.setMath(ast_math)
        if self.message is not None:
            check(
                sbase.setMessage(self.message),
                message=f"Setting message on constraint: '{self.message}'",
            )


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
        value: float | None = None,
        var: str | None = None,
        unit: UnitType = None,
    ):
        """Construct UncertParameter."""
        if (value is None) and (var is None):
            raise ValueError(
                "Either 'value' or 'var' have to be set in UncertParameter."
            )
        self.type: str = type
        self.value: float | None = value
        self.var: str | None = var
        self.unit: UnitType = unit


class UncertSpan:
    """UncertSpan.

    FIXME: This is an SBase!
    """

    def __init__(
        self,
        type: str,
        valueLower: float | None = None,
        varLower: str | None = None,
        valueUpper: float | None = None,
        varUpper: str | None = None,
        unit: UnitType = None,
    ):
        """Construct UncertSpan."""
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
        sid: str | None = None,
        formula: str | None = None,
        uncertParameters: list[UncertParameter] | None = None,
        uncertSpans: list[UncertSpan] | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        replacedBy: Any | None = None,
    ):
        """Uncertainty constructor."""
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            replacedBy=replacedBy,
        )

        # Object on which the uncertainty is written
        self.formula = formula
        self.uncertParameters: list[UncertParameter] = (
            uncertParameters if uncertParameters else []
        )
        self.uncertSpans: list[UncertSpan] = uncertSpans if uncertSpans else []

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
                    "Unsupported type for UncertSpan: '%s' in '%s'.",
                    uncertSpan.type,
                    uncertSpan,
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
                up_p: libsbml.UncertParameter = uncertainty.createUncertParameter()
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
                    "Unsupported type for UncertParameter: '%s' in '%s'.",
                    uncertParameter.type,
                    uncertParameter,
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
                        f"http://www.sbml.org/sbml/symbols/distrib/{key}"
                    )
                    ast = libsbml.parseL3FormulaWithModel(self.formula, model)
                    if ast is None:
                        logger.error(libsbml.getLastParseL3Error())
                    else:
                        check(up_dist.setMath(ast), "set math in distrib formula")

        return uncertainty


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
        compartment: str | None = None,
        fast: bool = False,
        reversible: bool = True,
        lowerFluxBound: str | None = None,
        upperFluxBound: str | None = None,
        geneProductAssociation: str | None = None,
        name: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct ExchangeReaction."""
        super().__init__(
            sid=ExchangeReaction.PREFIX + species_id,
            equation=f"{species_id} ->",
            sboTerm=SBO.EXCHANGE_REACTION,
            name=name,
            compartment=compartment,
            fast=fast,
            reversible=reversible,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            lowerFluxBound=lowerFluxBound,
            upperFluxBound=upperFluxBound,
            geneProductAssociation=geneProductAssociation,
            uncertainties=uncertainties,
            port=port,
            replacedBy=replacedBy,
        )


class GeneProduct(Sbase):
    """GeneProduct.

    GeneProduct is a new FBC class derived from SBML SBase that inherits metaid
    and sboTerm, as well as the subcomponents for Annotation and Notes.
    The purpose of this class is to define a single gene product. It implements
    two required attributes id and label as well as two optional attributes
    name and associatedSpecies.
    """

    def __init__(
        self,
        sid: str,
        label: str,
        associatedSpecies: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Create a GeneProduct."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.associatedSpecies = associatedSpecies
        self.label = label

    def create_sbml(self, model: libsbml.Model) -> libsbml.GeneProduct:
        """Create GeneProduct."""
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        gene_product: libsbml.GeneProduct = model_fbc.createGeneProduct()
        self._set_fields(gene_product, model=model)

        gene_product.setLabel(self.label)
        if self.associatedSpecies:
            gene_product.setAssociatedSpecies(self.associatedSpecies)

        return gene_product


class UserDefinedConstraintComponent(Sbase):
    """UserDefinedConstraintComponent."""

    def __init__(
        self,
        coefficient: str,
        variable: str,
        variableType: str | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Create a UserDefinedConstraintComponent."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.variable = variable
        self.coefficient = coefficient
        self.variableType = (
            FluxObjective.normalize_variable_type(variableType)
            if variableType
            else None
        )

    def create_sbml(
        self, constraint: libsbml.UserDefinedConstraint
    ) -> libsbml.UserDefinedConstraintComponent:
        """Create Objective."""
        component: libsbml.UserDefinedConstraintComponent = (
            constraint.createUserDefinedConstraintComponent()
        )
        self._set_fields(component, model=constraint.getModel())

        check(component.setVariable(self.variable), f"set variable `{self.variable}`")
        check(
            component.setCoefficient(self.coefficient),
            f"set coefficient `{self.coefficient}`",
        )
        check(
            component.setVariableType(self.variableType),
            f"set variableType `{self.variableType}`",
        )

        return component


class UserDefinedConstraint(Sbase):
    """UserDefinedConstraint.

    The FBC UserDefinedConstraint class is derived from SBML SBase and inherits
    metaid and sboTerm, as well as the subcomponents for Annotation and Notes.
    It’s purpose is to define non-stoichiometric constraints, that is
    constraints that are not necessarily defined by the stoichiometrically coupled
    reaction network. In order to achieve, we defined a new type of linear
    constraint, the UserDefinedConstraint

    """

    def __init__(
        self,
        lowerBound: str,
        upperBound: str,
        components: list[UserDefinedConstraintComponent] | dict[str, str] | None = None,
        variableType: str = libsbml.FBC_VARIABLE_TYPE_LINEAR,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Create an UserDefinedConstraint."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.lowerBound = lowerBound
        self.upperBound = upperBound

        # normalize components
        self.components: list[UserDefinedConstraintComponent] = []
        if components:
            if isinstance(components, dict):
                # create FluxObjectives from dict
                for variable, coefficient in components.items():
                    self.components.append(
                        UserDefinedConstraintComponent(
                            variable=variable,
                            coefficient=coefficient,
                            variableType=variableType,
                        )
                    )
            else:
                for component in components:
                    # infer variableType from objective
                    if not component.variableType:
                        component.variableType = variableType
                    self.components.append(component)

    def create_sbml(self, model: libsbml.Model) -> libsbml.UserDefinedConstraint:
        """Create UserDefinedConstraint."""
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        udc: libsbml.UserDefinedConstraint = model_fbc.createUserDefinedConstraint()
        self._set_fields(udc, model)
        udc.setUpperBound(self.upperBound)
        udc.setLowerBound(self.lowerBound)
        for component in self.components:
            component.create_sbml(constraint=udc)

        return udc


class FluxObjective(Sbase):
    """FluxObjective."""

    fbc_variable_types: ClassVar[set[str]] = {
        libsbml.FBC_VARIABLE_TYPE_LINEAR,
        libsbml.FBC_VARIABLE_TYPE_QUADRATIC,
        libsbml.FBC_VARIABLE_TYPE_INVALID,
        "linear",
        "quadratic",
        "invalid",
    }

    def __init__(
        self,
        reaction: str,
        coefficient: float,
        variableType: str,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Create a FluxObjective."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.reaction = reaction
        self.coefficient = coefficient
        self.variableType = FluxObjective.normalize_variable_type(variableType)

    @classmethod
    def normalize_variable_type(cls, variable_type: str) -> str:
        """Normalize variable type."""
        if variable_type not in cls.fbc_variable_types:
            raise ValueError(
                f"Unsupported objective type `{variable_type}`. Supported are "
                f"`{FluxObjective.fbc_variable_types}`."
            )

        if variable_type == "linear":
            variable_type = libsbml.FBC_VARIABLE_TYPE_LINEAR
        elif variable_type == "quadratic":
            variable_type = libsbml.FBC_VARIABLE_TYPE_QUADRATIC
        elif variable_type == "invalid":
            variable_type = libsbml.FBC_VARIABLE_TYPE_INVALID
        return variable_type

    def create_sbml(self, objective: libsbml.Objective) -> libsbml.FluxObjective:
        """Create Objective."""
        flux_objective: libsbml.FluxObjective = objective.createFluxObjective()
        self._set_fields(flux_objective, model=objective.getModel())

        flux_objective.setReaction(self.reaction)
        flux_objective.setCoefficient(self.coefficient)
        flux_objective.setVariableType(self.variableType)

        return flux_objective


class Objective(Sbase):
    """Objective."""

    objective_types: ClassVar[set[str]] = {
        libsbml.OBJECTIVE_TYPE_MAXIMIZE,
        libsbml.OBJECTIVE_TYPE_MINIMIZE,
        "maximize",
        "minimize",
        "max",
        "min",
    }

    def __init__(
        self,
        sid: str,
        objectiveType: str = libsbml.OBJECTIVE_TYPE_MAXIMIZE,
        active: bool = True,
        fluxObjectives: list[FluxObjective] | dict[str, float] | None = None,
        variableType: str = libsbml.FBC_VARIABLE_TYPE_LINEAR,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Create an Objective.

        FluxObjectives can either be provided as a list of FluxObjectives or as a
        dictionary with the reaction ids as keys and the coefficients as values.
        """
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
            uncertainties=uncertainties,
            replacedBy=replacedBy,
        )
        self.objectiveType = self.normalize_objective_type(objectiveType)
        self.active = active

        # normalize fluxObjectives
        self.fluxObjectives: list[FluxObjective] = []
        if fluxObjectives:
            if isinstance(fluxObjectives, dict):
                # create FluxObjectives from dict
                for rid, coefficient in fluxObjectives.items():
                    self.fluxObjectives.append(
                        FluxObjective(
                            reaction=rid,
                            coefficient=coefficient,
                            variableType=variableType,
                        )
                    )
            else:
                for flux_objective in fluxObjectives:
                    # infer variableType from objective
                    if not flux_objective.variableType:
                        flux_objective.variableType = variableType
                    self.fluxObjectives.append(flux_objective)

    @classmethod
    def normalize_objective_type(cls, objective_type: str) -> str:
        """Normalize objective type."""
        if objective_type not in Objective.objective_types:
            raise ValueError(
                f"Unsupported objective type `{objective_type}`. Supported are "
                f"`{Objective.objective_types}`."
            )
        if objective_type in {"min", "minimize"}:
            objective_type = libsbml.OBJECTIVE_TYPE_MINIMIZE
        elif objective_type in {"max", "maximize"}:
            objective_type = libsbml.OBJECTIVE_TYPE_MAXIMIZE

        return objective_type

    def create_sbml(self, model: libsbml.Model) -> libsbml.Objective:
        """Create Objective."""
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        objective: libsbml.Objective = model_fbc.createObjective()
        self._set_fields(objective, model)
        objective.setType(self.objectiveType)
        if self.active:
            model_fbc.setActiveObjectiveId(self.sid)
        for flux_objective in self.fluxObjectives:
            flux_objective.create_sbml(objective=objective)

        return objective


class ModelDefinition(Sbase):
    """ModelDefinition."""

    # FIXME: handle as model

    def __init__(
        self,
        sid: str,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        units: type[Units] | None = None,
        compartments: list[Compartment] | None = None,
        species: list[Species] | None = None,
    ):
        """Create a ModelDefinition."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
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

    def _set_fields(self, sbase: libsbml.ModelDefinition, model: libsbml.Model) -> None:
        """Set fields on ModelDefinition."""
        super()._set_fields(sbase, model)
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
                    create_objects(sbase, obj_iter=objects, key=attr)


class ExternalModelDefinition(Sbase):
    """ExternalModelDefinition."""

    def __init__(
        self,
        sid: str,
        source: str,
        modelRef: str,
        md5: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create an ExternalModelDefinition."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
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
        self, sbase: libsbml.ExternalModelDefinition, model: libsbml.Model
    ) -> None:
        """Set fields on ExternalModelDefinition."""
        super()._set_fields(sbase, model)
        sbase.setModelRef(self.modelRef)
        sbase.setSource(self.source)
        if self.md5 is not None:
            sbase.setMd5(self.md5)


class Submodel(Sbase):
    """Submodel."""

    def __init__(
        self,
        sid: str,
        modelRef: str | None = None,
        timeConversionFactor: str | None = None,
        extentConversionFactor: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create a Submodel."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
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

    def _set_fields(self, sbase: libsbml.Submodel, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)


class SbaseRef(Sbase):
    """SBaseRef."""

    def __init__(
        self,
        sid: str,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create an SBaseRef."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )
        self.portRef = portRef
        self.idRef = idRef
        self.unitRef = unitRef
        self.metaIdRef = metaIdRef

    def _set_fields(self, sbase: Any, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)

        sbase.setId(self.sid)
        if self.portRef is not None:
            sbase.setPortRef(self.portRef)
        if self.idRef is not None:
            sbase.setIdRef(self.idRef)
        if self.unitRef is not None:
            unit_str = UnitDefinition.get_uid_for_unit(unit=self.unitRef)
            sbase.setUnitRef(unit_str)
        if self.metaIdRef is not None:
            sbase.setMetaIdRef(self.metaIdRef)


class ReplacedElement(SbaseRef):
    """ReplacedElement."""

    def __init__(
        self,
        sid: str,
        elementRef: str,
        submodelRef: str,
        deletion: str | None = None,
        conversionFactor: str | None = None,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create a ReplacedElement."""
        super().__init__(
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
            keyValuePairs=keyValuePairs,
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

    def _set_fields(self, sbase: libsbml.ReplacedElement, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)
        sbase.setSubmodelRef(self.submodelRef)
        if self.deletion:
            sbase.setDeletion(self.deletion)
        if self.conversionFactor:
            sbase.setConversionFactor(self.conversionFactor)


class ReplacedBy(SbaseRef):
    """ReplacedBy."""

    def __init__(
        self,
        sid: str,
        elementRef: str,
        submodelRef: str,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create a ReplacedElement."""
        super().__init__(
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
            keyValuePairs=keyValuePairs,
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

    def _set_fields(self, sbase: libsbml.ReplacedBy, model: libsbml.Model) -> None:
        """Set fields in ReplacedBy."""
        super()._set_fields(sbase, model)
        sbase.setSubmodelRef(self.submodelRef)


class Deletion(SbaseRef):
    """Deletion."""

    def __init__(
        self,
        sid: str,
        submodelRef: str,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Initialize Deletion."""
        super().__init__(
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
            keyValuePairs=keyValuePairs,
        )
        self.submodelRef = submodelRef

    def create_sbml(self, model: libsbml.Model) -> libsbml.Deletion:
        """Create SBML Deletion."""
        cmodel: libsbml.CompModelPlugin = model.getPlugin("comp")
        submodel: libsbml.Submodel = cmodel.getSubmodel(self.submodelRef)
        deletion: libsbml.Deletion = submodel.createDeletion()
        self._set_fields(deletion, model)

        return deletion

    def _set_fields(self, sbase: libsbml.Deletion, model: libsbml.Model) -> None:
        """Set fields on Deletion."""
        super()._set_fields(sbase, model)


class PortType(StrEnum):
    """Supported port types."""

    PORT = "port"
    INPUT_PORT = "input port"
    OUTPUT_PORT = "output port"


class Port(SbaseRef):
    """Port.

    Ports are stored in an optional child ListOfPorts object, which, if
    present, must contain one or more Port objects.  All of the Ports
    present in the ListOfPorts collectively define the 'port interface' of
    the Model.
    """

    def __init__(
        self,
        sid: str,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        portType: PortType | None = PortType.PORT,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create a Port."""
        super().__init__(
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
            keyValuePairs=keyValuePairs,
        )
        self.portType = portType

    def create_sbml(self, model: libsbml.Model) -> libsbml.Port:
        """Create SBML for Port."""
        cmodel = model.getPlugin("comp")
        p = cmodel.createPort()
        self._set_fields(p, model)

        if self.sboTerm is None:
            if self.portType == PortType.PORT:
                sbo = SBO.PORT
            elif self.portType == PortType.INPUT_PORT:
                sbo = SBO.INPUT_PORT
            elif self.portType == PortType.OUTPUT_PORT:
                sbo = SBO.OUTPUT_PORT
            p.setSBOTerm(sbo.value.replace("_", ":"))

        return p

    def _set_fields(self, sbase: libsbml.Port, model: libsbml.Model) -> None:
        """Set fields on Port."""
        super()._set_fields(sbase, model)


class Package(StrEnum):
    """Supported/tested packages."""

    COMP = "comp"
    COMP_V1 = "comp-v1"
    DISTRIB = "distrib"
    DISTRIB_V1 = "distrib-v1"
    FBC = "fbc"
    FBC_V2 = "fbc-v2"
    FBC_V3 = "fbc-v3"


class ModelDict(TypedDict, total=False):
    """ModelDict.

    The ModelDict allows to define the Model as dictionary and then
    use:

      md: ModelDict
      Model(**md)

    For model construction. If possible use the Model object directly.
    """

    sid: str
    name: str | None
    sboTerm: str | None
    metaId: str | None
    annotations: OptionalAnnotationsType
    notes: str | None
    keyValuePairs: list[KeyValuePair] | None
    packages: list[Package] | None
    creators: list[Creator] | None
    model_units: ModelUnits | None
    objects: list[Sbase] | None

    units: type[Units] | None
    functions: list[Function] | None
    compartments: list[Compartment] | None
    species: list[Species] | None
    parameters: list[Parameter] | None
    assignments: list[InitialAssignment] | None
    rules: list[AssignmentRule] | None
    rate_rules: list[RateRule] | None
    algebraic_rules: list[AlgebraicRule] | None
    reactions: list[Reaction] | None
    events: list[Event] | None
    constraints: list[Constraint] | None
    # comp
    external_model_definitions: list[ExternalModelDefinition] | None
    model_definitions: list[ModelDefinition] | None
    submodels: list[Submodel] | None
    ports: list[Port] | None
    replaced_elements: list[ReplacedElement] | None
    deletions: list[Deletion] | None
    # fbc
    user_defined_constraints: list[UserDefinedConstraint] | None
    objectives: list[Objective] | None
    gene_products: list[GeneProduct] | None
    # layout
    layouts: list | None


class Model(Sbase, FrozenClass, BaseModel):
    """Model."""

    model_config = ConfigDict(
        extra="allow",
        arbitrary_types_allowed=True,
        protected_namespaces=(),
    )

    sid: str
    name: str | None
    sboTerm: str | None
    metaId: str | None
    annotations: AnnotationsType
    notes: str | None
    keyValuePairs: list[KeyValuePair] | None
    port: Any | None
    packages: list[Package]
    creators: list[Creator]
    model_units: ModelUnits | None
    units: type[Units] | None
    functions: list[Function]
    compartments: list[Compartment]
    species: list[Species]
    parameters: list[Parameter]
    assignments: list[InitialAssignment]
    rules: list[AssignmentRule]
    rate_rules: list[RateRule]
    algebraic_rules: list[AlgebraicRule]
    reactions: list[Reaction]
    events: list[Event]
    constraints: list[Constraint]
    # comp
    external_model_definitions: list[ExternalModelDefinition]
    model_definitions: list[ModelDefinition]
    submodels: list[Submodel]
    ports: list[Port]
    replaced_elements: list[ReplacedElement]
    deletions: list[Deletion]
    # fbc
    user_defined_constraints: list[UserDefinedConstraint]
    objectives: list[Objective]
    gene_products: list[GeneProduct]
    # layout
    layouts: list | None

    _keys: ClassVar[dict[str, Any]] = {
        "sid": None,
        "name": None,
        "sboTerm": None,
        "metaId": None,
        "annotations": list,
        "notes": None,
        "keyValuePairs": list,
        "port": None,
        "packages": list,
        "creators": None,
        "model_units": None,
        "units": None,
        "functions": list,
        "compartments": list,
        "species": list,
        "parameters": list,
        "assignments": list,
        "rules": list,
        "rate_rules": list,
        "algebraic_rules": list,
        "reactions": list,
        "events": list,
        "constraints": list,
        "external_model_definitions": list,
        "model_definitions": list,
        "submodels": list,
        "ports": list,
        "replaced_elements": list,
        "deletions": list,
        "user_defined_constraints": list,
        "objectives": list,
        "gene_products": list,
        "layouts": list,
    }

    _supported_packages: ClassVar[set[str]] = {
        Package.COMP,
        Package.COMP_V1,
        Package.DISTRIB,
        Package.DISTRIB_V1,
        Package.FBC,
        Package.FBC_V2,
        Package.FBC_V3,
    }

    def __str__(self) -> str:
        """Get string."""
        # FIXME: issue with access
        # field_str = ", ".join(f"{a}={v!r}" for a, v in self.__repr_args__() if a and v and not a.startswith("_"))
        # return f"{self.__class__.__name__}({field_str})"
        return f"{self.__class__.__name__}"

    def __init__(
        self,
        sid: str,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        packages: list[Package] | None = None,
        creators: list[Creator] | None = None,
        model_units: ModelUnits | None = None,
        units: type[Units] | None = None,
        objects: list[Sbase] | None = None,
        external_model_definitions: list[ExternalModelDefinition] | None = None,
        model_definitions: list[ModelDefinition] | None = None,
        submodels: list[Submodel] | None = None,
        functions: list[Function] | None = None,
        compartments: list[Compartment] | None = None,
        species: list[Species] | None = None,
        parameters: list[Parameter] | None = None,
        assignments: list[InitialAssignment] | None = None,
        rules: list[AssignmentRule] | None = None,
        rate_rules: list[RateRule] | None = None,
        algebraic_rules: list[AlgebraicRule] | None = None,
        reactions: list[Reaction] | None = None,
        events: list[Event] | None = None,
        constraints: list[Constraint] | None = None,
        ports: list[Port] | None = None,
        replaced_elements: list[ReplacedElement] | None = None,
        deletions: list[Deletion] | None = None,
        user_defined_constraints: list[UserDefinedConstraint] | None = None,
        objectives: list[Objective] | None = None,
        gene_products: list[GeneProduct] | None = None,
        layouts: list | None = None,
    ):
        """Model constructor."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )

        self.packages = self.check_packages(packages)

        self.creators = creators if creators else []
        self.model_units = model_units
        self.units = units if units else Units
        self.units_dict = None
        self.external_model_definitions = (
            external_model_definitions if external_model_definitions else []
        )
        self.model_definitions = model_definitions if model_definitions else []

        self.submodels: list[Submodel] = submodels if submodels else []
        self.functions: list[Function] = functions if functions else []
        self.compartments: list[Compartment] = compartments if compartments else []
        self.species: list[Species] = species if species else []
        self.parameters: list[Parameter] = parameters if parameters else []
        self.assignments: list[InitialAssignment] = assignments if assignments else []
        self.rules: list[AssignmentRule] = rules if rules else []
        self.rate_rules: list[RateRule] = rate_rules if rate_rules else []
        self.algebraic_rules: list[AlgebraicRule] = (
            algebraic_rules if algebraic_rules else []
        )
        self.reactions: list[Reaction] = reactions if reactions else []
        self.events: list[Event] = events if events else []
        self.constraints: list[Constraint] = constraints if constraints else []
        self.ports: list[Port] = ports if ports else []
        self.replaced_elements: list[ReplacedElement] = (
            replaced_elements if replaced_elements else []
        )
        self.deletions: list[Deletion] = deletions if deletions else []
        self.user_defined_constraints: list[UserDefinedConstraint] = (
            user_defined_constraints if user_defined_constraints else []
        )
        self.objectives: list[Objective] = objectives if objectives else []
        self.gene_products: list[GeneProduct] = gene_products if gene_products else []

        self.layouts: list | None = layouts

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
                elif isinstance(sbase, AlgebraicRule):
                    self.algebraic_rules.append(sbase)
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
                elif isinstance(sbase, UserDefinedConstraint):
                    self.user_defined_constraints.append(sbase)
                elif isinstance(sbase, Objective):
                    self.objectives.append(sbase)
                elif isinstance(sbase, GeneProduct):
                    self.gene_products.append(sbase)

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
            "gene_products",
            "reactions",
            "assignments",
            "rules",
            "rate_rules",
            "algebraic_rules",
            "events",
            "constraints",
            "ports",
            "replaced_elements",
            "deletions",
            "user_defined_constraints",
            "objectives",
            "layouts",
        ]:
            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                if objects:
                    create_objects(model, obj_iter=objects, key=attr)

        return model

    def get_sbml(self) -> str:
        """Create SBML model."""
        return Document(model=self).get_sbml()

    def check_packages(self, packages: list[Package] | None) -> list[Package]:
        """Check that all provided packages are supported."""
        if packages is None:
            packages = []
        packages_set: set[Package] = set(packages)
        for p in packages_set:
            if not isinstance(p, Package):
                msg = (
                    f"Packages must be provided as `Package`, but package "
                    f"`{p}` is `{type(p)}`."
                )
                logger.error(msg)
                raise ValueError(msg)

        # normalize package versions
        if Package.COMP in packages_set:
            packages_set.remove(Package.COMP)
            packages_set.add(Package.COMP_V1)

        if Package.FBC in packages_set:
            packages_set.remove(Package.FBC)
            packages_set.add(Package.FBC_V3)

        if Package.DISTRIB in packages_set:
            packages_set.remove(Package.DISTRIB)
            packages_set.add(Package.DISTRIB_V1)

        if len(packages_set) < len(packages):
            raise ValueError(f"Duplicate packages in `{packages}`.")

        for p in packages_set:
            if not isinstance(p, str):
                raise ValueError(
                    f"Packages must be provided as `Package`, but type `{type(p)}` "
                    f"for package `{p}`."
                )
            if p not in self._supported_packages:
                raise ValueError(
                    f"Supported packages are: '{self._supported_packages}', "
                    f"but package '{p}' found."
                )

        # add comp as default package
        packages_set.add(Package.COMP_V1)

        return list(packages_set)

    @staticmethod
    def merge_models(models: Iterable[Model]) -> Model:
        """Merge information from multiple models."""
        if isinstance(models, Model):
            return models
        if not models:
            raise ValueError("No models are provided.")
        model = Model("template")
        units_base_classes: list[type[Units]] = (
            [model.units] if model.units else [Units]
        )
        creators: dict[Creator, Any] = {}  # using a dict to keep order of insertion
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
                            creators[c] = None
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


class Document(Sbase):
    """Document."""

    def __init__(
        self,
        model: Model,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sbml_level: int = SBML_LEVEL,
        sbml_version: int = SBML_VERSION,
    ):
        """Document constructor."""
        self.model = model
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.annotations: list[AnnotationType] = (
            list(annotations) if annotations else []
        )
        self.notes = notes
        self.keyValuePairs = keyValuePairs
        self.sbml_level = sbml_level
        self.sbml_version = sbml_version
        self.doc: libsbml.SBMLDocument | None = None

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
        logger.info("Create SBML for model '%s'", self.model.sid)

        # create core model
        sbmlns = libsbml.SBMLNamespaces(self.sbml_level, self.sbml_version)

        # add all the package
        for package in self.model.packages:
            if package == Package.COMP_V1:
                sbmlns.addPackageNamespace("comp", 1)
            if package == Package.DISTRIB_V1:
                sbmlns.addPackageNamespace("distrib", 1)
            if package == Package.FBC_V2:
                sbmlns.addPackageNamespace("fbc", 2)
            if package == Package.FBC_V3:
                sbmlns.addPackageNamespace("fbc", 3)

        self.doc = libsbml.SBMLDocument(sbmlns)
        self._set_fields(self.doc, None)

        # create model
        sbml_model: libsbml.Model = self.model.create_sbml(self.doc)

        if Package.COMP_V1 in self.model.packages:
            self.doc.setPackageRequired("comp", True)
        if (Package.FBC_V2 in self.model.packages) or (
            Package.FBC_V3 in self.model.packages
        ):
            self.doc.setPackageRequired("fbc", False)
            fbc_plugin = sbml_model.getPlugin("fbc")
            fbc_plugin.setStrict(False)
        if Package.DISTRIB_V1 in self.model.packages:
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
    """Data structure for model creation."""

    model: Model
    sbml_path: Path
    antimony_path: Path | None = None
    markdown_path: Path | None = None


def create_model(
    model: Model | Iterable[Model],
    filepath: Path,
    sbml_level: int = SBML_LEVEL,
    sbml_version: int = SBML_VERSION,
    validate: bool = True,
    validation_options: ValidationOptions | None = None,
    show_sbml: bool = False,
    annotations: Path | None = None,
    create_antimony: bool = False,
    create_markdown: bool = False,
) -> FactoryResult:
    """Create SBML model from models.

    This is the entry point for creating models. If multiple models are provided
    these are merged in the process of model creation. See `merge_models` for more
    details.

    Additional model annotations can be provided via a file.

    The created SBML can be serialized to additional formats for inspection, which
    are written next to the SBML file: the antimony serialization of the model
    (`create_antimony`, `*.ant`) and the markdown overview of the ODE system
    (`create_markdown`, `*.md`, see `sbmlutils.converters.odefac`).

    :param model: Model or iterable of Model instances which are merged in single model
    :param filepath: Path to write the SBML model to
    :param sbml_level: set SBML level for model generation
    :param sbml_version: set SBML version for model generation
    :param validate: boolean flag to validate the SBML file
    :param validation_options: options for model validation
    :param show_sbml: boolean flag to show SBML
    :param annotations: Path to annotations file
    :param create_antimony: write the antimony serialization to `*.ant`
    :param create_markdown: write the markdown overview of the ODE system to `*.md`

    :return: FactoryResult
    """
    console.rule(title="Create SBML", style="white")
    if validation_options is None:
        validation_options = ValidationOptions()

    # merge models (a Model is iterable itself, so it is checked first)
    m: Model
    if isinstance(model, Model):
        m = model
    elif isinstance(model, Iterable):
        m = Model.merge_models(model)
    else:
        raise ValueError(f"Unsupported `model` type: {type(model)}")

    # create and write SBML
    doc: libsbml.SBMLDocument = Document(
        model=m,
        sbml_level=sbml_level,
        sbml_version=sbml_version,
    ).create_sbml()

    write_sbml(
        doc=doc,
        filepath=filepath,
        validate=validate,
        validation_options=validation_options,
    )

    # annotation of model (overwrites file)
    if annotations is not None:
        annotator.annotate_sbml(
            source=filepath, annotations_path=annotations, filepath=filepath
        )

    # additional serializations (from the final file, including the annotations)
    antimony_path: Path | None = None
    if create_antimony:
        antimony_path = filepath.with_suffix(".ant")
        antimony_path.write_text(sbml_to_antimony(filepath), encoding="utf-8")
        logger.info("Antimony written to '%s'", antimony_path)

    markdown_path: Path | None = None
    if create_markdown:
        markdown_path = filepath.with_suffix(".md")
        SBML2ODE.from_file(filepath).to_markdown(md_file=markdown_path)
        logger.info("Markdown written to '%s'", markdown_path)

    console.rule(style="white")

    # print created sbml
    if show_sbml:
        with open(filepath, encoding="utf-8") as f_sbml:
            sbml_str = f_sbml.read()

        console.log(sbml_str)

    console.rule(style="white")
    return FactoryResult(
        sbml_path=filepath,
        model=m,
        antimony_path=antimony_path,
        markdown_path=markdown_path,
    )
