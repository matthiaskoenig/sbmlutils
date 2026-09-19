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
import numbers
import re
from collections import namedtuple
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import UnionType
from typing import (
    Any,
    ClassVar,
    Literal,
    TypeAlias,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import libsbml
import numpy as np
import xmltodict
from numpy import nan as NaN
from pint import UndefinedUnitError, UnitRegistry
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
from sbmlutils.notes import Notes, NotesFormat, detect_format
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
    "Delay",
    "Deletion",
    "Document",
    "Event",
    "EventAssignment",
    "ExchangeReaction",
    "ExternalModelDefinition",
    "FactoryResult",
    "FluxObjective",
    "Formula",
    "Function",
    "GeneProduct",
    "InitialAssignment",
    "KeyValuePair",
    "KineticLaw",
    "LocalParameter",
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
    "Priority",
    "RateRule",
    "Reaction",
    "ReactionEquation",
    "ReplacedBy",
    "ReplacedElement",
    "SbaseRef",
    "Species",
    "Submodel",
    "Trigger",
    "UncertParameter",
    "UncertSpan",
    "Uncertainty",
    "Unit",
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

#: libsbml types whose `setId` aliases another attribute, so that the id has to
#: be set through `setIdAttribute`
_ID_ATTRIBUTE_TYPECODES: frozenset[int] = frozenset(
    {
        libsbml.SBML_ASSIGNMENT_RULE,
        libsbml.SBML_RATE_RULE,
        libsbml.SBML_ALGEBRAIC_RULE,
        libsbml.SBML_INITIAL_ASSIGNMENT,
        libsbml.SBML_EVENT_ASSIGNMENT,
    }
)


def _create_object(obj: Any, container: Any) -> libsbml.SBase:
    """Create one object in its container, naming it if the creation fails.

    Args:
        obj: the object to create, e.g. a `Parameter`
        container: what its `create_sbml` takes, the `libsbml.Model` for an
            element of a model and the `libsbml.SBMLDocument` for a
            `ModelDefinition`, which is a child of the `<sbml>` element

    Returns:
        the created libsbml object

    Raises:
        Exception: whatever `create_sbml` raises, after reporting which
            object it was raised for, which the traceback alone does not say
    """
    try:
        return obj.create_sbml(container)
    except Exception as err:
        logger.error("Error creating SBML object for '%s'", obj)
        logger.error(err)
        raise err


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

        sbml_obj: libsbml.SBase = _create_object(obj, model)
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
        # the libsbml parser gives no reason for an empty formula
        reason: str = libsbml.getLastParseL3Error().strip() or "empty formula"
        logger.error("Formula could not be parsed: '%s', %s", formula, reason)
    return ast_node


def _set_math(sbase: Any, math: str | None, model: libsbml.Model) -> None:
    """Set a formula as the math of an element.

    Args:
        sbase: the libsbml object the math is set on, e.g. a
            `libsbml.Trigger`; `libsbml.SBase` itself declares no `setMath`
        math: the math as an SBML L3 formula string; `None` for an element
            without math, which SBML allows from L3V2 on. A formula which does
            not parse is logged as an error by `ast_node_from_formula` and
            leaves the element without math
        model: the libsbml.Model which resolves the ids in the formula
    """
    if math is None:
        return
    ast_node: libsbml.ASTNode | None = ast_node_from_formula(model, math)
    if ast_node is not None:
        check(sbase.setMath(ast_node), f"Set math '{math}' on {sbase.getElementName()}")


UnitType: TypeAlias = "UnitDefinition | str | None"

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


def _xhtml_body_content(xhtml: str) -> str:
    """Extract the inner content of the body of XHTML notes.

    Used to merge two already normalized notes fragments, e.g. a user
    supplied notes body and the `sbmlutils` attribution notes of
    `Document`, into a single body instead of nesting one body inside
    another.

    Args:
        xhtml: XHTML notes, either a body, e.g. `<body xmlns="...">...</body>`,
            or a complete XHTML document rooted at `<html>`, whose `<body>`
            holds the content

    Returns:
        the content between the opening and the closing `body` tag, or an
        empty string if `xhtml` has no closing `</body>` tag, e.g. a
        self-closing `<body/>`
    """
    end = xhtml.rfind("</body>")
    body = xhtml.find("<body")
    if end == -1 or body == -1:
        logger.warning(
            "Notes have no '<body>' with a closing '</body>' tag, treating "
            "their content as empty: '%s'",
            xhtml,
        )
        return ""
    start = xhtml.find(">", body) + 1
    return xhtml[start:end]


def _append_to_xhtml_body(xhtml: str, content: str) -> str:
    """Append content to the end of the body of XHTML notes.

    The notes keep their root: a body stays a body, and a complete XHTML
    document rooted at `<html>` keeps its `<head>`.

    Args:
        xhtml: XHTML notes, either a body or a complete XHTML document rooted
            at `<html>`
        content: the XHTML content to append

    Returns:
        the notes with the content at the end of their body; notes without a
        closing `</body>` tag, e.g. a self-closing `<body/>`, have no content,
        they are replaced by a body which holds only the appended content
    """
    end = xhtml.rfind("</body>")
    if end == -1:
        logger.warning(
            "Notes body has no closing '</body>' tag, treating its content "
            "as empty: '%s'",
            xhtml,
        )
        return f'<body xmlns="http://www.w3.org/1999/xhtml">\n{content}\n</body>'
    return f"{xhtml[:end]}\n{content}\n{xhtml[end:]}"


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
            if Sbase._authoring_hints.get():
                logger.warning(
                    "Model units should be set for a model. These can be stored "
                    "using the 'model_units' on a model definition."
                )
        else:
            for key in ("time", "extent", "substance", "length", "area", "volume"):
                if getattr(model_units, key) is None:
                    if Sbase._authoring_hints.get():
                        # strongly recommended fields warn, optional ones inform
                        logger.log(
                            logging.WARNING
                            if key in ["time", "extent", "substance", "volume"]
                            else logging.INFO,
                            "'%s' should be set in 'model_units'.",
                            key,
                        )

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


def _comp_plugin(sbase: libsbml.SBase, what: str) -> Any:
    """Get the comp plugin of a libsbml object for a port or a replacement.

    Args:
        sbase: the libsbml object, the model for a port, the replaced
            element for a replacement
        what: the port or the replacement, for the error message

    Returns:
        the comp plugin of the libsbml object

    Raises:
        ValueError: if the document does not declare the comp package, which
            `create_model` does for every model with comp content, see
            `Model._has_comp_content`
    """
    plugin = sbase.getPlugin("comp")
    if plugin is None:
        raise ValueError(
            f"{what} needs the comp package, which the document does not declare."
        )
    return plugin


def _iter_sbases(value: Any, seen: set[int] | None = None) -> Iterator[Sbase]:
    """Iterate every `Sbase` reachable from a value, the value included.

    The walk descends into the attributes of every `Sbase` and into lists,
    tuples, sets and the values of dicts. So it finds an element wherever a
    model definition nests it: in a list of the model, among the parameters
    and rules of a reaction, the local parameters of a kinetic law, the
    assignments of an event or the glyphs of a layout.

    Args:
        value: the value to walk, e.g. a `Model`
        seen: the ids of the `Sbase` objects already yielded, which the
            recursion shares; every `Sbase` is yielded once, which also ends
            the walk on a cycle

    Yields:
        every `Sbase` reachable from the value
    """
    if seen is None:
        seen = set()
    if isinstance(value, Sbase):
        if id(value) in seen:
            return
        seen.add(id(value))
        yield value
        for attribute in vars(value).values():
            yield from _iter_sbases(attribute, seen)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _iter_sbases(item, seen)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_sbases(item, seen)


class Sbase:
    """Base class of all SBML objects."""

    def __init__(
        self,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.notes = Sbase._process_notes(notes)
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

    #: the reference a `<comp:port>` names an element of this class by, which
    #: `create_port` fills in for `port=True` and for a `Port` which
    #: references nothing itself. `idRef` names the element by its id, which
    #: comp resolves with `libsbml.Model.getElementBySId`; `unitRef` is for a
    #: `UnitDefinition`, whose ids live in a namespace of their own; and
    #: `metaIdRef` names the element by its metaid, which is how an
    #: `EventAssignment` and a `LocalParameter` are named: measured with
    #: libsbml 5.21.2, `getElementBySId` answers with neither of the two, so a
    #: port naming an event assignment by `comp:idRef` is rejected (libsbml
    #: 1020702) and one naming a local parameter that way makes the flattened
    #: model invalid (1090105), while `comp:metaIdRef` to either validates.
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "idRef"

    #: authoring hints are logged for a hand written model definition, they are
    #: noise for a model which was parsed from a file, see
    #: `Sbase.no_authoring_hints`. A `ContextVar` rather than a class attribute:
    #: the suppression belongs to the code which writes one model, and a class
    #: attribute is shared by every thread, so writing a parsed model in one
    #: thread silenced the hints of a model definition written in another. A
    #: thread starts with a fresh context, in which this holds its default.
    _authoring_hints: ClassVar[ContextVar[bool]] = ContextVar(
        "sbmlutils_authoring_hints", default=True
    )

    @staticmethod
    @contextmanager
    def no_authoring_hints() -> Iterator[None]:
        """Suppress the hints about a hand written element inside the context.

        The `name` and `sboTerm` hints of `_set_fields` help somebody writing
        a model definition. They are noise when a model is written back out
        after it was parsed from a file, which is what `sbmlutils.parser`
        does, and when the element is built by this module rather than by
        hand, see `_UncertChild._check_states_a_value`.

        Yields:
            None
        """
        token = Sbase._authoring_hints.set(False)
        try:
            yield
        finally:
            Sbase._authoring_hints.reset(token)

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

    @staticmethod
    def _process_notes(notes: str | Notes | None) -> str | None:
        """Normalize notes to an XHTML body string.

        Notes are stored as XHTML so that a round trip is a fixed point:
        markdown is rendered once here, and notes which came from an SBML
        document are stored verbatim instead of being run through the
        markdown renderer, which would mutate them.

        Args:
            notes: the notes as markdown, as XHTML, or as a `Notes` object
                which states its format explicitly

        Returns:
            the XHTML body of the notes, `None` if no notes were given
        """
        if notes is None:
            return None
        if isinstance(notes, Notes):
            return str(notes)
        if not notes.strip():
            return None
        return str(Notes(notes, format=detect_format(notes)))

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
            # libsbml aliases setId to the variable/symbol attribute on rules,
            # initial assignments and event assignments, where it is a no-op;
            # setIdAttribute is the accessor which actually sets the id
            if sbase.getTypeCode() in _ID_ATTRIBUTE_TYPECODES:
                check(
                    sbase.setIdAttribute(self.sid),
                    f"Set id '{self.sid}' on {sbase}",
                )
            else:
                status: int = sbase.setId(self.sid)
                if status == libsbml.LIBSBML_UNEXPECTED_ATTRIBUTE and (
                    sbase.getLevel(),
                    sbase.getVersion(),
                ) < (3, 2):
                    # many elements only have an id from SBML L3V2 on, e.g. a
                    # constraint or a kinetic law; below it the id has no
                    # place in the document, which the caller cannot change
                    logger.debug(
                        "'%s' has no id in SBML L%sV%s, id '%s' is not written.",
                        sbase.getElementName(),
                        sbase.getLevel(),
                        sbase.getVersion(),
                        self.sid,
                    )
                else:
                    check(status, f"Set id '{self.sid}' on {sbase}")
        if self.name is not None:
            sbase.setName(self.name)
        elif Sbase._authoring_hints.get() and not isinstance(
            self,
            (
                Document,
                Port,
                ReplacedBy,
                ReplacedElement,
                AssignmentRule,
                EventAssignment,
                # identified by its key and its value; an fbc version 2
                # document cannot carry its name at all
                KeyValuePair,
                # created from a formula string in the authoring style, which
                # has no place for their name or sboTerm
                KineticLaw,
                Trigger,
                Priority,
                Delay,
                # identified by their type and their value, a name and an
                # sboTerm are unusual on them
                UncertParameter,
                UncertSpan,
            ),
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
        elif Sbase._authoring_hints.get() and not isinstance(
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
                EventAssignment,
                KeyValuePair,
                KineticLaw,
                Trigger,
                Priority,
                Delay,
                UncertParameter,
                UncertSpan,
            ),
        ):
            logger.warning("'sboTerm' should be set on '%s'", self)
        if self.metaId is not None:
            sbase.setMetaId(self.metaId)

        if self.notes is not None and self.notes.strip():
            # notes are normalized to xhtml by `Sbase._process_notes`
            set_notes(sbase, self.notes, format=NotesFormat.HTML)

        # annotation handling
        processed_annotations: list[Annotation] = []
        if self.annotations:
            # annotations can have been added after initial processing
            processed_annotations = Sbase._process_annotations(self.annotations)

        for annotation in processed_annotations:
            annotator.ModelAnnotator.annotate_sbase(sbase=sbase, annotation=annotation)

        if model:
            self.create_uncertainties(sbase, model)
            self.create_replaced_by(sbase, model)

        if self.keyValuePairs is not None:
            self.create_key_value_pairs(sbase, model)

    def create_port(self, model: libsbml.Model | None) -> libsbml.Port | None:
        """Create the port of the element, if it has one.

        A port which references nothing of its own is made to reference this
        element, by the reference `_port_reference` names for the class: its
        id, its unit id or its metaid. An element which has no such name
        cannot be referenced and gets no port, which is reported.

        Args:
            model: the model the port is created in; `None` for an element
                which is written without one, which is reported, since a port
                lives in the `<comp:listOfPorts>` of a model

        Returns:
            the port, `None` if the element has no port, no model to create it
            in or no name which the port could reference

        Raises:
            ValueError: if the document does not declare the comp package
        """
        if self.port is None or self.port is False:
            return None
        if model is None:
            logger.error(
                "'%s' is written without a model, its port is not created.",
                self,
            )
            return None

        reference = self._port_reference
        # the name the port references this element by; `unitRef` names a
        # unit definition by its id like `idRef` does, in the namespace of
        # the unit definitions of the model
        target: str | None = self.metaId if reference == "metaIdRef" else self.sid

        references_self = isinstance(self.port, bool) or not (
            self.port.portRef
            or self.port.idRef
            or self.port.unitRef
            or self.port.metaIdRef
        )
        if references_self and target is None:
            logger.error(
                "'%s' has no %s for its port to reference, no port is created.",
                self,
                "metaid" if reference == "metaIdRef" else "id",
            )
            return None

        p: libsbml.Port | None = None
        if isinstance(self.port, bool):
            if self.port is True:
                # manually create port for this element
                cmodel: libsbml.CompModelPlugin = _comp_plugin(
                    model, f"The port of {type(self).__name__} '{self.sid}'"
                )
                p = cmodel.createPort()
                suffix = PORT_UNIT_SUFFIX if reference == "unitRef" else PORT_SUFFIX
                # the id of the element where it has one, so that the port of
                # an element named by its metaid is still named after it
                port_sid = f"{self.sid if self.sid is not None else target}{suffix}"
                p.setId(port_sid)
                p.setName(f"Port of {self.sid if self.sid is not None else target}")
                p.setMetaId(port_sid)
                sbo = SBO.PORT.curie
                p.setSBOTerm(sbo)

                if reference == "unitRef":
                    p.setUnitRef(target)
                elif reference == "metaIdRef":
                    p.setMetaIdRef(target)
                else:
                    p.setIdRef(target)
        else:
            # use the port object
            if references_self:
                # if no reference set the reference of this class to it
                if reference == "unitRef":
                    self.port.unitRef = target
                elif reference == "metaIdRef":
                    self.port.metaIdRef = target
                else:
                    self.port.idRef = target
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
        self, sbase: libsbml.SBase, model: libsbml.Model | None
    ) -> list[libsbml.KeyValuePair] | None:
        """Create the fbc:keyValuePair elements of the element.

        Args:
            sbase: the libsbml object the pairs are created on
            model: the `libsbml.Model` the element belongs to, which the port
                of a pair is created in; `None` for an element written
                without one

        Returns:
            the created pairs, `None` if the element has none
        """
        if not self.keyValuePairs:
            return None

        kvps: list[libsbml.KeyValuePair] = []
        for kvp in self.keyValuePairs:
            kvps.append(kvp.create_sbml(sbase, model))
        return kvps


class KeyValuePair(Sbase):
    """A key-value pair of fbc version 3, which every element can carry.

    An fbc version 3 `<fbc:keyValuePair>` carries its `key`, `value` and
    `uri` and, like every other `SBase`, an id, a name, a metaid, an sboTerm,
    notes and annotations; all of them are written and the document
    validates. Measured with libsbml 5.21.2, on a document built with libsbml
    alone, two of them survive a re-read only in part:

    - the `id` and the `name` are read back from an SBML **L3V2** document
      and not from an L3V1 one, although libsbml writes them into both,
    - a pair in an **fbc version 2** document keeps only the metaid, the
      sboTerm, the notes and the annotation: libsbml writes no `key`,
      `value`, `uri`, `id` or `name` there, and `setId`/`setName` answer with
      `LIBSBML_UNEXPECTED_ATTRIBUTE`, which `check()` reports.

    Both are properties of libsbml's reader, not of the document: what is
    written is in the file either way.

    Neither `uncertainties` nor a nested list of `keyValuePairs` is offered:
    libsbml creates both on the plugins of a `<fbc:keyValuePair>` without an
    error and writes neither into the XML. A `replacedBy` is not offered
    either, since libsbml attaches no `CompSBasePlugin` to the element, see
    `sbmlutils.parser._drop_replaced_by`.
    """

    def __init__(
        self,
        key: str,
        value: str | None,
        uri: str | None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        notes: str | Notes | None = None,
        annotations: OptionalAnnotationsType = None,
        port: Any = None,
    ):
        """Create a KeyValuePair.

        Args:
            key: the key of the pair, which is required
            value: the value of the pair
            uri: the URI which defines the meaning of the key
            sid: optional SId, written as `fbc:id`
            name: optional SBML name, written as `fbc:name`
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            notes: optional notes, as markdown, XHTML or a `Notes` object
            annotations: optional RDF annotations
            port: optional comp port, which names the pair by its id
        """
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            port=port,
        )
        self.key = key
        self.value = value
        self.uri = uri

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model | None = None
    ) -> libsbml.KeyValuePair:
        """Create the libsbml.KeyValuePair on the given element.

        Args:
            sbase: the libsbml object the pair is created on
            model: the libsbml.Model the element belongs to, which the port of
                the pair is created in. It has to be handed down, since
                libsbml answers `getModel()` of an element inside a
                `<comp:modelDefinition>` with the model of the *document*, see
                `Model._fill_sbml`. `None` is for a caller which writes a pair
                without a model, which is reported if the pair has a port

        Returns:
            the created libsbml.KeyValuePair
        """
        sbase_fbc: libsbml.FbcSBasePlugin = sbase.getPlugin("fbc")
        kvp_list: libsbml.ListOfKeyValuePairs = sbase_fbc.getListOfKeyValuePairs()
        kvp_list.setXmlns("http://sbml.org/fbc/keyvaluepair")
        kvp: libsbml.KeyValuePair = kvp_list.createKeyValuePair()
        self._set_fields(kvp, model)
        self.create_port(model)
        check(kvp.setKey(self.key), "Set Key on KeyValuePair")
        if self.value is not None:
            check(kvp.setValue(self.value), f"Set `value={self.value}` on KeyValuePair")
        if self.uri is not None:
            check(kvp.setUri(self.uri), f"Set `uri={self.uri}` on KeyValuePair")

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
        notes: str | Notes | None = None,
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


class Unit:
    """A single unit of a `UnitDefinition`.

    Corresponds to the information in a `libsbml.Unit`, i.e. one factor of a
    unit definition. An SBML unit is `multiplier * 10^scale * kind^exponent`.
    """

    def __init__(
        self,
        kind: str,
        exponent: float = 1.0,
        scale: int = 0,
        multiplier: float = 1.0,
    ):
        """Construct a Unit.

        Args:
            kind: the SBML unit kind, e.g. `"litre"`
            exponent: the exponent of the unit
            scale: the decimal scale of the unit
            multiplier: the multiplier of the unit
        """
        self.kind = kind
        self.exponent = exponent
        self.scale = scale
        self.multiplier = multiplier

    def __repr__(self) -> str:
        """Get string representation."""
        return (
            f"Unit({self.kind}, exponent={self.exponent}, "
            f"scale={self.scale}, multiplier={self.multiplier})"
        )

    def __eq__(self, other: object) -> bool:
        """Compare two units."""
        if not isinstance(other, Unit):
            return NotImplemented
        return (
            self.kind == other.kind
            and self.exponent == other.exponent
            and self.scale == other.scale
            and self.multiplier == other.multiplier
        )

    def __hash__(self) -> int:
        """Get hash of the unit."""
        return hash((self.kind, self.exponent, self.scale, self.multiplier))

    def create_sbml(self, udef: libsbml.UnitDefinition) -> libsbml.Unit:
        """Create the libsbml.Unit in the given libsbml.UnitDefinition.

        Args:
            udef: the libsbml.UnitDefinition the unit is created in

        Returns:
            the created libsbml.Unit
        """
        unit: libsbml.Unit = udef.createUnit()
        kind: int = libsbml.UnitKind_forName(self.kind)
        if kind == libsbml.UNIT_KIND_INVALID:
            logger.error("'%s' is not a valid SBML unit kind.", self.kind)
        check(unit.setKind(kind), f"Set kind '{self.kind}' on unit")
        check(unit.setExponent(float(self.exponent)), "Set exponent on unit")
        check(unit.setScale(int(self.scale)), "Set scale on unit")
        check(unit.setMultiplier(float(self.multiplier)), "Set multiplier on unit")
        return unit


class UnitDefinition(Sbase):
    """Unit.

    Corresponds to the information in the libsbml.UnitDefinition.
    """

    # definition: str = (None,)

    #: the unit definitions of a model live in a namespace of their own, which
    #: comp names by `comp:unitRef`, see `Sbase._port_reference`
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "unitRef"

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
        units: list[Unit] | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        replacedBy: Any | None = None,
    ):
        """Construct UnitDefinition.

        A unit definition is either written as a pint expression in
        `definition`, which is the authoring style, or as the explicit list of
        `units` it consists of, which is what the parser reads from a file.

        Args:
            sid: the id of the unit definition
            definition: the pint expression, e.g. `"mmole/liter"`; defaults to
                `sid`
            units: the explicit units of the definition; they take precedence
                over `definition`
            name: the name of the unit definition
            sboTerm: the SBO term of the unit definition
            metaId: the meta id of the unit definition
            annotations: the annotations of the unit definition
            notes: the notes of the unit definition
            keyValuePairs: the key value pairs of the unit definition
            port: the port of the unit definition
            replacedBy: the comp ReplacedBy of the unit definition
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
            replacedBy=replacedBy,
        )

        self.units = units
        self.definition = definition if definition is not None else sid
        if not self.name and units is None:
            # the pint expression is the readable label of the definition; with
            # explicit units the definition is only the id and would make a
            # meaningless name
            self.name = self.definition

    def create_sbml(self, model: libsbml.Model) -> libsbml.UnitDefinition | None:
        """Create libsbml.UnitDefinition.

        Args:
            model: the libsbml.Model the unit definition is created in

        Returns:
            the created libsbml.UnitDefinition, `None` for a base unit kind
        """
        if self.units is None and isinstance(self.definition, int):
            # libsbml unit kind, the unit definition is a base unit
            return None

        obj: libsbml.UnitDefinition = model.createUnitDefinition()

        units = self.units if self.units is not None else self._units_from_definition()
        for unit in units:
            unit.create_sbml(obj)

        self._set_fields(obj, model)
        self.create_port(model)
        return obj

    def _units_from_definition(self) -> list[Unit]:
        """Compile the pint definition string into explicit units.

        Returns:
            the units the pint expression of `definition` resolves to

        Raises:
            UndefinedUnitError: if the expression is not valid pint syntax
            ValueError: if a unit of the expression has no SBML unit kind
        """
        # parse the string into pint
        try:
            quantity = Q_(self.definition)
        except UndefinedUnitError as err:
            console.print_exception(show_locals=False)
            logger.error(
                "Unit definition '%s' is not valid pint syntax, %s.",
                self.definition,
                err,
            )
            raise err

        magnitude, units_tuple = quantity.to_tuple()
        # pint types the units as a fixed length tuple, it is empty for a number
        units: list[Sequence[Any]] = list(units_tuple)

        sbml_units: list[Unit] = []
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

                # the pint path cannot resolve a scale, it is part of the
                # multiplier; only a parsed unit definition carries a scale
                scale = 0
                # resolve the kind (this is already a unit known by libsbml)
                kind = self.__class__._pint2sbml.get(unit_name, None)
                if kind is None:
                    # we have to bring the unit to base units
                    uq = Q_(unit_name).to_base_units()
                    multiplier = multiplier * uq.magnitude
                    kind = self.__class__._pint2sbml.get(str(uq.units), None)
                    if kind is None:
                        msg = (
                            f"Unit '{uq.units}' in definition "
                            f"'{self.definition}' could not be converted to SBML."
                        )
                        logger.error(msg)
                        raise ValueError(msg)

                sbml_units.append(
                    Unit(
                        kind=libsbml.UnitKind_toString(kind),
                        exponent=exponent,
                        scale=scale,
                        multiplier=float(multiplier),
                    )
                )
        else:
            # only magnitude (units canceled)
            kind = self.__class__._pint2sbml["dimensionless"]
            sbml_units.append(
                Unit(
                    kind=libsbml.UnitKind_toString(kind),
                    exponent=1.0,
                    scale=0,
                    multiplier=float(magnitude),
                )
            )

        return sbml_units

    def _set_fields(self, sbase: libsbml.UnitDefinition, model: libsbml.Model) -> None:
        """Set fields on libsbml.UnitDefinition."""
        super()._set_fields(sbase, model)

    @staticmethod
    def get_uid_for_unit(unit: UnitDefinition | str | None) -> str | None:
        """Get unit id for the given unit.

        Args:
            unit: a UnitDefinition or the id of one

        Returns:
            the unit id, `None` if no unit was given

        Raises:
            ValueError: if the unit is neither a `UnitDefinition` nor a unit
                id; the value would otherwise reach a libsbml setter and
                surface as a SWIG `TypeError` which names neither the value
                nor the element it was set on
        """
        if unit is None:
            return None
        if isinstance(unit, UnitDefinition):
            return unit.sid
        if not isinstance(unit, str):
            raise ValueError(
                f"A unit must be a UnitDefinition or the id of one, but "
                f"'{unit}' is '{type(unit)}'."
            )
        return unit


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
        """Create the libsbml.UnitDefinitions in the model.

        Deprecated, `Model` normalizes its units to a list of
        `UnitDefinition` and creates them directly.

        Args:
            model: the libsbml.Model the unit definitions are created in
        """
        for udef in Model._normalize_units(cls):
            udef.create_sbml(model=model)


def _check_unit_type(unit: Any, attribute: str, owner: object) -> None:
    """Warn if a unit attribute is neither a `UnitDefinition` nor a unit id.

    The value is passed on either way, `UnitDefinition.get_uid_for_unit`
    refuses it when the element is written. The warning is the early hint
    which names the attribute and the element it was given on.

    Args:
        unit: the value given for the unit attribute
        attribute: the name of the attribute, e.g. `substanceUnit`
        owner: the element the attribute belongs to, which the warning names
    """
    if unit is not None and not isinstance(unit, (UnitDefinition, str)):
        logger.warning(
            "'%s' must be a UnitDefinition or a unit id, but '%s' in '%s' is '%s'.",
            attribute,
            unit,
            owner,
            type(unit),
        )


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
        sid: str | None,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
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
        _check_unit_type(self.unit, "unit", self)

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

    A value of `None` is a function definition without math, which SBML
    allows from L3V2 on.
    """

    def __init__(
        self,
        sid: str,
        value: str | None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
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
        if self.formula is not None:
            sbase.setMath(ast_node_from_formula(model, self.formula))


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
        notes: str | Notes | None = None,
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
            # an unset value stays unset, it is not invented as NaN
            pass
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


class LocalParameter(ValueWithUnit):
    """LocalParameter of a KineticLaw.

    A local parameter is scoped to the kinetic law it is defined in, unlike a
    `Parameter`, which is global to the model. Its id is scoped with it:
    `libsbml.Model.getElementBySId`, which comp resolves a `comp:idRef` with,
    does not answer with a local parameter, so a `<comp:port>` names one by
    its metaid, see `Sbase._port_reference`.

    A `<comp:replacedBy>` is not offered. libsbml writes one on a
    `<localParameter>` and reads it back, but no such replacement is valid,
    whichever way it names the element it is replaced by (measured with
    libsbml 5.21.2): naming the local parameter of the submodel, by
    `comp:metaIdRef` or through a `<comp:port>` of the submodel, makes the
    flattened model invalid (libsbml 10216, "Cannot use a KineticLaw local
    parameter outside of its local scope"), `comp:idRef` cannot name a local
    parameter at all (1020702), and naming anything else is a class mismatch
    (1021201, 1021203).
    """

    #: the identifier is required, unlike on `Sbase`
    sid: str

    #: the id of a local parameter is scoped to its kinetic law, see the
    #: class docstring
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "metaIdRef"

    def __init__(
        self,
        sid: str,
        value: str | float | None = None,
        unit: UnitType = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
    ):
        """Construct LocalParameter.

        Args:
            sid: the SId of the local parameter, which is required
            value: the value of the local parameter
            unit: the unit of the value
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid, which a `<comp:port>` of the local
                parameter references it by
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port, which names the local parameter by its
                metaid
            uncertainties: optional distrib uncertainties
        """
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
        )

    def create_sbml(
        self, klaw: libsbml.KineticLaw, model: libsbml.Model | None = None
    ) -> libsbml.LocalParameter:
        """Create the libsbml.LocalParameter in the given kinetic law.

        Args:
            klaw: the libsbml.KineticLaw the local parameter is created in
            model: the libsbml.Model the kinetic law is created in, which
                the port and the uncertainties of the local parameter are
                created in. It has to be handed down, since libsbml answers
                `klaw.getModel()` with the model of the *document* for a
                kinetic law inside a `<comp:modelDefinition>`, see
                `Model._fill_sbml`. `None` falls back to that lookup, for a
                caller which creates a local parameter in a kinetic law of the
                model of a document, where the two are the same model

        Returns:
            the created libsbml.LocalParameter
        """
        if model is None:
            model = klaw.getModel()
        lp: libsbml.LocalParameter = klaw.createLocalParameter()
        self._set_fields(lp, model)
        self.create_port(model)
        if self.value is not None:
            check(lp.setValue(float(self.value)), f"Set value on '{self.sid}'")
        return lp

    def _set_fields(self, sbase: libsbml.LocalParameter, model: libsbml.Model) -> None:
        """Set fields on libsbml.LocalParameter."""
        super()._set_fields(sbase, model)


class Compartment(ValueWithUnit):
    """Compartment."""

    #: the identifier is required, unlike on `Sbase`
    sid: str

    def __init__(
        self,
        sid: str,
        value: str | float | None,
        unit: UnitType = None,
        constant: bool = True,
        spatialDimensions: float | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
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
            # an unset size stays unset, it is not invented as NaN
            pass
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
        if self.spatialDimensions is not None:
            check(
                sbase.setSpatialDimensions(self.spatialDimensions),
                f"Set spatialDimensions on '{self.sid}'",
            )


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
        notes: str | Notes | None = None,
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
        _check_unit_type(self.substanceUnits, "substanceUnit", self)
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
                    self._set_charge(obj_fbc)
                if self.chemicalFormula is not None:
                    obj_fbc.setChemicalFormula(self.chemicalFormula)

    def _set_charge(self, species_fbc: libsbml.FbcSpeciesPlugin) -> None:
        """Set the fbc charge as the fbc version of the document writes it.

        libsbml keeps the integer `fbc:charge` of fbc version 2 and the double
        `fbc:charge` of fbc version 3 apart: it writes only the one of the
        version of the document, and the getter of the other one returns 0.
        `FbcSpeciesPlugin.setCharge` picks which of the two it sets from the
        python type of its argument, an `int` the fbc version 2 charge and a
        `float` the fbc version 3 one, so the charge is passed as the type the
        version of the plugin writes. The version is read from the plugin of
        the created species, which is the version of the document being
        written, rather than from the packages of the `Model`.

        fbc version 2 has no charge which is not a whole number, so such a
        charge cannot be written into a document of that version at all. It is
        reported and left unset rather than rounded, which would write a
        charge the model never stated.

        Args:
            species_fbc: the fbc plugin of the created libsbml.Species
        """
        if self.charge is None:
            return
        if species_fbc.getPackageVersion() >= 3:
            check(
                species_fbc.setCharge(float(self.charge)),
                f"Set charge '{self.charge}' on species '{self.sid}'",
            )
        elif float(self.charge).is_integer():
            check(
                species_fbc.setCharge(int(self.charge)),
                f"Set charge '{self.charge}' on species '{self.sid}'",
            )
        else:
            logger.error(
                "Species '%s' has the charge %s, which fbc version 2 cannot "
                "express: its 'fbc:charge' is an integer. The charge is not "
                "written; use `Package.FBC_V3` for a model with such a charge.",
                self.sid,
                self.charge,
            )


class InitialAssignment(Value):
    """InitialAssignments.

    The unit attribute is only for the case where a parameter must be created
    (which has the unit). In case of an initialAssignment of a value the units
    have to be defined in the math. A value of `None` is an initial assignment
    without math, which SBML allows from L3V2 on.
    """

    def __init__(
        self,
        symbol: str,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
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
        if self.value is not None:
            obj.setMath(ast_node_from_formula(model, str(self.value)))

        self.create_port(model)
        return obj


class RuleWithVariable:
    """Rule."""

    variable: str
    value: str | float | None
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
    have to be defined in the math. A value of `None` is a rule without math,
    which SBML allows from L3V2 on.
    """

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.variable} = {self.value} [{self.unit}]"

    def __init__(
        self,
        variable: str,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct AssignmentRule."""
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
        self.variable: str = variable

    def create_sbml(self, model: libsbml.Model) -> libsbml.AssignmentRule:
        """Create AssignmentRule."""
        self.check_model_for_rule(model)
        obj: libsbml.AssignmentRule = model.createAssignmentRule()
        self._set_fields(obj, model)
        obj.setVariable(self.variable)
        if self.value is not None:
            obj.setMath(ast_node_from_formula(model, str(self.value)))
        self.create_port(model)
        return obj


class RateRule(ValueWithUnit, RuleWithVariable):
    """RateRule.

    A value of `None` is a rule without math, which SBML allows from L3V2 on.
    """

    def __repr__(self) -> str:
        """Get string representation."""
        return f"d{self.variable}/dt = {self.value} [{self.unit}]"

    def __init__(
        self,
        variable: str,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct RateRule."""
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
        self.variable: str = variable

    def create_sbml(self, model: libsbml.Model) -> libsbml.RateRule:
        """Create RateRule."""
        self.check_model_for_rule(model)
        obj: libsbml.RateRule = model.createRateRule()
        self._set_fields(obj, model)
        obj.setVariable(self.variable)
        if self.value is not None:
            obj.setMath(ast_node_from_formula(model, str(self.value)))
        self.create_port(model)
        return obj


class AlgebraicRule(ValueWithUnit, RuleWithVariable):
    """AlgebraicRule.

    A value of `None` is a rule without math, which SBML allows from L3V2 on.
    """

    def __repr__(self) -> str:
        """Get string representation."""
        return f"0 = {self.value} [{self.unit}]"

    def __init__(
        self,
        sid: str | None,
        value: str | float | None,
        unit: UnitType = Units.dimensionless,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
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
        if self.value is not None:
            rule.setMath(ast_node_from_formula(model, str(self.value)))
        self.create_port(model)
        return rule


#: deprecated, a kinetic law is a `KineticLaw`; still accepted by
#: `Reaction._process_formula`
Formula = namedtuple("Formula", "value unit")


class KineticLaw(Sbase):
    """KineticLaw of a Reaction.

    Corresponds to the information in a `libsbml.KineticLaw`: the rate math,
    and the local parameters which are scoped to it.
    """

    def __init__(
        self,
        math: str | None,
        unit: UnitType = None,
        local_parameters: list[LocalParameter] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct a KineticLaw.

        Args:
            math: the rate expression, as an SBML L3 formula string; `None`
                for a kinetic law without math, which SBML allows from L3V2 on
            unit: the unit of the rate; never written to XML in any
                level/version this package currently emits (it existed on
                `libsbml.KineticLaw` only in L1V1, L1V2 and L2V1, and this
                package never wrote it even then). Kept as python state for a
                `KineticLaw` parsed from such an old document, since a future
                write-back needs somewhere to hold it
            local_parameters: the parameters scoped to this kinetic law
            sid: optional SId, kinetic laws only carry one since SBML L3V2;
                not written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
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
        self.math = math
        self.unit = unit
        self.local_parameters = local_parameters if local_parameters else []

    def __repr__(self) -> str:
        """Get string representation."""
        return f"KineticLaw({self.math})"

    def create_sbml(
        self, reaction: libsbml.Reaction, model: libsbml.Model | None = None
    ) -> libsbml.KineticLaw:
        """Create the libsbml.KineticLaw on the given reaction.

        Args:
            reaction: the libsbml.Reaction the kinetic law belongs to
            model: the libsbml.Model the reaction is created in, which the
                math is parsed against and which the port, the uncertainties
                and the replacedBy of the kinetic law and of its local
                parameters are created in. It has to be handed down, since
                libsbml answers `reaction.getModel()` with the model of the
                *document* for a reaction inside a `<comp:modelDefinition>`,
                see `Model._fill_sbml`. `None` falls back to that lookup, for
                a caller which creates a kinetic law on a reaction of the
                model of a document, where the two are the same model

        Returns:
            the created libsbml.KineticLaw
        """
        if model is None:
            model = reaction.getModel()
        klaw: libsbml.KineticLaw = reaction.createKineticLaw()
        self._set_fields(klaw, model)
        self.create_port(model)

        # local parameters must exist before the math is parsed, so that the
        # formula parser resolves their ids
        for local_parameter in self.local_parameters:
            local_parameter.create_sbml(klaw, model)

        if self.math is None:
            return klaw
        ast_node = libsbml.parseL3FormulaWithModel(self.math, model)
        if ast_node is None:
            logger.error(
                "Kinetic law math could not be parsed: '%s', %s",
                self.math,
                libsbml.getLastParseL3Error(),
            )
        else:
            check(klaw.setMath(ast_node), f"Set math on kinetic law '{self.math}'")
        return klaw


#: a token of an infix gene product association: a run of characters which is
#: neither whitespace nor a parenthesis, so that the string is split on both
_ASSOCIATION_TOKEN: re.Pattern[str] = re.compile(r"[^\s()]+")

#: the operators of an infix gene product association, in the two spellings
#: libsbml's own infix parser accepts for each of them; every other token of an
#: association is a gene product id
_ASSOCIATION_OPERATORS: frozenset[str] = frozenset({"and", "AND", "or", "OR"})


def _gene_product_ids(association: str) -> list[str]:
    """Get the gene products an infix gene product association references.

    The association is split into tokens on whitespace and on parentheses, and
    every token which is not an operator is a gene product id. Only a whole
    token is an operator: an id such as `ORF1`, `brandy` or `sensor` carries
    the letters of one inside it and is a gene product like any other.

    Args:
        association: the association as an infix string of gene product ids,
            e.g. `(ORF1 and b0001) or b0002`

    Returns:
        the id of every gene product the association references, in the order
        of the string and with a repeated id repeated
    """
    return [
        token
        for token in _ASSOCIATION_TOKEN.findall(association)
        if token not in _ASSOCIATION_OPERATORS
    ]


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
        formula: KineticLaw | Formula | tuple[str, UnitType] | str | None = None,
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
        notes: str | Notes | None = None,
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
        formula: KineticLaw | Formula | tuple[str, UnitType] | str | None,
    ) -> KineticLaw | None:
        """Process the reaction formula into a KineticLaw.

        Args:
            formula: a KineticLaw, a `(math, unit)` tuple, a math string, or
                None

        Returns:
            the kinetic law of the reaction, None if no formula was given

        Raises:
            ValueError: if the formula is of an unsupported type
        """
        if formula is None:
            return None
        if isinstance(formula, KineticLaw):
            return formula
        if isinstance(formula, str):
            return KineticLaw(math=formula)
        if isinstance(formula, (tuple, list)):
            math, unit = formula
            return KineticLaw(math=math, unit=unit)
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
            sref: libsbml.SpeciesReference | libsbml.ModifierSpeciesReference,
            part: EquationPart,
        ) -> None:
            """Set the fields on the SpeciesReference.

            A `libsbml.ModifierSpeciesReference` has no `constant` or
            `stoichiometry` attribute (only its sibling `SpeciesReference`,
            used for reactants and products, does), so those two are only
            set when `sref` actually is one. Everything else an `SBase`
            carries, the key-value pairs of fbc version 3 included, is
            written for all three roles alike.
            """
            if part.species is not None:
                sref.setSpecies(part.species)
            if part.sid is not None:
                sref.setId(part.sid)
            if isinstance(sref, libsbml.SpeciesReference):
                if part.constant is not None:
                    sref.setConstant(part.constant)
                if part.stoichiometry is not None:
                    sref.setStoichiometry(part.stoichiometry)
            if part.metaId is not None:
                sref.setMetaId(part.metaId)
            if part.sboTerm is not None:
                sref.setSBOTerm(part.sboTerm)
            if part.name is not None:
                # `SimpleSpeciesReference::setName` (libsbml 5.21.1)
                # erroneously applies SId syntax validation to `name`,
                # which SBML L3 defines as a plain `string`, not an `SId`;
                # `Species.setName`/`Reaction.setName` do not do this.
                # Verified live: `SpeciesReference.setName('reactant
                # name')` returns rc=-4 (LIBSBML_INVALID_ATTRIBUTE_VALUE)
                # and leaves `getName()` empty, while
                # `SpeciesReference.setName('reactantname')` (no space)
                # returns rc=0 and is set; `Species.setName('a species
                # name')` (the control) returns rc=0. This is a libsbml
                # defect specific to `SimpleSpeciesReference` (the base of
                # both `SpeciesReference` and `ModifierSpeciesReference`),
                # not a bug in this package, and there is nothing correct
                # to do about it here short of mangling the name, which
                # this deliberately does not do. Logged as a warning
                # rather than routed through `check()` (which always logs
                # at error level): the name is unfixable from the caller's
                # side, and any name containing a space, one of the most
                # common cases, would otherwise log as an error on every
                # single reaction.
                rc = sref.setName(part.name)
                if rc != libsbml.LIBSBML_OPERATION_SUCCESS:
                    logger.warning(
                        "Name '%s' could not be set on species reference "
                        "for species '%s': rejected by libsbml with code "
                        "%s (a known SimpleSpeciesReference.setName defect "
                        "which applies SId syntax validation to the "
                        "string-typed 'name' attribute).",
                        part.name,
                        part.species,
                        rc,
                    )
            if part.notes is not None and part.notes.strip():
                set_notes(sref, part.notes, format=detect_format(part.notes))
            for annotation in Sbase._process_annotations(part.annotations or []):
                annotator.ModelAnnotator.annotate_sbase(
                    sbase=sref, annotation=annotation
                )
            for key_value_pair in part.keyValuePairs or []:
                key_value_pair.create_sbml(sref, model)

        # equation
        for reactant in self.equation.reactants:
            rref: libsbml.SpeciesReference = r.createReactant()
            set_speciesref_fields(sref=rref, part=reactant)

        for product in self.equation.products:
            pref: libsbml.SpeciesReference = r.createProduct()
            set_speciesref_fields(sref=pref, part=product)

        for modifier in self.equation.modifiers:
            mref: libsbml.ModifierSpeciesReference = r.createModifier()
            set_speciesref_fields(sref=mref, part=modifier)

        # kinetics
        if self.formula is not None:
            self.formula.create_sbml(r, model)

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

            # check all genes are in model; the association names them by id,
            # which is what `setAssociation(usingId=True)` below writes, so the
            # lookup is `getGeneProduct` and not `getGeneProductByLabel`. The
            # model is the one the reaction is created in, which is passed in:
            # `r.getModel()` returns the model of the document even for a
            # reaction inside a `<comp:modelDefinition>` (measured with
            # libsbml 5.21.2), whose gene products are its own.
            model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
            for gp in _gene_product_ids(self.geneProductAssociation):
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
        reversible = (
            self.reversible if self.reversible is not None else self.equation.reversible
        )
        check(sbase.setReversible(reversible), f"Set reversible on '{self.sid}'")

        # `fast` was removed from SBML in L3V2; `setFast` errors on such a
        # document, so it is only called when the level/version being
        # written still supports the attribute.
        supports_fast = sbase.getLevel() < 3 or (
            sbase.getLevel() == 3 and sbase.getVersion() < 2
        )
        if supports_fast:
            check(sbase.setFast(self.fast), f"Set fast on '{self.sid}'")


class EventAssignment(Value):
    """EventAssignment of an Event.

    Assigns the value of the expression to the variable when the event fires.
    """

    def __init__(
        self,
        variable: str,
        value: str | float | None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct an EventAssignment.

        Args:
            variable: the id of the element the assignment applies to
            value: the assigned expression, as an SBML L3 formula string;
                `None` for an event assignment without math, which SBML allows
                from L3V2 on
            sid: optional SId; `libsbml.EventAssignment` only gained a real,
                separate `id` attribute in SBML L3V2, and only from L3V2
                onward is it distinct from `variable` (see `_set_fields`
                docstring for the L3V1 behaviour)
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
        """
        super().__init__(
            sid=sid,
            value=value,
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

    def __repr__(self) -> str:
        """Get string representation."""
        return f"EventAssignment({self.variable} = {self.value})"

    def create_sbml(
        self, event: libsbml.Event, model: libsbml.Model
    ) -> libsbml.EventAssignment:
        """Create the libsbml.EventAssignment on the given event.

        Args:
            event: the libsbml.Event the assignment belongs to
            model: the libsbml.Model, used to resolve ids in the expression

        Returns:
            the created libsbml.EventAssignment
        """
        ea: libsbml.EventAssignment = event.createEventAssignment()
        self._set_fields(ea, model)
        self.create_port(model)
        check(ea.setVariable(self.variable), f"Set variable '{self.variable}'")
        if self.value is None:
            return ea
        ast_node = libsbml.parseL3FormulaWithModel(str(self.value), model)
        if ast_node is None:
            logger.error(
                "Event assignment math could not be parsed: '%s', %s",
                self.value,
                libsbml.getLastParseL3Error(),
            )
        else:
            check(ea.setMath(ast_node), f"Set math on '{self.variable}'")
        return ea

    #: `libsbml.Model.getElementBySId`, which comp resolves a `comp:idRef`
    #: with, does not answer with an event assignment, so a port names one by
    #: its metaid, see `Sbase._port_reference`
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "metaIdRef"

    def _set_fields(self, sbase: libsbml.EventAssignment, model: libsbml.Model) -> None:
        """Set fields on libsbml.EventAssignment.

        No override of the id handling is needed here: `SBML_EVENT_ASSIGNMENT`
        is already in `Sbase._ID_ATTRIBUTE_TYPECODES`, so `Sbase._set_fields`
        already routes `self.sid` through `setIdAttribute` rather than
        `setId`, and `setIdAttribute` never touches `variable`. Verified
        against live libsbml: on an L3V1 object `setIdAttribute` returns
        success but writes nothing (`EventAssignment` has no `id` attribute
        before L3V2, so it is silently dropped, exactly the "silently
        skipped on an older level/version" behaviour `KineticLaw` documents);
        on L3V2+ it writes a real, separately-serialized `id` distinct from
        `variable`. Nulling `self.sid` unconditionally, as an earlier draft
        of this method did, would have thrown away that L3V2 case for no
        benefit.

        Args:
            sbase: the libsbml.EventAssignment created by `create_sbml`
            model: the libsbml.Model the event assignment belongs to
        """
        super()._set_fields(sbase, model)


class Trigger(Sbase):
    """Trigger of an Event.

    Corresponds to a `libsbml.Trigger`: the condition whose change from false
    to true fires the event, and the two flags which qualify it.
    """

    def __init__(
        self,
        math: str | None,
        initialValue: bool = False,
        persistent: bool = True,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct a Trigger.

        Args:
            math: the condition, as an SBML L3 formula string, e.g.
                `"time >= 10"`; `None` for a trigger without math, which SBML
                allows from L3V2 on
            initialValue: the value of the trigger before the simulation
                starts; with `False` a condition which is true at the start
                fires the event at the start
            persistent: whether a fired event is executed even if the
                condition turns false again before its delay has passed
            sid: optional SId, a trigger only carries one since SBML L3V2;
                not written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name, a trigger only carries one since SBML
                L3V2; not written when the target document is older
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
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
        self.math = math
        self.initialValue = initialValue
        self.persistent = persistent

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Trigger({self.math})"

    def create_sbml(
        self, event: libsbml.Event, model: libsbml.Model
    ) -> libsbml.Trigger:
        """Create the libsbml.Trigger on the given event.

        Args:
            event: the libsbml.Event the trigger belongs to
            model: the libsbml.Model, used to resolve ids in the math

        Returns:
            the created libsbml.Trigger
        """
        trigger: libsbml.Trigger = event.createTrigger()
        self._set_fields(trigger, model)
        self.create_port(model)
        return trigger

    def _set_fields(self, sbase: libsbml.Trigger, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.Trigger.

        Args:
            sbase: the libsbml.Trigger created by `create_sbml`
            model: the libsbml.Model the trigger belongs to
        """
        super()._set_fields(sbase, model)
        if sbase.getLevel() < 3:
            # a trigger has these flags from SBML L3 on, below libsbml rejects
            # them as unexpected attributes, which the caller cannot change
            logger.debug(
                "'trigger' has no initialValue and persistent in SBML L%sV%s, "
                "they are not written.",
                sbase.getLevel(),
                sbase.getVersion(),
            )
        else:
            # initialValue False is not supported by Copasi, a condition on
            # time is the workaround
            check(
                sbase.setInitialValue(self.initialValue),
                f"Set initialValue on trigger '{self.math}'",
            )
            # persistent True is not supported by Copasi, careful with its usage
            check(
                sbase.setPersistent(self.persistent),
                f"Set persistent on trigger '{self.math}'",
            )
        _set_math(sbase, self.math, model)


class Priority(Sbase):
    """Priority of an Event.

    Corresponds to a `libsbml.Priority`: the math which orders the events
    that are executed at the same time, the event with the higher priority
    first.
    """

    def __init__(
        self,
        math: str | None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
    ):
        """Construct a Priority.

        Args:
            math: the priority, as an SBML L3 formula string; `None` for a
                priority without math, which SBML allows from L3V2 on
            sid: optional SId, a priority only carries one since SBML L3V2;
                not written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name, a priority only carries one since SBML
                L3V2; not written when the target document is older
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
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
        )
        self.math = math

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Priority({self.math})"

    def create_sbml(
        self, event: libsbml.Event, model: libsbml.Model
    ) -> libsbml.Priority | None:
        """Create the libsbml.Priority on the given event.

        Args:
            event: the libsbml.Event the priority belongs to
            model: the libsbml.Model, used to resolve ids in the math

        Returns:
            the created libsbml.Priority, `None` below SBML L3, which has no
            priority; that is logged as an error
        """
        priority: libsbml.Priority | None = event.createPriority()
        if priority is None:
            logger.error(
                "An event priority needs SBML L3, the priority '%s' of event "
                "'%s' is not written in SBML L%sV%s.",
                self.math,
                event.getId(),
                event.getLevel(),
                event.getVersion(),
            )
            return None
        self._set_fields(priority, model)
        self.create_port(model)
        return priority

    def _set_fields(self, sbase: libsbml.Priority, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.Priority.

        Args:
            sbase: the libsbml.Priority created by `create_sbml`
            model: the libsbml.Model the priority belongs to
        """
        super()._set_fields(sbase, model)
        _set_math(sbase, self.math, model)


class Delay(Sbase):
    """Delay of an Event.

    Corresponds to a `libsbml.Delay`: the math of the time between the firing
    of the event and the execution of its assignments.
    """

    def __init__(
        self,
        math: str | None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct a Delay.

        Args:
            math: the delay, as an SBML L3 formula string; `None` for a delay
                without math, which SBML allows from L3V2 on
            sid: optional SId, a delay only carries one since SBML L3V2; not
                written when the target document is older, see
                `Sbase._set_fields`
            name: optional SBML name, a delay only carries one since SBML
                L3V2; not written when the target document is older
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement
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
        self.math = math

    def __repr__(self) -> str:
        """Get string representation."""
        return f"Delay({self.math})"

    def create_sbml(self, event: libsbml.Event, model: libsbml.Model) -> libsbml.Delay:
        """Create the libsbml.Delay on the given event.

        Args:
            event: the libsbml.Event the delay belongs to
            model: the libsbml.Model, used to resolve ids in the math

        Returns:
            the created libsbml.Delay
        """
        delay: libsbml.Delay = event.createDelay()
        self._set_fields(delay, model)
        self.create_port(model)
        return delay

    def _set_fields(self, sbase: libsbml.Delay, model: libsbml.Model) -> None:
        """Set the fields on the libsbml.Delay.

        Args:
            sbase: the libsbml.Delay created by `create_sbml`
            model: the libsbml.Model the delay belongs to
        """
        super()._set_fields(sbase, model)
        _set_math(sbase, self.math, model)


class Event(Sbase):
    """Event.

    An event fires when its trigger, e.g. `time >= 10`, changes from false to
    true, and then executes its assignments, e.g. `{"S1": 5.0}`, after its
    optional delay. The priority orders events which are executed at the same
    time.

    The trigger, the priority and the delay are a `Trigger`, a `Priority` and
    a `Delay`, which carry their own metadata. Each of them is also accepted
    as a formula string or a number, which is normalized into the object;
    this is the documented authoring style, e.g.
    `Event("e1", trigger="time >= 10", priority="1", delay="2")`. `None`
    writes no element at all: an event without a priority or a delay, or,
    from SBML L3V2 on, without a trigger. An element without math, which SBML
    allows from L3V2 on, is an object whose `math` is `None`, e.g.
    `Trigger(None)`.

    `trigger`, `priority` and `delay` normalize what is assigned to them
    after construction in the same way. `trigger_persistent` and
    `trigger_initialValue` read and set the flags of the trigger.
    """

    def __init__(
        self,
        sid: str | None,
        trigger: Trigger | str | float | None,
        assignments: dict[str, str | float] | list[EventAssignment] | None = None,
        trigger_persistent: bool | None = None,
        trigger_initialValue: bool | None = None,
        useValuesFromTriggerTime: bool = True,
        priority: Priority | str | float | None = None,
        delay: Delay | str | float | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
        replacedBy: Any | None = None,
    ):
        """Construct an Event.

        Args:
            sid: optional SId
            trigger: the trigger, a `Trigger`, or its math as a formula string
                or a number; `None` for an event without a trigger, which SBML
                allows from L3V2 on
            assignments: the event assignments, a list of `EventAssignment`
                or a `{variable: expression}` dict
            trigger_persistent: the `persistent` of the `Trigger` created from
                math, `True` if not given. A `Trigger` keeps its own
                `persistent`, a different value given here is logged as a
                warning and not applied, as is one given without a trigger
            trigger_initialValue: the `initialValue` of the `Trigger` created
                from math, `False` if not given. A `Trigger` keeps its own
                `initialValue`, a different value given here is logged as a
                warning and not applied, as is one given without a trigger
            useValuesFromTriggerTime: whether the assignments are evaluated
                when the event fires rather than when it is executed
            priority: the priority, a `Priority`, or its math as a formula
                string or a number; `None` for an event without a priority
            delay: the delay, a `Delay`, or its math as a formula string or a
                number; `None` for an event without a delay
            name: optional SBML name
            sboTerm: optional SBO term
            metaId: optional SBML metaid
            annotations: optional RDF annotations
            notes: optional notes, as markdown, XHTML or a `Notes` object
            keyValuePairs: optional key-value pairs
            port: optional comp port
            uncertainties: optional distrib uncertainties
            replacedBy: optional comp replacement

        Raises:
            TypeError: if the trigger, the priority or the delay is neither
                the object, nor a formula string, nor a number
        """
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

        self._trigger: Trigger | None = None
        self._init_trigger(trigger, trigger_persistent, trigger_initialValue)
        self.assignments = Event._process_assignments(assignments)
        self.useValuesFromTriggerTime = useValuesFromTriggerTime

        self._priority: Priority | None = None
        self.priority = priority
        self._delay: Delay | None = None
        self.delay = delay

    @staticmethod
    def _math(value: object, element: str) -> str:
        """Convert the math of a trigger, a priority or a delay to a formula.

        Args:
            value: the math, a formula string, or a number, which is
                converted with `str()`
            element: `"trigger"`, `"priority"` or `"delay"`, for the error

        Returns:
            the math as a formula string

        Raises:
            TypeError: if the value is neither a formula string nor a number;
                a bool is rejected too, `str(True)` is the id `True` rather
                than the constant `true`
        """
        if isinstance(value, str):
            return value
        if isinstance(value, numbers.Real) and not isinstance(value, bool):
            return str(value)
        raise TypeError(
            f"The {element} of an event is a {element.title()}, a formula "
            f"string or a number, not '{value!r}'."
        )

    def _init_trigger(
        self,
        trigger: Trigger | str | float | None,
        persistent: bool | None,
        initialValue: bool | None,
    ) -> None:
        """Set the trigger and the trigger flags given to the constructor.

        The `trigger_persistent` and `trigger_initialValue` arguments
        configure the `Trigger` created from math, which is the documented
        authoring style. A `Trigger` carries its own flags, which win over
        these arguments, so an argument which differs from them is logged as
        a warning, as is one given for an event without a trigger.

        Args:
            trigger: the trigger, a `Trigger`, its math, or `None` for an
                event without a trigger
            persistent: the `trigger_persistent` argument, `None` if it was
                not given
            initialValue: the `trigger_initialValue` argument, `None` if it was
                not given
        """
        self.trigger = trigger
        if not isinstance(trigger, Trigger):
            # created from math with the default flags, or no trigger, for
            # which the setters log that a flag is not applied
            if persistent is not None:
                self.trigger_persistent = persistent
            if initialValue is not None:
                self.trigger_initialValue = initialValue
            return

        for flag, value, attribute in (
            ("trigger_persistent", persistent, "persistent"),
            ("trigger_initialValue", initialValue, "initialValue"),
        ):
            if value is not None and value != getattr(trigger, attribute):
                logger.warning(
                    "Event '%s': '%s=%s' is not applied, its Trigger has '%s=%s'.",
                    self.sid,
                    flag,
                    value,
                    attribute,
                    getattr(trigger, attribute),
                )

    @property
    def trigger(self) -> Trigger | None:
        """Get the trigger, `None` for an event without a trigger."""
        return self._trigger

    @trigger.setter
    def trigger(self, trigger: Trigger | str | float | None) -> None:
        """Set the trigger.

        Math is normalized into a `Trigger`, which keeps the `persistent` and
        `initialValue` of the trigger it replaces, or takes their defaults,
        `True` and `False`, if the event had no trigger. In 0.10 the flags
        were attributes of the event, which a new trigger string did not
        change.

        Args:
            trigger: the trigger, a `Trigger`, or its math as a formula string
                or a number; `None` for an event without a trigger

        Raises:
            TypeError: if the trigger is neither a `Trigger` nor math
        """
        if trigger is None or isinstance(trigger, Trigger):
            self._trigger = trigger
            return
        replaced = self._trigger
        self._trigger = Trigger(
            math=Event._math(trigger, "trigger"),
            persistent=True if replaced is None else replaced.persistent,
            initialValue=False if replaced is None else replaced.initialValue,
        )

    @property
    def trigger_persistent(self) -> bool | None:
        """Get the `persistent` of the trigger, `None` without a trigger."""
        return None if self._trigger is None else self._trigger.persistent

    @trigger_persistent.setter
    def trigger_persistent(self, persistent: bool) -> None:
        """Set the `persistent` of the trigger.

        Args:
            persistent: the flag; an event without a trigger has nothing to
                set it on, which is logged as a warning
        """
        self._set_trigger_flag("trigger_persistent", "persistent", persistent)

    @property
    def trigger_initialValue(self) -> bool | None:
        """Get the `initialValue` of the trigger, `None` without a trigger."""
        return None if self._trigger is None else self._trigger.initialValue

    @trigger_initialValue.setter
    def trigger_initialValue(self, initialValue: bool) -> None:
        """Set the `initialValue` of the trigger.

        Args:
            initialValue: the flag; an event without a trigger has nothing to
                set it on, which is logged as a warning
        """
        self._set_trigger_flag("trigger_initialValue", "initialValue", initialValue)

    def _set_trigger_flag(self, flag: str, attribute: str, value: bool) -> None:
        """Set a flag of the trigger, or log that the event has no trigger.

        Args:
            flag: the name of the flag on the event, for the warning
            attribute: the name of the flag on the `Trigger`
            value: the value of the flag
        """
        if self._trigger is None:
            logger.warning(
                "Event '%s' has no trigger, '%s=%s' is not applied.",
                self.sid,
                flag,
                value,
            )
            return
        setattr(self._trigger, attribute, value)

    @property
    def priority(self) -> Priority | None:
        """Get the priority, `None` for an event without a priority."""
        return self._priority

    @priority.setter
    def priority(self, priority: Priority | str | float | None) -> None:
        """Set the priority, math is normalized into a `Priority`.

        Args:
            priority: the priority, a `Priority`, or its math as a formula
                string or a number; `None` for an event without a priority

        Raises:
            TypeError: if the priority is neither a `Priority` nor math
        """
        if priority is None or isinstance(priority, Priority):
            self._priority = priority
        else:
            self._priority = Priority(math=Event._math(priority, "priority"))

    @property
    def delay(self) -> Delay | None:
        """Get the delay, `None` for an event without a delay."""
        return self._delay

    @delay.setter
    def delay(self, delay: Delay | str | float | None) -> None:
        """Set the delay, math is normalized into a `Delay`.

        Args:
            delay: the delay, a `Delay`, or its math as a formula string or a
                number; `None` for an event without a delay

        Raises:
            TypeError: if the delay is neither a `Delay` nor math
        """
        if delay is None or isinstance(delay, Delay):
            self._delay = delay
        else:
            self._delay = Delay(math=Event._math(delay, "delay"))

    @staticmethod
    def _process_assignments(
        assignments: dict[str, str | float] | list[EventAssignment] | None,
    ) -> list[EventAssignment]:
        """Normalize the event assignments to a list.

        A model definition writes the assignments as a `{variable:
        expression}` dict, which is the documented authoring style; the
        parser passes a list of `EventAssignment`, which carry their own
        metaId, sboTerm and annotations.

        Args:
            assignments: the assignments as a dict or a list

        Returns:
            the event assignments as `EventAssignment` objects
        """
        if assignments is None:
            return []
        if isinstance(assignments, dict):
            return [
                EventAssignment(variable=variable, value=value)
                for variable, value in assignments.items()
            ]
        return list(assignments)

    def create_sbml(self, model: libsbml.Model) -> libsbml.Event:
        """Create Event SBML in model."""
        event: libsbml.Event = model.createEvent()
        self._set_fields(event, model)
        self.create_port(model)

        return event

    def _set_fields(self, sbase: libsbml.Event, model: libsbml.Model) -> None:
        """Set fields in libsbml.Event."""
        super()._set_fields(sbase, model)

        check(
            sbase.setUseValuesFromTriggerTime(self.useValuesFromTriggerTime),
            f"Set useValuesFromTriggerTime on '{self.sid}'",
        )
        if self.trigger is not None:
            self.trigger.create_sbml(sbase, model)
        if self.priority is not None:
            self.priority.create_sbml(sbase, model)
        if self.delay is not None:
            self.delay.create_sbml(sbase, model)

        for assignment in self.assignments:
            assignment.create_sbml(sbase, model)

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
        math: str | None = None,
        message: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
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
        self.create_port(model)
        return constraint

    def _set_fields(self, sbase: libsbml.Constraint, model: libsbml.Model) -> None:
        """Set fields on libsbml.Constraint."""
        super()._set_fields(sbase, model)

        _set_math(sbase, self.math, model)
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


class _UncertChild(Sbase):
    """The part an `UncertParameter` and an `UncertSpan` have in common.

    Both are children of the `distrib:listOfUncertParameters` of an
    uncertainty or of an uncert parameter, and both state what is known about
    a value: an `UncertParameter` states one value, an `UncertSpan` a lower
    and an upper bound. Everything else is the same on both and lives here:
    the `type` which says what the value is, the `unit` of the value, the
    `definitionURL` which names the distribution or the external parameter
    the element stands for, the `math` which states a distribution, and the
    uncert parameters and spans of its own, which an external distribution
    states its parameters as.

    Both are SBML `SBase` objects: libsbml writes and reads back `id`,
    `name`, `metaId`, `sboTerm`, notes, annotations and fbc key value pairs
    on a `distrib:uncertParameter` and a `distrib:uncertSpan`, so all of them
    are offered.

    The three `Sbase` fields which are written from the `libsbml.Model` are
    not offered, and passing one is a `TypeError` rather than a value which is
    accepted and dropped:

    - `uncertainties`: libsbml does attach a distrib plugin to an uncert
      parameter, but it then writes the `listOfUncertainties` twice, which
      makes the document invalid (`distrib-20201`, only one list is allowed).
      `uncertParameters` is how an uncert parameter holds children.
    - `port` and `replacedBy`: a comp port which references an uncert
      parameter is written as a `Port` of the model with an `idRef` or a
      `metaIdRef`, which is how the parser reads it back; the shorthand on the
      element would have to be written with the model, which the children of
      an uncertainty are not written with, see `_set_fields`.
    """

    #: the `distrib:type` values SBML allows on the element of this class
    _types: ClassVar[frozenset[int]] = frozenset()

    def __init__(
        self,
        type: int | None,
        unit: UnitType = None,
        definitionURL: str | None = None,
        math: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Construct the fields an uncert parameter and an uncert span share.

        Args:
            type: the kind of the value, a `libsbml.DISTRIB_UNCERTTYPE_*`;
                `None` for an element which states no `distrib:type`, which
                SBML requires and libsbml reads and writes without
            unit: the unit of the value
            definitionURL: the URL which defines the distribution or the
                external parameter the element stands for, e.g. a term of
                ProbOnto or the csymbol of a distribution of distrib
            math: the math of the element as an SBML L3 formula, which an
                uncert parameter of the type `distribution` states its
                distribution as
            uncertParameters: the uncert parameters and spans of the element,
                in the order they are written in; the parameters of an
                external distribution
            sid: the id of the element, which is optional in SBML
            name: the name of the element
            sboTerm: the SBO term of the element
            metaId: the meta id of the element, which its annotations are
                referenced by
            annotations: the annotations of the element
            notes: the notes of the element
            keyValuePairs: the fbc key value pairs of the element
        """
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )
        self.type: int | None = type
        self.unit: UnitType = unit
        self.definitionURL: str | None = definitionURL
        self.math: str | None = math
        self.uncertParameters: list[UncertParameter | UncertSpan] = (
            list(uncertParameters) if uncertParameters else []
        )
        _check_unit_type(self.unit, "unit", self)
        self._check_states_a_value()

    def __str__(self) -> str:
        """Get string representation.

        `Sbase.__str__` lists the `Sbase` fields, which are all optional on a
        child of an uncertainty and empty on most of them. The messages which
        name the element are only useful with its type and its value, which is
        what `__repr__` prints, so both representations are the same here.
        """
        return repr(self)

    def _states_a_value(self) -> bool:
        """Test whether the element states anything about the value.

        Returns:
            whether the element has a value, a variable it reads the value
            from, a definitionURL, math, or uncert parameters of its own
        """
        return bool(
            self.definitionURL is not None
            or self.math is not None
            or self.uncertParameters
        )

    def _check_states_a_value(self) -> None:
        """Report an element which states nothing about the value.

        SBML requires neither a value nor anything else of an uncert
        parameter, and libsbml reads and validates an element which states
        nothing, so this is reported rather than refused: the parser has to be
        able to hold every document libsbml reads.

        This is a hint about a hand written element, so it is silent inside
        `Sbase.no_authoring_hints`, which is what `_distribution_parameter`
        builds its parameter in: the caller which knows why the element states
        nothing says it precisely instead.
        """
        if Sbase._authoring_hints.get() and not self._states_a_value():
            logger.error(
                "'%s' states nothing about the value: none of 'value', 'var', "
                "'definitionURL', 'math' and 'uncertParameters' is set.",
                self,
            )

    def _supports_type(self) -> bool:
        """Test whether SBML allows the type of the element on it.

        A span states an interval and a parameter a single value, so the types
        of the two are disjoint; a type of the other element, or no type of
        distrib at all, is reported and the element is not written, since
        libsbml would write an element SBML does not define.

        An element which states no type at all is written as it is: SBML
        requires a `distrib:type` and libsbml reads an element without one,
        which the round trip of such a document has to write back as it was.
        The missing attribute is reported by the validation of the written
        document, as it is for the document it was read from.

        Returns:
            whether the element is written
        """
        if self.type is None or self.type in self._types:
            return True
        logger.error(
            "Unsupported type for %s: '%s' in '%s'.",
            type(self).__name__,
            self.type,
            self,
        )
        return False

    def _set_fields(self, sbase: Any, model: Any) -> None:
        """Set the shared fields on the created libsbml object.

        `sbase` is declared `Any` for the reason `Sbase._set_fields` declares
        it `Any`: each subclass narrows it to the one libsbml type it creates,
        and a `libsbml.UncertParameter` here would make the `libsbml.UncertSpan`
        of `UncertSpan._set_fields` an LSP violation.

        Args:
            sbase: the libsbml.UncertParameter or libsbml.UncertSpan created
                by `create_sbml`
            model: the libsbml.Model the uncertainty is created in, which the
                math of the child is parsed against; `None` falls back to the
                model of the created object, which is attached to its parent
                already. It is handed down rather than looked up, since
                libsbml answers that lookup with the model of the *document*
                for an element inside a `<comp:modelDefinition>`, see
                `Model._fill_sbml`. It is never passed on to
                `Sbase._set_fields`, which is what keeps it from descending
                into the `uncertainties` and the comp fields of a child.
        """
        super()._set_fields(sbase, None)
        if self.type is not None:
            check(sbase.setType(self.type), f"Set type '{self.type}' on {sbase}")
        if self.definitionURL is not None:
            check(
                sbase.setDefinitionURL(self.definitionURL),
                f"Set definitionURL '{self.definitionURL}' on {sbase}",
            )
        _set_math(sbase, self.math, model if model is not None else sbase.getModel())
        if self.unit:
            uid = UnitDefinition.get_uid_for_unit(unit=self.unit)
            check(sbase.setUnits(uid), f"Set unit '{uid}' on {sbase}")

        child: UncertParameter | UncertSpan
        for child in self.uncertParameters:
            child.create_sbml(sbase, model)


class UncertParameter(_UncertChild):
    """A single value of an `Uncertainty`, e.g. a mean or a standard deviation.

    The value is either a number (`value`), a reference to a parameter of the
    model (`var`), or, for an uncert parameter of the type `distribution`, the
    distribution the value is drawn from, as `math` or as a `definitionURL`
    with the `uncertParameters` of the distribution. The `type` states which of
    them it is, e.g. `libsbml.DISTRIB_UNCERTTYPE_MEAN`.

    The fields it shares with an `UncertSpan`, and the fields neither of them
    offers, are documented in `_UncertChild`.
    """

    _types: ClassVar[frozenset[int]] = frozenset(
        {
            libsbml.DISTRIB_UNCERTTYPE_COEFFIENTOFVARIATION,
            libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
            libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER,
            libsbml.DISTRIB_UNCERTTYPE_KURTOSIS,
            libsbml.DISTRIB_UNCERTTYPE_MEAN,
            libsbml.DISTRIB_UNCERTTYPE_MEDIAN,
            libsbml.DISTRIB_UNCERTTYPE_MODE,
            libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE,
            libsbml.DISTRIB_UNCERTTYPE_SKEWNESS,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
            libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR,
            libsbml.DISTRIB_UNCERTTYPE_VARIANCE,
        }
    )

    def __init__(
        self,
        type: int | None,
        value: float | None = None,
        var: str | None = None,
        unit: UnitType = None,
        definitionURL: str | None = None,
        math: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Construct UncertParameter.

        Args:
            type: the kind of the value, a `libsbml.DISTRIB_UNCERTTYPE_*`,
                `None` for an element without one, see `_UncertChild`
            value: the numerical value
            var: the id of the element which holds the value, an alternative
                to `value`
            unit: the unit of the value
            definitionURL: see `_UncertChild`
            math: see `_UncertChild`
            uncertParameters: see `_UncertChild`
            sid: the id of the uncert parameter, which is optional in SBML
            name: the name of the uncert parameter
            sboTerm: the SBO term of the uncert parameter
            metaId: the meta id of the uncert parameter, which its annotations
                are referenced by
            annotations: the annotations of the uncert parameter
            notes: the notes of the uncert parameter
            keyValuePairs: the fbc key value pairs of the uncert parameter
        """
        # before `super().__init__`, which checks and reports what the
        # element states, through the `_states_a_value` of this class
        self.value: float | None = value
        self.var: str | None = var
        super().__init__(
            type=type,
            unit=unit,
            definitionURL=definitionURL,
            math=math,
            uncertParameters=uncertParameters,
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )

    def __repr__(self) -> str:
        """Get string representation."""
        value = self.value if self.value is not None else self.var
        return f"UncertParameter({self.type}, {value} [{self.unit}])"

    def _states_a_value(self) -> bool:
        """Test whether the uncert parameter states anything about the value."""
        return (
            self.value is not None or self.var is not None or super()._states_a_value()
        )

    def create_sbml(
        self,
        parent: libsbml.Uncertainty | libsbml.UncertParameter,
        model: libsbml.Model | None = None,
    ) -> libsbml.UncertParameter | None:
        """Create the libsbml.UncertParameter in the given parent.

        Args:
            parent: the libsbml.Uncertainty or libsbml.UncertParameter the
                parameter is created in
            model: the libsbml.Model the uncertainty is created in, which the
                math is parsed against, see `_UncertChild._set_fields`

        Returns:
            the created libsbml.UncertParameter, `None` for a parameter whose
            type SBML does not allow on one, see `_supports_type`
        """
        if not self._supports_type():
            return None
        up: libsbml.UncertParameter = parent.createUncertParameter()
        self._set_fields(up, model)
        return up

    def _set_fields(self, sbase: libsbml.UncertParameter, model: Any) -> None:
        """Set the fields on the libsbml.UncertParameter.

        Args:
            sbase: the libsbml.UncertParameter created by `create_sbml`
            model: the model the math is parsed against, see
                `_UncertChild._set_fields`
        """
        super()._set_fields(sbase, model)
        if self.value is not None:
            check(sbase.setValue(self.value), f"Set value '{self.value}' on {sbase}")
        if self.var is not None:
            check(sbase.setVar(self.var), f"Set var '{self.var}' on {sbase}")


class UncertSpan(_UncertChild):
    """An interval of an `Uncertainty`, e.g. a range or a confidence interval.

    Both bounds are either a number (`valueLower`, `valueUpper`) or a
    reference to a parameter of the model (`varLower`, `varUpper`), and the
    `type` states what the interval is, e.g.
    `libsbml.DISTRIB_UNCERTTYPE_RANGE`.

    An uncert span carries the same fields as an `UncertParameter`, which it
    is a subclass of in libsbml: it is written with `createUncertSpan` and
    read back from the `listOfUncertParameters`. The shared fields, and the
    fields neither class offers, are documented in `_UncertChild`.
    """

    _types: ClassVar[frozenset[int]] = frozenset(
        {
            libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_CREDIBLEINTERVAL,
            libsbml.DISTRIB_UNCERTTYPE_INTERQUARTILERANGE,
            libsbml.DISTRIB_UNCERTTYPE_RANGE,
        }
    )

    def __init__(
        self,
        type: int | None,
        valueLower: float | None = None,
        varLower: str | None = None,
        valueUpper: float | None = None,
        varUpper: str | None = None,
        unit: UnitType = None,
        definitionURL: str | None = None,
        math: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Construct UncertSpan.

        Args:
            type: the kind of the interval, a `libsbml.DISTRIB_UNCERTTYPE_*`,
                `None` for an element without one, see `_UncertChild`
            valueLower: the numerical value of the lower bound
            varLower: the id of the element which holds the lower bound, an
                alternative to `valueLower`
            valueUpper: the numerical value of the upper bound
            varUpper: the id of the element which holds the upper bound, an
                alternative to `valueUpper`
            unit: the unit of the bounds
            definitionURL: see `_UncertChild`
            math: see `_UncertChild`
            uncertParameters: see `_UncertChild`
            sid: the id of the uncert span, which is optional in SBML
            name: the name of the uncert span
            sboTerm: the SBO term of the uncert span
            metaId: the meta id of the uncert span, which its annotations are
                referenced by
            annotations: the annotations of the uncert span
            notes: the notes of the uncert span
            keyValuePairs: the fbc key value pairs of the uncert span
        """
        # before `super().__init__`, which checks and reports the bounds
        # through the `_check_states_a_value` of this class
        self.valueLower: float | None = valueLower
        self.varLower: str | None = varLower
        self.valueUpper: float | None = valueUpper
        self.varUpper: str | None = varUpper
        super().__init__(
            type=type,
            unit=unit,
            definitionURL=definitionURL,
            math=math,
            uncertParameters=uncertParameters,
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )

    def __repr__(self) -> str:
        """Get string representation."""
        lower = self.valueLower if self.valueLower is not None else self.varLower
        upper = self.valueUpper if self.valueUpper is not None else self.varUpper
        return f"UncertSpan({self.type}, {lower} - {upper} [{self.unit}])"

    def _states_a_value(self) -> bool:
        """Test whether the uncert span states anything about its bounds."""
        return (
            self.valueLower is not None
            or self.varLower is not None
            or self.valueUpper is not None
            or self.varUpper is not None
            or super()._states_a_value()
        )

    def _check_states_a_value(self) -> None:
        """Report every bound of the span which is not stated.

        A span states an interval, so each of its two bounds needs either a
        value or the variable it is read from. The check of `_UncertChild`
        only sees whether the element states anything at all, which a span
        with one bound does; both are named here instead, which is what the
        constructor refused before an element of every document libsbml reads
        had to be expressible.

        A span which states its interval as math, as the definitionURL of an
        external distribution or as uncert parameters of its own needs neither
        bound, and nothing is reported for it.
        """
        if not Sbase._authoring_hints.get() or super()._states_a_value():
            return
        for bound, value, var in (
            ("lower", self.valueLower, self.varLower),
            ("upper", self.valueUpper, self.varUpper),
        ):
            if value is None and var is None:
                logger.error(
                    "The %s bound of '%s' is not stated: neither 'value%s' nor "
                    "'var%s' is set.",
                    bound,
                    self,
                    bound.capitalize(),
                    bound.capitalize(),
                )

    def create_sbml(
        self,
        parent: libsbml.Uncertainty | libsbml.UncertParameter,
        model: libsbml.Model | None = None,
    ) -> libsbml.UncertSpan | None:
        """Create the libsbml.UncertSpan in the given parent.

        Args:
            parent: the libsbml.Uncertainty or libsbml.UncertParameter the
                span is created in
            model: the libsbml.Model the uncertainty is created in, which the
                math is parsed against, see `_UncertChild._set_fields`

        Returns:
            the created libsbml.UncertSpan, `None` for a span whose type SBML
            does not allow on one, see `_supports_type`
        """
        if not self._supports_type():
            return None
        span: libsbml.UncertSpan = parent.createUncertSpan()
        self._set_fields(span, model)
        return span

    def _set_fields(self, sbase: libsbml.UncertSpan, model: Any) -> None:
        """Set the fields on the libsbml.UncertSpan.

        Args:
            sbase: the libsbml.UncertSpan created by `create_sbml`
            model: the model the math is parsed against, see
                `_UncertChild._set_fields`
        """
        super()._set_fields(sbase, model)
        if self.valueLower is not None:
            check(
                sbase.setValueLower(self.valueLower),
                f"Set valueLower '{self.valueLower}' on {sbase}",
            )
        if self.valueUpper is not None:
            check(
                sbase.setValueUpper(self.valueUpper),
                f"Set valueUpper '{self.valueUpper}' on {sbase}",
            )
        if self.varLower is not None:
            check(
                sbase.setVarLower(self.varLower),
                f"Set varLower '{self.varLower}' on {sbase}",
            )
        if self.varUpper is not None:
            check(
                sbase.setVarUpper(self.varUpper),
                f"Set varUpper '{self.varUpper}' on {sbase}",
            )


#: the start of the `definitionURL` of every distribution of distrib
_DISTRIBUTION_URL: str = "http://www.sbml.org/sbml/symbols/distrib/"

#: the distributions of distrib, which `Uncertainty.formula` names one of
_DISTRIBUTIONS: tuple[str, ...] = (
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
    "rayleigh",
)


def _distribution_parameter(formula: str) -> UncertParameter:
    """Build the uncert parameter the `formula` of an uncertainty is written as.

    Which distribution the formula draws from is decided on the parsed
    formula, the name of the function it calls at the top level: libsbml
    parses every distribution of distrib into an AST node of its own, whose
    name is the name of the distribution. The name cannot be searched for in
    the text of the formula, which is what this did: `lognormal(0, 1)`
    contains `normal`, and so does an identifier like `normalization`.

    A formula which is not a call of a distribution is written as the uncert
    parameter of the type `distribution` it has always been written as,
    without a `definitionURL` and without math, and is reported: the shortcut
    has no way to express it, and the generic check of `_UncertChild` would
    only say that the parameter states nothing, which this says precisely.
    The math itself is parsed again when it is written, by `_set_math` with
    the model of the document, which resolves the ids of the formula.

    Args:
        formula: the distribution of the value as an SBML L3 formula, e.g.
            `normal(2.0, 2.0)`

    Returns:
        an uncert parameter of the type `distribution`: with the
        `definitionURL` of the distribution the formula calls and the formula
        as its math, or, for a formula which calls none, with neither
    """
    distribution: str | None = None
    ast: libsbml.ASTNode | None = libsbml.parseL3Formula(formula)
    if ast is None:
        reason: str = libsbml.getLastParseL3Error().strip() or "empty formula"
        logger.error(
            "The formula '%s' of an uncertainty could not be parsed: %s",
            formula,
            reason,
        )
    elif ast.isFunction() and ast.getName() in _DISTRIBUTIONS:
        distribution = str(ast.getName())

    if distribution is None:
        if ast is not None:
            logger.error(
                "The formula '%s' of an uncertainty is not a call of a "
                "distribution of distrib (%s), so the uncert parameter of the "
                "uncertainty is written without a definitionURL and without "
                "math.",
                formula,
                ", ".join(_DISTRIBUTIONS),
            )
        # the parameter states nothing about the value, which the message
        # above says more precisely than `_UncertChild._check_states_a_value`
        with Sbase.no_authoring_hints():
            return UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION)

    return UncertParameter(
        type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
        definitionURL=f"{_DISTRIBUTION_URL}{distribution}",
        math=formula,
    )


class Uncertainty(Sbase):
    """The uncertainty of the value of an element, a `distrib:uncertainty`.

    An uncertainty states what is known about a value beyond the value
    itself: a mean with a standard deviation, a range, a confidence interval,
    or the distribution the value is drawn from. Every `Sbase` can carry a
    list of them.

    SBML holds the values of an uncertainty in one list, the
    `distrib:listOfUncertParameters`, whose elements are
    `distrib:uncertParameter` and `distrib:uncertSpan`, and
    `uncertParameters` is that list: it takes `UncertParameter` and
    `UncertSpan` objects and is written in its own order, which is how the
    order of a parsed document is preserved.

    `uncertSpans` is the authoring style of two lists, one per kind, and is
    kept. It has no place for an order between the two, so its spans are put
    in front of `uncertParameters`, which is the order such an uncertainty has
    always been written in.

    `formula` is the shortcut for a distribution: it is normalized into one
    `UncertParameter` of the type `distribution` when the uncertainty is
    constructed, see `_distribution_parameter`, and appended after the
    children given explicitly. An uncertainty is written from
    `uncertParameters` and from nothing else, so a parsed uncertainty, which
    carries the distribution as an ordinary child, is written exactly once.
    """

    def __init__(
        self,
        sid: str | None = None,
        formula: str | None = None,
        uncertParameters: list[UncertParameter | UncertSpan] | None = None,
        uncertSpans: list[UncertSpan] | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
    ):
        """Construct Uncertainty.

        Args:
            sid: the id of the uncertainty, which is optional in SBML
            formula: the distribution of the value as an SBML L3 formula,
                e.g. `normal(2.0, 2.0)`; the shortcut for the uncert parameter
                of the type `distribution` it is normalized into
            uncertParameters: the uncert parameters and spans of the
                uncertainty, in the order they are written in
            uncertSpans: the spans of the uncertainty, which are written
                before `uncertParameters`
            name: the name of the uncertainty
            sboTerm: the SBO term of the uncertainty
            metaId: the meta id of the uncertainty, which its annotations are
                referenced by
            annotations: the annotations of the uncertainty
            notes: the notes of the uncertainty
            keyValuePairs: the fbc key value pairs of the uncertainty
            port: the comp port of the uncertainty
        """
        super().__init__(
            sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            port=port,
        )

        # Object on which the uncertainty is written
        self.formula = formula
        self.uncertParameters: list[UncertParameter | UncertSpan] = [
            *(uncertSpans if uncertSpans else []),
            *(uncertParameters if uncertParameters else []),
        ]
        if formula:
            self.uncertParameters.append(_distribution_parameter(formula))

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.Uncertainty:
        """Create the libsbml.Uncertainty on the given element.

        Args:
            sbase: the libsbml object the uncertainty is created on
            model: the libsbml.Model the element belongs to

        Returns:
            the created libsbml.Uncertainty
        """
        sbase_distrib: libsbml.DistribSBasePlugin = sbase.getPlugin("distrib")
        uncertainty: libsbml.Uncertainty = sbase_distrib.createUncertainty()

        self._set_fields(uncertainty, model)
        self.create_port(model)

        child: UncertParameter | UncertSpan
        for child in self.uncertParameters:
            child.create_sbml(uncertainty, model)

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
        notes: str | Notes | None = None,
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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
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
        )
        self.associatedSpecies = associatedSpecies
        self.label = label

    def create_sbml(self, model: libsbml.Model) -> libsbml.GeneProduct:
        """Create GeneProduct."""
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        gene_product: libsbml.GeneProduct = model_fbc.createGeneProduct()
        self._set_fields(gene_product, model=model)

        self.create_port(model)

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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
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
        )
        self.variable = variable
        self.coefficient = coefficient
        # `None` is "the component has no variableType", which fbc writes as
        # an absent attribute; the tested value is `is not None`, since
        # `libsbml.FBC_VARIABLE_TYPE_LINEAR` is `0` and falsy
        self.variableType = (
            FluxObjective.normalize_variable_type(variableType)
            if variableType is not None
            else None
        )

    def create_sbml(
        self,
        constraint: libsbml.UserDefinedConstraint,
        model: libsbml.Model | None = None,
    ) -> libsbml.UserDefinedConstraintComponent:
        """Create the libsbml.UserDefinedConstraintComponent in the constraint.

        Args:
            constraint: the libsbml.UserDefinedConstraint the component
                belongs to
            model: the libsbml.Model the constraint is created in, which the
                fields of the component are written with. It has to be handed
                down, since libsbml answers `constraint.getModel()` with the
                model of the *document* for a constraint inside a
                `<comp:modelDefinition>`, see `Model._fill_sbml`. `None` falls
                back to that lookup, for a caller which creates a component in
                a constraint of the model of a document

        Returns:
            the created libsbml.UserDefinedConstraintComponent
        """
        component: libsbml.UserDefinedConstraintComponent = (
            constraint.createUserDefinedConstraintComponent()
        )
        if model is None:
            model = constraint.getModel()
        self._set_fields(component, model)
        self.create_port(model)

        check(component.setVariable(self.variable), f"set variable `{self.variable}`")
        check(
            component.setCoefficient(self.coefficient),
            f"set coefficient `{self.coefficient}`",
        )
        if self.variableType is not None:
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
        variableType: str | None = libsbml.FBC_VARIABLE_TYPE_LINEAR,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
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
                    # infer variableType from the constraint; a component
                    # which states one keeps it, `libsbml.
                    # FBC_VARIABLE_TYPE_LINEAR` included, which is `0`
                    if component.variableType is None:
                        component.variableType = variableType
                    self.components.append(component)

    def create_sbml(self, model: libsbml.Model) -> libsbml.UserDefinedConstraint:
        """Create UserDefinedConstraint."""
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        udc: libsbml.UserDefinedConstraint = model_fbc.createUserDefinedConstraint()
        self._set_fields(udc, model)
        self.create_port(model)
        udc.setUpperBound(self.upperBound)
        udc.setLowerBound(self.lowerBound)
        for component in self.components:
            component.create_sbml(constraint=udc, model=model)

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
        variableType: str | None = None,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
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
        )
        self.reaction = reaction
        self.coefficient = coefficient
        # `None` is "the flux objective has no variableType", which fbc writes
        # as an absent attribute; the tested value is `is not None`, since
        # `libsbml.FBC_VARIABLE_TYPE_LINEAR` is `0` and falsy
        self.variableType = (
            FluxObjective.normalize_variable_type(variableType)
            if variableType is not None
            else None
        )

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

    def create_sbml(
        self, objective: libsbml.Objective, model: libsbml.Model | None = None
    ) -> libsbml.FluxObjective:
        """Create the libsbml.FluxObjective in the objective.

        Args:
            objective: the libsbml.Objective the flux objective belongs to
            model: the libsbml.Model the objective is created in, which the
                fields of the flux objective are written with. It has to be
                handed down, since libsbml answers `objective.getModel()` with
                the model of the *document* for an objective inside a
                `<comp:modelDefinition>`, see `Model._fill_sbml`. `None` falls
                back to that lookup, for a caller which creates a flux
                objective in an objective of the model of a document

        Returns:
            the created libsbml.FluxObjective
        """
        flux_objective: libsbml.FluxObjective = objective.createFluxObjective()
        if model is None:
            model = objective.getModel()
        self._set_fields(flux_objective, model)
        self.create_port(model)

        flux_objective.setReaction(self.reaction)
        flux_objective.setCoefficient(self.coefficient)
        if self.variableType is not None:
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
        variableType: str | None = libsbml.FBC_VARIABLE_TYPE_LINEAR,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        port: Any = None,
        uncertainties: list[Uncertainty] | None = None,
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
                    # infer variableType from objective; a flux objective
                    # which states one keeps it, `libsbml.
                    # FBC_VARIABLE_TYPE_LINEAR` included, which is `0`
                    if flux_objective.variableType is None:
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
        """Create Objective.

        An objective whose `active` is set becomes the `activeObjective` of
        the model. The objectives of a model are written in the order they
        are defined in, so of several active ones the last one written wins,
        and a model whose objectives are all inactive gets no active
        objective at all.

        Args:
            model: the libsbml.Model the objective is created in

        Returns:
            the created libsbml.Objective
        """
        model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
        objective: libsbml.Objective = model_fbc.createObjective()
        self._set_fields(objective, model)
        self.create_port(model)
        objective.setType(self.objectiveType)
        if self.active:
            model_fbc.setActiveObjectiveId(self.sid)
        for flux_objective in self.fluxObjectives:
            flux_objective.create_sbml(objective=objective, model=model)

        return objective


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
        notes: str | Notes | None = None,
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
        notes: str | Notes | None = None,
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

        if self.modelRef is None:
            # comp:modelRef is a required attribute; libsbml raises a
            # SWIG TypeError for `setModelRef(None)` rather than reporting
            # an invalid value, so the guard has to sit in front of the
            # call. The document is written anyway (`create_model` reports,
            # it never blocks) and is caught by validation instead, which
            # reports id 1020607 ("Allowed <submodel> attributes") naming
            # 'comp:modelRef' as a missing required attribute, once for
            # every consistency check `ValidationOptions` runs.
            logger.error(
                "Submodel '%s' has no modelRef, which is a required "
                "attribute; the written document will not validate.",
                self.sid,
            )
        else:
            submodel.setModelRef(self.modelRef)
        if self.timeConversionFactor:
            submodel.setTimeConversionFactor(self.timeConversionFactor)
        if self.extentConversionFactor:
            submodel.setExtentConversionFactor(self.extentConversionFactor)

        return submodel

    def _set_fields(self, sbase: libsbml.Submodel, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)


class SbaseRef(Sbase):
    """SBaseRef.

    The base of `Port`, `ReplacedElement`, `ReplacedBy` and `Deletion`: each
    references an element by one of `portRef`, `idRef`, `unitRef`,
    `metaIdRef`. The SBML spec allows a `<comp:sBaseRef>` to hold a nested
    `<comp:sBaseRef>` child of its own, which continues the reference into a
    submodel of the referenced submodel, to arbitrary depth; `sBaseRef`
    holds that nested reference, an `SbaseRef` in its own right so the chain
    can continue.

    `sid` is set on every level (`Sbase._set_fields` sets it through the
    generic `id` SBase core added in SBML L3V2), but libsbml's comp writer
    does not serialize that generic `id`/`name` on a `ReplacedElement`, a
    `ReplacedBy` or a nested `<comp:sBaseRef>`: measured with libsbml 5.21.2,
    `isSetIdAttribute()` is `True` right after `_set_fields`, and `False` once
    the document is written and read back. `metaId`, `sboTerm`, notes and
    annotations are unaffected (they predate L3V2 and are written normally),
    and so are the `sid` and `name` of a `Port` and of a `Deletion`, since
    comp gives both elements an `id` and a `name` of their own, written as the
    package attributes `comp:id` and `comp:name`.

    A `Port`, a `ReplacedElement` or a `ReplacedBy` is a convenient, already
    available `SbaseRef` which a caller may reuse for a nested level, and
    whichever class builds it, a nested level is written as a plain
    `<comp:sBaseRef>`, see `_set_fields`. So a `Port` reused as one drops its
    `portType`, its `sid` and its `name`, and a `ReplacedElement` or a
    `ReplacedBy` reused as one drops its `submodelRef`, and a
    `ReplacedElement` also its `deletion` and its `conversionFactor`: none of
    those attributes exists on a `<comp:sBaseRef>`. `sbmlutils.parser` builds
    every nested level as a plain `SbaseRef`.
    """

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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
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
        _check_unit_type(self.unitRef, "unitRef", self)
        self.metaIdRef = metaIdRef
        self.sBaseRef = sBaseRef

    def _set_fields(self, sbase: Any, model: Any) -> None:
        """Set the fields of the created libsbml `SBaseRef` (or subclass).

        Args:
            sbase: the libsbml object created by `create_sbml`, one of
                `libsbml.Port`, `libsbml.ReplacedElement`,
                `libsbml.ReplacedBy`, `libsbml.Deletion` or, for a nested
                reference, `libsbml.SBaseRef` itself
            model: the `libsbml.Model` the object belongs to; `None` for a
                nested reference, which lives inside another `SbaseRef`
                rather than in a list of the model, following the pattern
                `LocalParameter`/`UncertParameter`/`UncertSpan` use for an
                element nested inside another
        """
        super()._set_fields(sbase, model)

        if self.portRef is not None:
            sbase.setPortRef(self.portRef)
        if self.idRef is not None:
            sbase.setIdRef(self.idRef)
        if self.unitRef is not None:
            unit_str = UnitDefinition.get_uid_for_unit(unit=self.unitRef)
            sbase.setUnitRef(unit_str)
        if self.metaIdRef is not None:
            sbase.setMetaIdRef(self.metaIdRef)
        if self.sBaseRef is not None:
            nested: libsbml.SBaseRef = sbase.createSBaseRef()
            # written through the base class explicitly rather than through
            # `self.sBaseRef._set_fields`: a nested reference is always a
            # plain `<comp:sBaseRef>` in the SBML written, never a
            # `<comp:port>`, `<comp:replacedElement>` or
            # `<comp:replacedBy>`, whatever python class built it (a `Port`
            # is a convenient, already available `SbaseRef` a caller may
            # reuse for a nested level; its `portType` is a construction
            # convenience of `Port.create_sbml`, not a field of
            # `_set_fields`, so it is silently not applied to the nested
            # level, and a `ReplacedElement`/`ReplacedBy` passed here would
            # otherwise raise `AttributeError` on `setSubmodelRef`, which
            # `libsbml.SBaseRef` does not implement). `model` is passed as
            # `None`, the pattern `LocalParameter.create_sbml` and
            # `KineticLaw.create_sbml` use for an element nested inside
            # another: none of the four subclasses exposes `port`,
            # `uncertainties` or `replacedBy` through its constructor, so
            # this is currently only a safety net, not an observed
            # difference.
            SbaseRef._set_fields(self.sBaseRef, nested, None)


class ReplacedElement(SbaseRef):
    """ReplacedElement.

    comp writes a `<comp:replacedElement>` inside the element it replaces,
    and `Model.replaced_elements` holds it next to that element instead, with
    `elementRef` naming it. `elementRef` is therefore a pointer inside
    sbmlutils, it is not written into the document: `create_sbml` resolves it
    against the model the replacement is written in, as the id of an element,
    of a unit definition, which lives in a namespace of its own and which
    `getElementBySId` does not answer with, or, for an element which has no
    id at all, as its metaid. An SBML rule, an initial assignment, an event
    assignment and a kinetic law have an id only from SBML L3V2 on, and the
    SBML test suite replaces a rate rule which carries a metaid and no id.

    **The resolution order is the id of an element, then the id of a unit
    definition, then a metaid**, and it is not disambiguated: an element id
    and a unit definition id live in different namespaces, and a metaid in a
    third, so one string can name three different elements of one model, and
    the first of the three wins. A caller which names an element by its metaid
    is responsible for that metaid being the id of nothing else in the same
    model; `sbmlutils.parser` uses a metaid only for an element which has no
    id and reports the replacement as a loss instead of writing it when the
    metaid is the id of an element or of a unit definition of the same model,
    see `_replaced_element_ref`.
    """

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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
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
            sBaseRef=sBaseRef,
        )
        self.elementRef = elementRef
        self.submodelRef = submodelRef
        self.deletion = deletion
        self.conversionFactor = conversionFactor

    def create_sbml(self, model: libsbml.Model) -> libsbml.ReplacedElement:
        """Create the libsbml.ReplacedElement inside the element it replaces.

        Args:
            model: the libsbml.Model, or libsbml.ModelDefinition, the
                replacement is written in, which `elementRef` is resolved
                against

        Returns:
            the created libsbml.ReplacedElement

        Raises:
            ValueError: if `elementRef` names no element of the model
        """
        # resolve the element the replacement is written into, see the class
        # docstring on the three things `elementRef` can name
        e = model.getElementBySId(self.elementRef)
        if not e:
            # a unit definition lives in a namespace of its own, which
            # `getElementBySId` does not search (this shadows an element of
            # the same id, which SBML allows)
            e = model.getUnitDefinition(self.elementRef)
        if not e:
            # an element which has no id at all is named by its metaid
            e = model.getElementByMetaId(self.elementRef)
        if not e:
            raise ValueError(
                f"No SBML element, UnitDefinition or metaid found for "
                f"elementRef: '{self.elementRef}' in '{self}'"
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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
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
            sBaseRef=sBaseRef,
        )
        self.elementRef = elementRef
        self.submodelRef = submodelRef

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.ReplacedBy:
        """Create SBML ReplacedBy."""
        sbase_comp: libsbml.CompSBasePlugin = _comp_plugin(
            sbase, f"The replacedBy of {sbase.getElementName()} '{sbase.getId()}'"
        )
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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
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
            sBaseRef=sBaseRef,
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

    `portType` is an authoring convenience: a port which states no `sboTerm`
    is given the SBO term of its port type, `SBO:0000599` for the plain
    `PortType.PORT` of the default. `portType=None` asks for neither, which is
    what a port read from a document states: SBML has no port type, the
    document either carries an sboTerm or it does not, and inventing one would
    make a round trip of a port without an sboTerm write one.
    """

    #: the SBO term which stands for each port type
    _SBO_FOR_PORT_TYPE: ClassVar[dict[PortType, SBO]] = {
        PortType.PORT: SBO.PORT,
        PortType.INPUT_PORT: SBO.INPUT_PORT,
        PortType.OUTPUT_PORT: SBO.OUTPUT_PORT,
    }

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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
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
            sBaseRef=sBaseRef,
        )
        self.portType = portType

    def create_sbml(self, model: libsbml.Model) -> libsbml.Port:
        """Create the libsbml.Port in the given model.

        Args:
            model: the libsbml.Model, or libsbml.ModelDefinition, the port is
                created in

        Returns:
            the created libsbml.Port

        Raises:
            ValueError: if the document does not declare the comp package
        """
        cmodel: libsbml.CompModelPlugin = _comp_plugin(model, f"Port '{self.sid}'")
        p = cmodel.createPort()
        self._set_fields(p, model)

        if self.sboTerm is None and self.portType is not None:
            sbo: SBO = Port._SBO_FOR_PORT_TYPE[self.portType]
            p.setSBOTerm(sbo.value.replace("_", ":"))

        return p

    def _set_fields(self, sbase: libsbml.Port, model: libsbml.Model) -> None:
        """Set fields on Port."""
        super()._set_fields(sbase, model)


class Package(StrEnum):
    """Supported/tested packages.

    The definition order is the order the packages are declared on the
    `<sbml>` element in, see `packages_in_canonical_order`.
    """

    COMP = "comp"
    COMP_V1 = "comp-v1"
    DISTRIB = "distrib"
    DISTRIB_V1 = "distrib-v1"
    FBC = "fbc"
    FBC_V2 = "fbc-v2"
    FBC_V3 = "fbc-v3"


def packages_in_canonical_order(packages: Iterable[Package]) -> list[Package]:
    """Order the packages of a model canonically, without repetition.

    The packages of a model were collected in a `set`, which the namespace
    declarations and the `required` attributes of the `<sbml>` element were
    written from in iteration order: the order of a set of `Package` members
    depends on the hash seed, so the same model definition wrote a different
    `<sbml>` element in every process. The declaration order of a namespace
    carries no meaning in XML, but a file which changes between two runs
    cannot be compared byte by byte at all. The definition order of `Package`
    is the order used instead, which is the alphabetical one, `comp`,
    `distrib`, `fbc`.

    Args:
        packages: the packages of a model, in any order and with repetition

    Returns:
        the packages in the definition order of `Package`, each one once
    """
    given = set(packages)
    return [package for package in Package if package in given]


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
    conversionFactor: str | None
    objects: list[Sbase] | None

    units: type[Units] | list[UnitDefinition] | None
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
    strict: bool | None
    user_defined_constraints: list[UserDefinedConstraint] | None
    objectives: list[Objective] | None
    gene_products: list[GeneProduct] | None
    # layout
    layouts: list | None


class Model(Sbase, FrozenClass):
    """Model.

    The field annotations below document the model structure. `Model` used to
    declare `pydantic.BaseModel` as a base, but `Model.__init__` never reached
    `BaseModel.__init__` and `FrozenClass.__setattr__` shadowed pydantic's, so
    no validation ever ran and `deepcopy`, `==` and `model_dump` raised.
    `FrozenClass` rejects unknown attributes, which is what the freeze was for.
    """

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
    conversionFactor: str | None
    units: list[UnitDefinition]
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
    #: `fbc:strict` of the model, `None` keeps today's default of writing it
    #: `False` when the model declares fbc, and unset otherwise (see
    #: `Document._create_sbml`). It is a scalar in `_keys` (not `list`-typed), so
    #: `merge_models` overwrites it with the value of the last model that
    #: sets it, like `conversionFactor` and every other scalar field.
    strict: bool | None
    user_defined_constraints: list[UserDefinedConstraint]
    objectives: list[Objective]
    gene_products: list[GeneProduct]
    # layout
    layouts: list | None
    parsed: bool

    #: field name -> merge kind read by `merge_models` to decide whether a
    #: field of two models is concatenated (`list`) or overwritten (`None`).
    #: Derived from the annotations above by `_derive_model_keys`, called once
    #: right after this class is defined, once every field annotation this
    #: class references is itself defined; see the comment there.
    _keys: ClassVar[dict[str, Any]] = {}

    _supported_packages: ClassVar[set[str]] = {
        Package.COMP,
        Package.COMP_V1,
        Package.DISTRIB,
        Package.DISTRIB_V1,
        Package.FBC,
        Package.FBC_V2,
        Package.FBC_V3,
    }

    #: field name -> why this kind of model does not support it, checked by
    #: `_check_fields`. Empty for the model of a document, which supports
    #: every field it declares; `ModelDefinition` fills it with the fields
    #: which have no place on a `<comp:modelDefinition>`.
    _unsupported_fields: ClassVar[dict[str, str]] = {}

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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        packages: list[Package] | None = None,
        creators: list[Creator] | None = None,
        model_units: ModelUnits | None = None,
        conversionFactor: str | None = None,
        units: type[Units] | list[UnitDefinition] | None = None,
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
        strict: bool | None = None,
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
        self.conversionFactor = conversionFactor
        self.units = Model._normalize_units(units)
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
        self.strict = strict
        self.user_defined_constraints: list[UserDefinedConstraint] = (
            user_defined_constraints if user_defined_constraints else []
        )
        self.objectives: list[Objective] = objectives if objectives else []
        self.gene_products: list[GeneProduct] = gene_products if gene_products else []

        self.layouts: list | None = layouts

        #: `True` when the model was created by `sbmlutils.parser`, which
        #: suppresses the authoring hints when it is written back out
        self.parsed = False

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

        self._check_fields()
        self._freeze()  # no new attributes after this point

    @staticmethod
    def _normalize_units(
        units: type[Units] | list[UnitDefinition] | None,
    ) -> list[UnitDefinition]:
        """Normalize the units of a model to a list of UnitDefinitions.

        A model definition declares its units as a `class U(Units)`, which is
        the documented authoring style; the parser passes a list. Both are
        stored as a list.

        Args:
            units: a `Units` subclass, a list of UnitDefinitions, or None

        Returns:
            the unit definitions of the model

        Raises:
            ValueError: if an attribute of the `Units` class is neither a unit
                string nor a UnitDefinition
        """
        if units is None:
            return []
        if isinstance(units, list):
            return units

        udefs: list[UnitDefinition] = []
        for uid, definition in units.attributes():
            if isinstance(definition, str):
                udefs.append(UnitDefinition(sid=uid, definition=definition))
            elif isinstance(definition, UnitDefinition):
                udefs.append(definition)
            else:
                raise ValueError(
                    f"Units attributes must be a unit string or UnitDefinition, "
                    f"but '{type(definition)}' for '{definition}'."
                )
        return udefs

    def create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.Model:
        """Create Model.

        To create the complete SBMLDocument with the model use:

          doc = Document(model=model).create_sbml()
        """
        if self.parsed:
            with Sbase.no_authoring_hints():
                return self._create_sbml(doc)
        return self._create_sbml(doc)

    def _create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.Model:
        """Create the libsbml.Model of this model on the document and fill it.

        Args:
            doc: the libsbml.SBMLDocument the model is created on

        Returns:
            the created and filled libsbml.Model
        """
        model: libsbml.Model = doc.createModel()
        self._fill_sbml(model)
        return model

    def _fill_sbml(self, model: libsbml.Model) -> None:
        """Write the content of this model into the libsbml model created for it.

        Filling a libsbml model is separated from creating it, because the two
        kinds of model this module writes are created differently but hold the
        same content: the model of a document is created on the document with
        `createModel`, a `ModelDefinition` is created on the comp plugin of the
        document, and both are filled from here.

        **Everything created here is handed the model it is created in.** An
        element writer must not reach for its model itself: libsbml answers
        `getModel()` of an element inside a `<comp:modelDefinition>` with the
        model of the *document*, not with the model definition the element
        belongs to (measured with libsbml 5.21.2). Math parsed against that
        model resolves the ids of the wrong model, silently: a `time`
        parameter of the model definition is written as the SBML csymbol, and
        the document validates. So a new element type which creates something
        of its own passes the model on, as `Reaction` does to its
        `KineticLaw`, `Uncertainty` to its children, `Objective` to its flux
        objectives and `UserDefinedConstraint` to its components.

        Args:
            model: the created libsbml.Model, or the libsbml.ModelDefinition
                created for a `ModelDefinition`, which subclasses it

        Raises:
            ValueError: if a field this kind of model does not support is set
        """
        self._check_fields()
        self._set_fields(model, model)

        # history
        if self.creators:
            set_model_history(model, self.creators)

        # conversion factor
        if self.conversionFactor is not None:
            check(
                model.setConversionFactor(self.conversionFactor),
                f"Set conversionFactor on model '{self.sid}'",
            )

        # units
        for udef in self.units:
            udef.create_sbml(model=model)

        # model units
        if self.model_units:
            ModelUnits.set_model_units(model, self.model_units)

        # the two document level lists of comp: a `<comp:externalModelDefinition>`
        # and a `<comp:modelDefinition>` are children of the `<sbml>` element,
        # not of the `<model>`, so they are created on the document rather
        # than in the model, which is why they are not in the loop below. They
        # are created before the content of the model, as they were when they
        # were the first two keys of it: a `Submodel` of the model
        # instantiates them by `modelRef`. A `ModelDefinition` supports
        # neither of them, see its class docstring, so both lists are empty
        # for one and only the model of the document writes them.
        # an external model definition resolves the document from the model
        # it is given, a model definition is created on the document itself
        create_objects(
            model,
            obj_iter=self.external_model_definitions,
            key="external_model_definitions",
        )
        for model_definition in self.model_definitions:
            _create_object(model_definition, model.getSBMLDocument())

        # `fbc:strict` cannot be written on a model definition, see
        # `ModelDefinition`. Reported once for the document and only for a
        # model definition which claims `True`: `False` is what a reader of
        # the written document sees for an unset `fbc:strict` anyway. After
        # the model definitions were written, so that a model definition
        # which is rejected reports nothing but its rejection.
        strict_definitions = [
            model_definition.sid
            for model_definition in self.model_definitions
            if model_definition.strict
        ]
        if strict_definitions:
            logger.warning(
                "'strict' is not written on the model definitions %s: libsbml "
                "writes 'fbc:strict' twice on a <comp:modelDefinition>, which "
                "makes the written document unreadable, so a reader sees "
                "'fbc:strict' unset on them. See the class docstring of "
                "`ModelDefinition`.",
                strict_definitions,
            )

        # lists ofs
        for attr in [
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

    def get_sbml(self) -> str:
        """Create SBML model."""
        return Document(model=self).get_sbml()

    def check_packages(self, packages: list[Package] | None) -> list[Package]:
        """Check that all provided packages are supported.

        Args:
            packages: the packages of the model definition, in any order

        Returns:
            the packages, normalized to their version and in the canonical
            order of `packages_in_canonical_order`

        Raises:
            ValueError: if a package is not a `Package`, given twice, or not
                supported
        """
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

        return packages_in_canonical_order(packages_set)

    def _check_fields(self) -> None:
        """Check that no field this kind of model does not support is set.

        Checked when the model is constructed and again when it is written,
        since the lists of a model are commonly populated by assignment after
        it was constructed, which the constructor cannot see.

        Raises:
            ValueError: if a field of `_unsupported_fields` is set
        """
        for field, reason in self._unsupported_fields.items():
            if getattr(self, field, None):
                raise ValueError(
                    f"'{field}' is not supported on "
                    f"{type(self).__name__} '{self.sid}': {reason}"
                )

    def _has_comp_content(self) -> bool:
        """Determine whether writing this model requires the comp package.

        The `submodels`/`ports`/`replaced_elements`/`deletions`/
        `model_definitions`/`external_model_definitions` lists are the
        explicit comp constructs, but comp is also engaged by the
        `port=True`/`Port(...)` and `replacedBy=...` shorthand any
        `Sbase`-derived element can carry (`Sbase.create_port`,
        `Sbase.create_replaced_by`), which does not populate `ports` at all.
        Such an element need not be in a list of the model: the parameters
        and rules of a `Reaction` are written as elements of the model, a
        `KineticLaw` holds its local parameters, an `Event` its assignments.
        So every `Sbase` reachable from the model is checked, see
        `_iter_sbases`, rather than a list of the places an element can be
        nested in, which would miss the next one.
        This is checked here, once every element list of the model is
        populated, rather than defaulted in `check_packages`, which runs
        from `__init__` before any of them are.

        Returns:
            True if the model uses a comp construct anywhere
        """
        if (
            self.submodels
            or self.ports
            or self.replaced_elements
            or self.deletions
            or self.model_definitions
            or self.external_model_definitions
        ):
            return True

        return any(
            getattr(sbase, "port", None) not in (None, False)
            or bool(getattr(sbase, "replacedBy", None))
            for sbase in _iter_sbases(self)
        )

    def _required_packages(self) -> set[Package]:
        """Determine the packages the content of this model requires.

        The model of a document declares the packages of the document itself,
        but a model definition has no way to declare one: a package is
        declared on the `<sbml>` element. So the document reads off the
        content of its model definitions which packages they need, see
        `Document._create_sbml`. Every `Sbase` reachable from the model is
        walked, see `_iter_sbases`, rather than a list of the places an
        element can be nested in, which would miss the next one.

        Returns:
            the packages the content of this model requires, at the version
            this module writes; fbc content contributes `Package.FBC_V3`,
            since the content says that it is fbc content and not which
            version of fbc writes it
        """
        packages: set[Package] = set()
        if self._has_comp_content():
            packages.add(Package.COMP_V1)

        for sbase in _iter_sbases(self):
            if getattr(sbase, "uncertainties", None):
                packages.add(Package.DISTRIB_V1)
            if (
                # the key-value pairs of fbc version 3, which any element can
                # carry, and the three fbc lists of a model
                getattr(sbase, "keyValuePairs", None)
                or isinstance(sbase, (GeneProduct, Objective, UserDefinedConstraint))
                # the fbc attributes of a species and of a reaction
                or (
                    isinstance(sbase, Species)
                    and (sbase.charge is not None or sbase.chemicalFormula is not None)
                )
                or (
                    isinstance(sbase, Reaction)
                    and (
                        sbase.lowerFluxBound
                        or sbase.upperFluxBound
                        or sbase.geneProductAssociation
                    )
                )
            ):
                packages.add(Package.FBC_V3)

        return packages

    @staticmethod
    def merge_models(models: Iterable[Model]) -> Model:
        """Merge information from multiple models into a single model.

        The lists of the models are concatenated, the creators and the unit
        definitions are collected and deduplicated, and every other attribute
        is taken from the last model which sets it.

        Args:
            models: the models to merge; a single Model is returned unchanged

        Returns:
            the merged model

        Raises:
            ValueError: if no models are provided
        """
        if isinstance(models, Model):
            return models
        if not models:
            raise ValueError("No models are provided.")
        model = Model("template")
        # units are collected over all models and deduplicated by their id, so
        # that two models which define the same unit do not write it twice
        udefs: dict[str, UnitDefinition] = {}
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

                # units are collected and merged at the end; they are copied
                # like every other merged list, so that the merged model and
                # the model it was merged from do not share one object
                elif key == "units":
                    for udef in m2.units:
                        if udef.sid:
                            udefs[udef.sid] = deepcopy(udef)
                elif key == "creators":
                    if m2.creators:
                        for c in m2.creators:
                            creators[c] = None
                # !everything else is overwritten
                else:
                    setattr(model, key, value)

        model.units = list(udefs.values())
        model.creators = list(creators)

        return model


class ModelDefinition(Model):
    """A comp model definition: a complete model of its own inside a document.

    A `<comp:modelDefinition>` lives in the document next to its main model
    and is instantiated by the `Submodel`s which name it in their `modelRef`.
    In libsbml `ModelDefinition` subclasses `Model`, and so does this class:
    the same code writes every element of it, its unit definitions, its model
    units and its model history included. It is created on the comp plugin of
    the document rather than with `createModel`, which is the only thing that
    differs, see `_create_sbml`.

    What a model definition does not take, decided by what libsbml 5.21.2
    accepts on a `<comp:modelDefinition>` and writes for it:

    - `packages`: a package is declared on the `<sbml>` element, which is the
      document, and comp gives a model definition no place to declare one.
      Rejected. The document declares what the content of its model
      definitions needs, see `Model._required_packages`.
    - `model_definitions` and `external_model_definitions`: both are children
      of the `<sbml>` element as well, and the `CompModelPlugin` of a model
      definition has neither `createModelDefinition` nor
      `createExternalModelDefinition`, so comp does not nest them at all.
      Rejected.
    - `strict`: the fbc model plugin does attach to a model definition and
      `setStrict` succeeds on it, but libsbml then writes `fbc:strict` twice
      on the `<comp:modelDefinition>` element and the document it writes
      cannot be read back, by libsbml or any other XML parser ("Duplicate XML
      attribute"). The attribute is therefore not written and a model
      definition which sets it is reported. A model definition with fbc
      content consequently carries the libsbml error 2020209 ("Strict
      attribute required on <model>"): a document which validates with one
      error is usable, an unreadable one is not.

    Everything else a `Model` holds is written into it: the comp constructs
    of a model definition (`submodels`, `ports`, `replaced_elements`,
    `deletions`), the fbc ones (`gene_products`, `objectives`,
    `user_defined_constraints`, the charge and the chemical formula of a
    species, the flux bounds and the gene product association of a reaction,
    key-value pairs), the distrib `uncertainties` of any of its elements and
    a `layouts` list, all through the plugins libsbml attaches to a model
    definition as it does to the model of a document.

    A model definition is a model *in* a document, not the model *of* it: it
    is written by putting it in the `model_definitions` of a `Model` and
    writing that model. Handing one to `create_model`, to `Document` or to
    `get_sbml` is refused, since the document it would write has a
    `<comp:modelDefinition>` and no `<model>` at all.
    """

    _unsupported_fields: ClassVar[dict[str, str]] = {
        "packages": (
            "the packages of a document are declared on its <sbml> element, "
            "which is written from the packages of its model; the document "
            "declares what the content of a model definition needs"
        ),
        "model_definitions": (
            "comp does not nest model definitions, a <comp:modelDefinition> "
            "is a child of the <sbml> element; use the model definitions of "
            "the model of the document"
        ),
        "external_model_definitions": (
            "a <comp:externalModelDefinition> is a child of the <sbml> "
            "element; use the external model definitions of the model of the "
            "document"
        ),
    }

    def _create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.ModelDefinition:
        """Create the libsbml.ModelDefinition on the document and fill it.

        Args:
            doc: the libsbml.SBMLDocument the model definition is created on

        Returns:
            the created and filled libsbml.ModelDefinition

        Raises:
            ValueError: if a field a model definition does not support is set,
                or if the document does not declare the comp package
        """
        # checked before anything is created, so that a model definition
        # which is rejected leaves no empty `<comp:modelDefinition>` behind
        self._check_fields()
        doc_comp: libsbml.CompSBMLDocumentPlugin = _comp_plugin(
            doc, f"The model definition '{self.sid}'"
        )
        model_definition: libsbml.ModelDefinition = doc_comp.createModelDefinition()
        self._fill_sbml(model_definition)
        return model_definition


def _model_field_kind(annotation: object) -> type | None:
    """Classify a resolved `Model` field annotation as list-valued or scalar.

    `merge_models` concatenates a `list`-valued field of the merged models
    and overwrites every other field with the value of the last model that
    sets it. An annotation is list-valued when it is, once `| None` /
    `Optional[...]` is stripped, the bare `list` (`Model.layouts`), a
    subscripted `list[X]`, or a subscripted `Sequence[X]`. `Model.annotations`
    is declared `AnnotationsType` (`Sequence[AnnotationType]`, see its
    definition above `Model`), not `list[...]`, because it accepts any
    sequence but `Sbase.__init__` always stores it as a list, so `Sequence` is
    classified the same as `list` here.

    Args:
        annotation: a fully resolved field annotation, as returned by
            `typing.get_type_hints`, not the raw annotation string
            `from __future__ import annotations` leaves in `__annotations__`

    Returns:
        `list` for a list-valued annotation, `None` for a scalar one

    Raises:
        TypeError: if `annotation` is a shape this function does not
            recognize (a union of more than one non-`None` member, or a
            generic other than `list`/`Sequence`), so a field with an
            annotation shape nobody has taught this function about fails
            loudly at import instead of silently being classified as scalar
    """
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        members = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(members) != 1:
            raise TypeError(
                f"Cannot classify Model field annotation {annotation!r}: a "
                f"union must have exactly one non-None member."
            )
        return _model_field_kind(members[0])
    if annotation is list or origin is list or origin is Sequence:
        return list
    if origin is None:
        # a plain, non-generic annotation (str, bool, Any, or a class): scalar
        return None
    raise TypeError(
        f"Cannot classify Model field annotation {annotation!r}: unsupported "
        f"generic origin {origin!r}."
    )


def _derive_model_keys() -> dict[str, Any]:
    """Derive `Model._keys` from `Model`'s own field annotations.

    Called once, as a module-level statement after the `Model` class body,
    rather than during it: `from __future__ import annotations` turns every
    annotation in this file into a string, and `typing.get_type_hints`
    resolves each of `Model`'s forward references (`Species`, `Reaction`, ...)
    by looking them up in this module's namespace, which only holds them once
    the statements that define them, all located earlier in this module, have
    run. Resolving them while `Model`'s own class body is still executing,
    before the `Model` name itself is bound, is not possible. One of those
    forward references is `ModelDefinition`, which subclasses `Model` and is
    therefore defined between the class body and this call.

    Every field `Model` declares in its own class body (not one inherited
    from `Sbase` or `FrozenClass`) is classified by `_model_field_kind`;
    `ClassVar`s and private names (`_keys` itself, `_supported_packages`) are
    not fields and are excluded.

    Two fields are `list`-typed on `Model` but forced to `None` here, because
    `merge_models` merges them itself in a dedicated branch, deduplicated,
    rather than through its generic list-extend branch:

    - `units`, deduplicated by unit id: marking it `list` would run the
      generic branch instead, which writes duplicate unit ids into the merged
      model.
    - `creators`, deduplicated by equality: marking it `list` would also run
      the generic branch instead, and `merge_models` then unconditionally
      overwrites `model.creators` with the (never populated) dedup dict after
      its main loop, discarding the generic branch's result and leaving the
      merged model with no creators at all.

    Returns:
        the field name -> merge kind mapping `merge_models` reads through
        `Model._keys`

    Raises:
        TypeError: if a field annotation's shape is not recognized by
            `_model_field_kind`
    """
    own_annotations = inspect.get_annotations(Model)
    resolved = get_type_hints(Model)
    keys: dict[str, Any] = {}
    for name in own_annotations:
        if name.startswith("_"):
            continue
        hint = resolved[name]
        if get_origin(hint) is ClassVar:
            continue
        keys[name] = _model_field_kind(hint)

    keys["units"] = None
    keys["creators"] = None
    return keys


Model._keys = _derive_model_keys()


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
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sbml_level: int = SBML_LEVEL,
        sbml_version: int = SBML_VERSION,
    ):
        """Document constructor.

        Args:
            model: the model of the document
            sid: the id of the document
            name: the name of the document
            sboTerm: the SBO term of the document
            metaId: the meta id of the document
            annotations: the annotations of the document
            notes: the notes of the document
            keyValuePairs: the fbc key value pairs of the document
            sbml_level: the SBML level to write
            sbml_version: the SBML version to write

        Raises:
            ValueError: if the model is a `ModelDefinition`, which is a model
                of the document but not the model of the document
        """
        if isinstance(model, ModelDefinition):
            raise ValueError(
                f"A ModelDefinition is not the model of a document: "
                f"'{model.sid}' cannot be written on its own, a "
                f"<comp:modelDefinition> lives next to the <model> of a "
                f"document. Put it in the `model_definitions` of a `Model` "
                f"and write that model."
            )
        self.model = model
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.annotations: list[AnnotationType] = (
            list(annotations) if annotations else []
        )
        # `Document` does not call `Sbase.__init__` (it has no sboTerm
        # handling and sets its own fields), so the notes normalization
        # `Sbase.__init__` otherwise applies is done here explicitly
        self.notes = Sbase._process_notes(notes)
        self.keyValuePairs = keyValuePairs
        self.sbml_level = sbml_level
        self.sbml_version = sbml_version
        self.doc: libsbml.SBMLDocument | None = None

        sbmlutils_notes = Sbase._process_notes(
            """
        Created with [https://github.com/matthiaskoenig/sbmlutils](https://github.com/matthiaskoenig/sbmlutils).
        [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5525390.svg)](https://doi.org/10.5281/zenodo.5525390)
        """
        )
        assert sbmlutils_notes is not None

        if self.notes is None:
            self.notes = sbmlutils_notes
        else:
            # both are already xhtml, appending the attribution as it is
            # would nest a body inside the notes; its content goes into their
            # body instead, which keeps an `<html>` root with its head
            self.notes = _append_to_xhtml_body(
                self.notes, _xhtml_body_content(sbmlutils_notes)
            )

    def create_sbml(self) -> libsbml.SBMLDocument:
        """Create the libsbml.SBMLDocument of the model.

        This writes a whole document, so an annotation resource which cannot
        be canonicalized is reported once for its collection rather than once
        for every element it is written on, see
        `annotator.collect_resource_losses`.

        Returns:
            the created libsbml.SBMLDocument
        """
        with annotator.collect_resource_losses():
            return self._create_sbml()

    def _create_sbml(self) -> libsbml.SBMLDocument:
        """Create the libsbml.SBMLDocument and all its objects.

        Returns:
            the created libsbml.SBMLDocument
        """
        logger.info("Create SBML for model '%s'", self.model.sid)

        # the packages actually needed to write this model: comp is added
        # when the model has comp content the definition did not explicitly
        # request it for (see `Model._has_comp_content`), and so is whatever
        # the content of a model definition of the document needs, which is a
        # model of its own but has no place to declare a package (see
        # `Model._required_packages`). This must be decided before the
        # namespace is built, since libsbml cannot enable a package on the
        # document after it exists.
        packages = list(self.model.packages)
        required: set[Package] = set()
        if self.model._has_comp_content():
            required.add(Package.COMP_V1)
        for model_definition in self.model.model_definitions:
            required |= model_definition._required_packages()

        if Package.COMP_V1 in required and Package.COMP_V1 not in packages:
            packages.append(Package.COMP_V1)
        if Package.DISTRIB_V1 in required and Package.DISTRIB_V1 not in packages:
            packages.append(Package.DISTRIB_V1)
        if Package.FBC_V3 in required and not (
            Package.FBC_V2 in packages or Package.FBC_V3 in packages
        ):
            # the content only says that it needs fbc, so the version is the
            # one `Package.FBC` normalizes to; a document which already
            # declares a version of fbc keeps it
            packages.append(Package.FBC_V3)
        # in the canonical order, so that a model which engages a package
        # through its content declares it where a model which asks for it
        # declares it, see `packages_in_canonical_order`
        packages = packages_in_canonical_order(packages)

        # create core model
        sbmlns = libsbml.SBMLNamespaces(self.sbml_level, self.sbml_version)

        # add all the package
        for package in packages:
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

        if Package.COMP_V1 in packages:
            self.doc.setPackageRequired("comp", True)
        if (Package.FBC_V2 in packages) or (Package.FBC_V3 in packages):
            self.doc.setPackageRequired("fbc", False)
            fbc_plugin: libsbml.FbcModelPlugin = sbml_model.getPlugin("fbc")
            # `Model.strict` is `None` for a model which never set it, which
            # keeps today's default of writing `fbc:strict="false"`, see the
            # field's docstring in `Model`
            strict = self.model.strict if self.model.strict is not None else False
            check(
                fbc_plugin.setStrict(strict),
                f"Set fbc:strict on model '{self.model.sid}'",
            )
        if Package.DISTRIB_V1 in packages:
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

    # create and write SBML; creating the document and annotating it from a
    # file both write annotation resources, and one call writes one document,
    # so both report into one collector, see `collect_resource_losses`
    with annotator.collect_resource_losses():
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
