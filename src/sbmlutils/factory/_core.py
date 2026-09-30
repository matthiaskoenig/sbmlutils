"""The base of the elements of the factory.

`Sbase`, which every element derives from, `KeyValuePair` and `Value`,
the reporting of the attributes and the content libsbml does not write,
and the helpers for math, notes and the package plugins which the
elements share.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager, contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeAlias

import libsbml

from sbmlutils.metadata import BQB, BQM, SBO, annotator
from sbmlutils.metadata.annotator import Annotation
from sbmlutils.notes import Notes, NotesFormat, detect_format
from sbmlutils.validation import ScopedLossCollector, check

if TYPE_CHECKING:
    from sbmlutils.factory.distrib import Uncertainty

logger = logging.getLogger(__name__)


SBML_LEVEL = 3  # default SBML level
SBML_VERSION = 1  # default SBML version
PORT_SUFFIX = "_port"
PORT_UNIT_SUFFIX = "_unit_port"

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

#: the libsbml types whose core `id` and `name` libsbml writes into no
#: document. Measured with libsbml 5.21.2 on a `<comp:replacedElement>`, a
#: `<comp:replacedBy>` and a nested `<comp:sBaseRef>`: below SBML L3V2 both
#: setters answer `LIBSBML_UNEXPECTED_ATTRIBUTE`, at L3V2 both answer success,
#: and the document written carries neither attribute at either version. So no
#: level and no package version keeps them and neither is written, see
#: `_record_unwritten_attribute`. A `<comp:port>` and a `<comp:deletion>` are
#: not affected: comp gives both an id and a name of their own, written as the
#: package attributes `comp:id` and `comp:name`.
_UNWRITTEN_ID_TYPECODES: frozenset[int] = frozenset(
    {
        libsbml.SBML_COMP_REPLACEDELEMENT,
        libsbml.SBML_COMP_REPLACEDBY,
        libsbml.SBML_COMP_SBASEREF,
    }
)


def _create_object(obj: Any, container: Any) -> libsbml.SBase | None:
    """Create one object in its container, naming it if the creation fails.

    Args:
        obj: the object to create, e.g. a `Parameter`
        container: what its `create_sbml` takes, the `libsbml.Model` for an
            element of a model and the `libsbml.SBMLDocument` for a
            `ModelDefinition`, which is a child of the `<sbml>` element

    Returns:
        the created libsbml object, `None` for an element which the document
        cannot carry at all and whose writer reported it

    Raises:
        Exception: whatever `create_sbml` raises, after reporting which
            object it was raised for, which the traceback alone does not say
    """
    try:
        return obj.create_sbml(container)
    except Exception as err:
        logger.error("Error creating SBML object for '%s'", obj)
        logger.error(err)
        raise


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
    :raises ValueError: if an object is `None`
    """
    sbml_objects: dict[str, libsbml.SBase] = {}

    for obj in obj_iter:
        if obj is None:
            raise ValueError(
                f"An object of '{key or 'objects'}' is 'None', check for an "
                f"incorrect terminating ',' after the objects: {list(sbml_objects)}"
            )

        sbml_obj: libsbml.SBase | None = _create_object(obj, model)
        if sbml_obj is None:
            # the document cannot carry the element at all and the writer
            # which refused it has reported why, e.g. an
            # `<fbc:userDefinedConstraint>` in an fbc version 2 document
            continue
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


def _sbml_element_name(sbase: Any) -> str:
    """Name the SBML element an attribute was set on.

    `sbase` is either a libsbml object, which answers `getElementName` with
    its own tag, or a libsbml **plugin**, which carries the attributes of a
    package on an element and has no `getElementName` at all (measured with
    libsbml 5.21.2: `FbcReactionPlugin` does not define it). A plugin is
    asked for the element it belongs to instead.

    Args:
        sbase: the libsbml object, or plugin, the attribute was set on

    Returns:
        the SBML element name, e.g. `species`; the name of the package for a
        plugin which is attached to nothing, which libsbml does not produce
    """
    if isinstance(sbase, libsbml.SBasePlugin):
        parent: libsbml.SBase | None = sbase.getParentSBMLObject()
        if parent is None:
            return str(sbase.getPackageName())
        return str(parent.getElementName())
    return str(sbase.getElementName())


def _sbml_flavour(sbase: Any) -> str:
    """Name the SBML level, version and package an object is written in.

    Args:
        sbase: the libsbml object, or the libsbml plugin, the attribute was
            set on; both answer `getLevel`, `getVersion`, `getPackageName`
            and `getPackageVersion`

    Returns:
        the flavour as a phrase, e.g. `SBML L3V1` for an element of the core
        and `fbc version 2 of an SBML L3V1 document` for one of a package
    """
    level: int = sbase.getLevel()
    version: int = sbase.getVersion()
    package: str = sbase.getPackageName()
    if package and package != "core":
        return (
            f"{package} version {sbase.getPackageVersion()} of an "
            f"SBML L{level}V{version} document"
        )
    return f"SBML L{level}V{version}"


#: the version of each package the factory writes, which is what a document
#: has to declare to carry the content of that version
_LATEST_PACKAGE_VERSION: dict[str, int] = {"comp": 1, "distrib": 1, "fbc": 3}


def _flavour_advice(sbase: Any) -> str:
    """Say what to write to keep an attribute the document has no place for.

    Args:
        sbase: the libsbml object, or plugin, the attribute was set on

    Returns:
        the sentence, empty if no level, version or package version this
        module writes has the attribute either
    """
    package: str = sbase.getPackageName()
    if package and package != "core":
        latest = _LATEST_PACKAGE_VERSION.get(package)
        if latest is not None and sbase.getPackageVersion() < latest:
            return f"Declare {package} version {latest} to keep it."
    # an element of a package carries the attributes of an `SBase` too, and
    # those came with SBML L3V2: a `<comp:replacedElement>` has no `comp:id`
    # below it although comp version 1 is the only version there is
    if (sbase.getLevel(), sbase.getVersion()) < (3, 2):
        return "Write SBML Level 3 Version 2 to keep it."
    return ""


@dataclass
class _AttributeLoss:
    """The elements of one kind whose attribute the document cannot carry.

    Attributes:
        count: how many elements of the kind lost the attribute
        example: the first of them, named in the report
        flavour: the level, version and package version which has no such
            attribute, see `_sbml_flavour`
        advice: what to write to keep the attribute, see `_flavour_advice`
    """

    count: int = 0
    example: str = ""
    flavour: str = ""
    advice: str = ""


def _report_attribute_loss(key: tuple[str, ...], loss: _AttributeLoss) -> None:
    """Report the elements of one kind which lost one attribute.

    Args:
        key: the SBML element name and the attribute, as collected
        loss: the count, the example, the flavour and the advice
    """
    element_name, attribute = key
    logger.warning(
        "The '%s' of %s <%s> element(s) is not written: %s has no such "
        "attribute, e.g. '%s'.%s",
        attribute,
        loss.count,
        element_name,
        loss.flavour,
        loss.example,
        f" {loss.advice}" if loss.advice else "",
    )


#: the attributes which the level, the version or the package version of the
#: document being written has no place for, collected per document so that
#: one decision is reported once, see `collect_attribute_losses`
_attribute_losses: ScopedLossCollector[tuple[str, ...], _AttributeLoss] = (
    ScopedLossCollector("sbmlutils_attribute_losses", _report_attribute_loss)
)


@dataclass
class _UnwrittenAttribute:
    """The elements of one kind whose attribute libsbml does not write.

    Attributes:
        count: how many elements of the kind lost the attribute
        example: the first of them, named in the report
    """

    count: int = 0
    example: str = ""


def _report_unwritten_attribute(
    key: tuple[str, ...], loss: _UnwrittenAttribute
) -> None:
    """Report the elements of one kind whose attribute libsbml does not write.

    Args:
        key: the SBML element name and the attribute, as collected
        loss: the count and the example
    """
    element_name, attribute = key
    logger.warning(
        "The '%s' of %s <%s> element(s) is not written: libsbml writes no "
        "core id or name on this element at any SBML level, e.g. '%s'.",
        attribute,
        loss.count,
        element_name,
        loss.example,
    )


#: the elements whose core id or name libsbml does not write, collected per
#: document so that the loss is reported once per kind of element, see
#: `_UNWRITTEN_ID_TYPECODES`
_unwritten_attributes: ScopedLossCollector[tuple[str, ...], _UnwrittenAttribute] = (
    ScopedLossCollector("sbmlutils_unwritten_attributes", _report_unwritten_attribute)
)


@contextmanager
def collect_attribute_losses() -> Iterator[None]:
    """Report the attributes a document does not carry once per kind.

    An attribute is lost for the same reason on every element which carries
    it, and a report per element buries that one reason under thousands of
    lines. Inside this context every such loss is collected and logged at
    debug, and one warning per element kind and attribute is emitted when the
    context ends. Outside it, every loss is warned about on its own. Two
    kinds are collected:

    - an attribute which the SBML level and version of the document, or the
      version of the package, does not have at all, which the caller fixes
      for every element at once by writing SBML Level 3 Version 2 or by
      declaring a later version of the package, see `_record_attribute_loss`;
    - an attribute which libsbml writes into no document whatever the level,
      the core id and name of a comp reference, which the caller can do
      nothing about and which is therefore reported without advice, see
      `_record_unwritten_attribute`.

    The context is entered by the code which writes a whole document,
    `Document.create_sbml` and `create_model`; a context inside an active one
    collects into it and reports nothing of its own.

    Yields:
        None
    """
    with _attribute_losses.scope(), _unwritten_attributes.scope():
        yield


def _record_unwritten_attribute(
    sbase: Any, attribute: str, value: Any, element: Any
) -> None:
    """Record an attribute libsbml writes into no document.

    Args:
        sbase: the libsbml object the attribute would be set on
        attribute: the name of the SBML attribute, `id` or `name`
        value: the value which is not written
        element: the model element the attribute belongs to
    """
    element_name: str = _sbml_element_name(sbase)
    loss = _unwritten_attributes.group(
        (element_name, attribute), lambda: _UnwrittenAttribute(example=str(element))
    )
    if loss is None:
        logger.warning(
            "The '%s' of '%s' is not written: libsbml writes no core id or "
            "name on a <%s> at any SBML level.",
            attribute,
            element,
            element_name,
        )
        return
    loss.count += 1
    logger.debug(
        "The '%s' of '%s' is not written with the value '%s': libsbml writes "
        "no core id or name on a <%s> at any SBML level.",
        attribute,
        element,
        value,
        element_name,
    )


def _record_attribute_loss(
    sbase: Any, attribute: str, value: Any, element: Any
) -> None:
    """Record an attribute the document being written has no place for.

    Args:
        sbase: the libsbml object, or plugin, the attribute was set on
        attribute: the name of the SBML attribute, e.g. `name`
        value: the value which was not written
        element: the model element the attribute belongs to
    """
    element_name: str = _sbml_element_name(sbase)
    loss = _attribute_losses.group(
        (element_name, attribute),
        lambda: _AttributeLoss(
            example=str(element),
            flavour=_sbml_flavour(sbase),
            advice=_flavour_advice(sbase),
        ),
    )
    if loss is None:
        advice = _flavour_advice(sbase)
        logger.warning(
            "The '%s' of '%s' is not written: %s has no such attribute.%s",
            attribute,
            element,
            _sbml_flavour(sbase),
            f" {advice}" if advice else "",
        )
        return
    loss.count += 1
    logger.debug(
        "The '%s' of '%s' is not written with the value '%s': %s has no such "
        "attribute.",
        attribute,
        element,
        value,
        loss.flavour,
    )


def _check_attribute(
    status: int, sbase: Any, attribute: str, value: Any, element: Any
) -> bool:
    """Report an attribute which libsbml did not write, naming the element.

    A libsbml setter answers with a status code instead of raising, so an
    attribute which could not be written is lost in silence unless the status
    is looked at. The two kinds of failure are reported differently:

    - `LIBSBML_UNEXPECTED_ATTRIBUTE` means the document has no place for the
      attribute at all, which no value can fix and which one decision fixes
      for every element at once, so it is collected for the document and
      reported once per element kind, see `collect_attribute_losses`;
    - every other status, an invalid **value** above all, is a property of
      the one element and goes through `check`, which reports it as an error.

    Both messages are built in the failure branch, so that a document which
    is written without a loss pays nothing for the report.

    Args:
        status: the status code the libsbml setter answered with
        sbase: the libsbml object, or plugin, the attribute was set on, which
            states the level, the version and the package version it has to
            fit, see `_sbml_flavour`
        attribute: the name of the SBML attribute, e.g. `compartment`
        value: the value which was to be written
        element: the model element the attribute belongs to

    Returns:
        `True` if the attribute was written, `False` if it was not
    """
    if status == libsbml.LIBSBML_OPERATION_SUCCESS:
        return True
    if status == libsbml.LIBSBML_UNEXPECTED_ATTRIBUTE:
        _record_attribute_loss(sbase, attribute, value, element)
        return False
    return check(status, f"Set {attribute} '{value}' on '{element}'")


@dataclass
class _ContentLoss:
    """The content of one kind which a document cannot carry.

    Attributes:
        count: how many pieces of the content are lost, e.g. 7 key-value pairs
        elements: how many elements carried them
        example: the first of those elements, named in the report
        needed: the fbc version which would carry the content
    """

    count: int = 0
    elements: int = 0
    example: str = ""
    needed: int = 0


def _report_content_loss(key: tuple[str, ...], loss: _ContentLoss) -> None:
    """Report the content of one kind which a document cannot carry.

    Args:
        key: what the content is and why the document cannot carry it, as
            collected
        loss: the count, the number of elements, the example and the version
    """
    what, reason = key
    logger.error(
        "The %s %s of %s element(s) are not written: %s, e.g. '%s'. Declare "
        "fbc version %s to keep them.",
        loss.count,
        what,
        loss.elements,
        reason,
        loss.example,
        loss.needed,
    )


#: the fbc content the document being written cannot carry, collected per
#: document so that one decision, declaring a later fbc version, is reported
#: once, see `collect_content_losses`
_content_losses: ScopedLossCollector[tuple[str, ...], _ContentLoss] = (
    ScopedLossCollector("sbmlutils_content_losses", _report_content_loss)
)


def collect_content_losses() -> AbstractContextManager[None]:
    """Report the content a document cannot carry once per kind.

    Content which the version of a package does not have at all is lost on
    every element which carries it, and declaring the version which has it is
    one decision which keeps all of them, exactly as writing a later SBML
    level and version is for an attribute, see `collect_attribute_losses`.
    Inside this context every such loss is collected and one report per kind
    of content is emitted when the context ends. Outside it, the content of
    every element is reported on its own.

    The context is entered by the code which writes a whole document,
    `Document.create_sbml` and `create_model`; a context inside an active one
    collects into it and reports nothing of its own.

    Returns:
        the context manager
    """
    return _content_losses.scope()


def _record_content_loss(
    what: str, reason: str, needed: int, count: int, element: Any
) -> None:
    """Record content the document being written cannot carry.

    Args:
        what: the content, named in the report, e.g. `key-value pair(s)`
        reason: why the document cannot carry it, a clause of the report
        needed: the fbc version which would carry the content
        count: how many pieces of the content are lost
        element: the model element the content belongs to
    """
    loss = _content_losses.group(
        (what, reason), lambda: _ContentLoss(example=str(element), needed=needed)
    )
    if loss is None:
        logger.error(
            "The %s %s of '%s' are not written: %s. Declare fbc version %s to "
            "keep them.",
            count,
            what,
            element,
            reason,
            needed,
        )
        return
    loss.count += count
    loss.elements += 1
    logger.debug("The %s %s of '%s' are not written: %s.", count, what, element, reason)


def _fbc_version_allows(
    plugin: Any, needed: int, what: str, count: int, element: Any
) -> bool:
    """Say whether the fbc version of a document can carry this content.

    The one place which answers that, and which reports the content it
    refuses. A `<fbc:keyValuePair>` and an `<fbc:userDefinedConstraint>` are
    both fbc version 3, and in an fbc version 2 document libsbml creates the
    element and answers every attribute of it with
    `LIBSBML_UNEXPECTED_ATTRIBUTE` (measured with libsbml 5.21.2), so what
    gets written is an empty element which no reader can use. The version is
    read from the plugin of the created libsbml object, which is the version
    of the document being written, rather than from the packages of the
    `Model`, the way `Species._set_charge` reads it.

    Declaring that version is one decision which keeps the content of every
    element of the document, so the loss is collected and reported once per
    kind of content and per reason, see `collect_content_losses`. A charge
    which fbc version 2 cannot express is the other case and stays one report
    per species: it is a refused **value**, different on each of them, and no
    decision about the document rounds it, see `Species._set_charge`.

    Args:
        plugin: the fbc plugin the content would be created on, `None` for a
            document which does not declare fbc at all
        needed: the fbc version the content needs
        what: the content, named in the report, e.g. `key-value pair(s)`
        count: how many of them would be lost
        element: the model element the content belongs to

    Returns:
        `True` if the content can be written, `False` if it was reported and
        nothing is to be written
    """
    if plugin is None:
        _record_content_loss(
            what,
            "the document does not declare the fbc package",
            needed,
            count,
            element,
        )
        return False
    have: int = plugin.getPackageVersion()
    if have < needed:
        _record_content_loss(
            what,
            f"the content is fbc version {needed}, the document is fbc version {have}",
            needed,
            count,
            element,
        )
        return False
    return True


def _sbo_term(sbo_term: Any) -> Any:
    """Normalize an SBO term to the spelling an SBML document is written with.

    A model definition may state an SBO term as an `SBO` member, as the
    `SBO:0000011` of the document or as the `SBO_0000011` of the ontology
    file; libsbml accepts only the first spelling and answers the second with
    `LIBSBML_INVALID_ATTRIBUTE_VALUE`. Every element normalizes through this in
    `Sbase._set_fields`, the species reference of an `EquationPart` included,
    see `_SpeciesReference`.

    Args:
        sbo_term: the SBO term as the model definition states it

    Returns:
        the term as it is written, unchanged for a value which is neither an
        `SBO` member nor a string, which libsbml then refuses and the caller
        reports
    """
    if isinstance(sbo_term, SBO):
        return sbo_term.curie
    if isinstance(sbo_term, str):
        return sbo_term.replace("_", ":")
    return sbo_term


def _set_variable_type(sbase: Any, variable_type: Any, element: Any) -> None:
    """Write the fbc variableType of an element, if the document can carry it.

    `fbc:variableType` was added in **fbc version 3**. An fbc version 2
    document has no such attribute at all, and its flux objectives and
    constraint components are linear by definition: the objective of an fbc
    version 2 model is the sum of `coefficient * flux`. So `linear` is what
    such a document means anyway and not writing it loses nothing, which is
    why it is not reported; `quadratic` cannot be expressed there at all and
    is, once per document, with every other attribute the document has no
    place for, see `collect_attribute_losses`.

    That distinction matters because `Objective` and `UserDefinedConstraint`
    give the elements which state none the `linear` of the fbc version 3
    default, so every fbc version 2 model built with the
    `{reaction: coefficient}` shorthand carries a variable type its author
    never chose.

    Args:
        sbase: the created `libsbml.FluxObjective` or
            `libsbml.UserDefinedConstraintComponent`, which states the fbc
            version of the document being written
        variable_type: the variable type to write, normalized by
            `FluxObjective.normalize_variable_type`
        element: the model element it belongs to, named in the report
    """
    if sbase.getPackageVersion() >= 3:
        _check_attribute(
            sbase.setVariableType(variable_type),
            sbase,
            "variableType",
            variable_type,
            element,
        )
        return
    if variable_type in (libsbml.FBC_VARIABLE_TYPE_LINEAR, "linear"):
        logger.debug(
            "The linear variableType of '%s' is not written: an fbc version "
            "%s document has no such attribute and is linear anyway.",
            element,
            sbase.getPackageVersion(),
        )
        return
    _record_attribute_loss(sbase, "variableType", variable_type, element)


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


# The aliases are evaluated rather than written as strings: `typing.get_type_hints`
# resolves a string alias in the namespace of the module which uses it, and
# `_derive_model_keys` resolves the fields of `Model` in `sbmlutils.factory.model`.

#: an annotation is either a full RDF annotation or a `(qualifier, resource)` tuple
AnnotationType: TypeAlias = Annotation | tuple[BQB | BQM, str]
#: annotations are accepted as any sequence, an `Sbase` stores them as a list, so
#: that annotations can be appended after the object was created
AnnotationsType: TypeAlias = Sequence[AnnotationType]
OptionalAnnotationsType: TypeAlias = Sequence[AnnotationType] | None


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


def _no_plugin_reason(sbase: Any, package: str) -> str:
    """Say why a libsbml object has no plugin of a package.

    libsbml attaches the plugin of a package to an element of a document
    which declares that package, and a package can only be declared on an
    SBML Level 3 document, so there are exactly two reasons, and the one
    which applies is what a caller can do something about.

    Args:
        sbase: the libsbml object, or plugin, which has no such plugin
        package: the name of the package, e.g. `fbc`

    Returns:
        the reason as a clause, without a leading or trailing stop
    """
    level: int = sbase.getLevel()
    if level < 3:
        return (
            f"an SBML L{level}V{sbase.getVersion()} document cannot declare "
            f"the {package} package"
        )
    return f"the document does not declare the {package} package"


def _package_plugin(sbase: libsbml.SBase, package: str, what: str) -> Any:
    """Get the plugin of a package on a libsbml object, or say why there is none.

    The one place which dereferences a package plugin, so that an element
    whose content needs a package it does not have says which element, which
    package and why the package is absent, instead of ending in an
    `AttributeError` on `None` from wherever the plugin was first used.

    Args:
        sbase: the libsbml object the content would be created on
        package: the name of the package, e.g. `fbc`
        what: the element whose content needs the package, for the message

    Returns:
        the plugin of the package on the libsbml object

    Raises:
        ValueError: if the object has no plugin of the package, see
            `_no_plugin_reason`
    """
    plugin = sbase.getPlugin(package)
    if plugin is None:
        raise ValueError(
            f"{what} cannot be written: {_no_plugin_reason(sbase, package)}."
        )
    return plugin


def _comp_plugin(sbase: libsbml.SBase, what: str) -> Any:
    """Get the comp plugin of a libsbml object for a port or a replacement.

    Args:
        sbase: the libsbml object, the model for a port, the replaced
            element for a replacement
        what: the port or the replacement, for the error message

    Returns:
        the comp plugin of the libsbml object

    Raises:
        ValueError: if the object has no comp plugin, which `create_model`
            gives every model with comp content, see
            `Model._has_comp_content`
    """
    return _package_plugin(sbase, "comp", what)


def _fbc_plugin(sbase: libsbml.SBase, what: str) -> Any:
    """Get the fbc plugin of a libsbml object for the fbc content of an element.

    Args:
        sbase: the libsbml object the fbc content is created on, the model
            for a gene product or an objective, the reaction for its flux
            bounds and its gene product association
        what: the element whose fbc content needs the package, for the error
            message

    Returns:
        the fbc plugin of the libsbml object

    Raises:
        ValueError: if the object has no fbc plugin, which `create_model`
            gives every model with fbc content of an SBML Level 3 document,
            see `Model._required_packages`
    """
    return _package_plugin(sbase, "fbc", what)


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
    #: `metaIdRef` names the element by its metaid.
    #:
    #: Measured with libsbml 5.21.2, on an SBML L3V2 document built with
    #: libsbml alone, `getElementBySId` answers with every element type this
    #: module can put a port on **except** an `InitialAssignment`, an
    #: `AssignmentRule`, a `RateRule`, an `AlgebraicRule`, an
    #: `EventAssignment`, a `LocalParameter` and a `UnitDefinition`, although
    #: each of them carries its id in the written XML. A port which names one
    #: of the first five by `comp:idRef` is rejected with libsbml 1020702
    #: ("The 'comp:idRef' attribute must be the 'id' of a model element") and
    #: one which names a local parameter or a unit definition that way makes
    #: the flat model invalid (1090105); `comp:metaIdRef` to any of them
    #: validates, and a unit definition has `comp:unitRef` of its own.
    _port_reference: ClassVar[Literal["idRef", "unitRef", "metaIdRef"]] = "idRef"

    #: whether the id of an element of this class is only carried by an SBML
    #: L3V2 document, so that a port cannot name it by `comp:idRef` below
    #: L3V2 and names it by its metaid there instead. Two reasons make an id
    #: need L3V2, both measured with libsbml 5.21.2: a `<kineticLaw>`, a
    #: `<trigger>`, a `<priority>`, a `<delay>` and a `<constraint>` have no
    #: `id` attribute at all below L3V2, and libsbml writes the `fbc:id` of a
    #: `<fbc:keyValuePair>` into an L3V1 document but does not read it back.
    #: A `<comp:port>` by `comp:idRef` to any of them is rejected in an L3V1
    #: document with libsbml 1020702, which is what `create_model` writes by
    #: default.
    _port_id_needs_l3v2: ClassVar[bool] = False

    #: whether `_set_fields` hints that `name` should be set when it is not.
    #: Switched off on the classes a name is unusual on: those identified by
    #: what they reference or by their key and value (an fbc version 2
    #: document cannot even carry the name of a key value pair), and those
    #: created from a formula string in the authoring style, which has no
    #: place for a name, see `no_authoring_hints` for the other suppression
    _hint_name: ClassVar[bool] = True

    #: whether `_set_fields` hints that `sboTerm` should be set when it is
    #: not, switched off on the classes an sboTerm is unusual on
    _hint_sbo_term: ClassVar[bool] = True

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
        does, and when the element is built by the factory rather than by
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

        Raises:
            ValueError: if an entry is neither an `Annotation` nor a
                `(qualifier, resource)` tuple
        """
        annotations: list[Annotation] = []
        if annotation_objects is not None:
            for annotation_obj in annotation_objects:
                if isinstance(annotation_obj, Annotation):
                    annotations.append(annotation_obj)
                elif isinstance(annotation_obj, (tuple, list, set)):
                    annotations.append(Annotation.from_tuple(annotation_obj))
                else:
                    raise ValueError(
                        f"An annotation is an 'Annotation' or a "
                        f"'(qualifier, resource)' tuple, but "
                        f"'{type(annotation_obj).__name__}' was given: "
                        f"'{annotation_obj}'."
                    )
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
            # many elements only have an id from SBML L3V2 on, e.g. a
            # constraint or a kinetic law; below it the id has no place in
            # the document, which one decision fixes for all of them, so it
            # is reported with every other such attribute, see
            # `collect_attribute_losses`
            if sbase.getTypeCode() in _UNWRITTEN_ID_TYPECODES:
                # a comp reference whose id libsbml writes into no document,
                # which the setter says at one level and not at the other:
                # reported here, so that the loss is the same at both
                _record_unwritten_attribute(sbase, "id", self.sid, self)
            elif sbase.getTypeCode() in _ID_ATTRIBUTE_TYPECODES:
                _check_attribute(
                    sbase.setIdAttribute(self.sid), sbase, "id", self.sid, self
                )
            else:
                _check_attribute(sbase.setId(self.sid), sbase, "id", self.sid, self)
        if self.name is not None:
            self._set_name(sbase, self.name)
        elif Sbase._authoring_hints.get() and self._hint_name:
            logger.warning("'name' should be set on '%s'", self)
        if self.sboTerm is not None:
            sbo = _sbo_term(self.sboTerm)
            _check_attribute(sbase.setSBOTerm(sbo), sbase, "sboTerm", sbo, self)
        elif Sbase._authoring_hints.get() and self._hint_sbo_term:
            logger.warning("'sboTerm' should be set on '%s'", self)
        if self.metaId is not None:
            _check_attribute(
                sbase.setMetaId(self.metaId), sbase, "metaid", self.metaId, self
            )

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

    def _set_name(self, sbase: Any, name: str) -> None:
        """Set the name on the created libsbml object.

        Args:
            sbase: the libsbml object created by `create_sbml`
            name: the name to set
        """
        if sbase.getTypeCode() in _UNWRITTEN_ID_TYPECODES:
            _record_unwritten_attribute(sbase, "name", name, self)
        else:
            _check_attribute(sbase.setName(name), sbase, "name", name, self)

    @classmethod
    def _port_reference_for(
        cls, level: int, version: int
    ) -> Literal["idRef", "unitRef", "metaIdRef"]:
        """Get how a port names an element of this class in such a document.

        A port names its element by what the document being written carries,
        which for the classes whose id needs SBML L3V2 is not the same in
        every document, see `_port_id_needs_l3v2`.

        Args:
            level: the SBML level of the document being written
            version: the SBML version of the document being written

        Returns:
            the reference the port uses
        """
        if cls._port_reference == "idRef" and cls._port_id_needs_l3v2:
            return "idRef" if (level, version) >= (3, 2) else "metaIdRef"
        return cls._port_reference

    def _port_target(self, reference: str) -> str | None:
        """Get the name a port references this element by, if it has one.

        Args:
            reference: the reference the port uses, see `_port_reference_for`

        Returns:
            the id of the element for `idRef` and `unitRef`, its metaid for
            `metaIdRef`, `None` if the element does not state it
        """
        return self.metaId if reference == "metaIdRef" else self.sid

    def _port_id(self, reference: str) -> str:
        """Get the id the `port=True` shorthand gives the port of this element.

        The port is named after the name it references the element by, which
        is unique in the document: an `SId` for `idRef` and `unitRef`, and the
        metaid for `metaIdRef`, whose `SId` is scoped to the element it lives
        in. Two local parameters called `kf` in two kinetic laws would
        otherwise be given two ports called `kf_port` (libsbml 1010303, "Ports
        must have unique ids", and 10307, "Duplicate 'metaid' attribute
        value").

        Args:
            reference: the reference the port uses, see `_port_reference_for`

        Returns:
            the id, which is also the metaid of the port; the empty string
            for an element with no name a port can reference
        """
        suffix = PORT_UNIT_SUFFIX if reference == "unitRef" else PORT_SUFFIX
        target = self._port_target(reference)
        return "" if target is None else f"{target}{suffix}"

    def _port_references_self(self) -> bool:
        """Say whether the port of this element has to be made to name it.

        The `port=True` shorthand and a `Port` object which names nothing of
        its own are both made to reference this element, by the reference
        `_port_reference_for` names for the document being written; a `Port`
        which carries a reference of its own keeps it. Both `_port_loss` and `create_port`
        ask this, which is why it is one predicate.

        Returns:
            `True` if the port references this element, `False` if it carries
            a reference of its own

        Raises:
            AttributeError: if the element has no port at all; both callers
                answer that case before they ask
        """
        if isinstance(self.port, bool):
            return True
        return not (
            self.port.portRef
            or self.port.idRef
            or self.port.unitRef
            or self.port.metaIdRef
        )

    def _port_loss(self, in_model: bool, level: int, version: int) -> str | None:
        """Say why the port of this element cannot be written, if it cannot.

        The one predicate which decides whether a port is written. Both users
        ask it: `create_port`, which reports the reason and writes nothing,
        and `Model._has_comp_content`, which does not count such a port as
        comp content, so that a model whose only comp construct is a port
        which cannot be written declares no comp package and leaves no empty
        comp namespace behind. Both hand over the SBML level and version of
        the document being written, since how a port names its element
        depends on it, see `_port_reference_for`.

        Three things stop a port from being written:

        - the element is written without the `libsbml.Model` its port would
          live in, which is what happens to a key-value pair nested in an
          uncert parameter, an uncert span or a `<comp:sBaseRef>`,
        - the port references the element itself and the element does not
          state the name that reference needs in this document, an id or a
          metaid,
        - the `port=True` shorthand would derive an id for the port which is
          no valid `SId`, which a metaid can be: a metaid is an XML `ID`,
          which allows `.` and `-`, and libsbml answers `setId` with
          `LIBSBML_INVALID_ATTRIBUTE_VALUE` for such a string and leaves the
          required `comp:id` of the port unset (measured with libsbml
          5.21.2, which then reports 1020803 and 1090105).

        Args:
            in_model: whether the element is written with the
                `libsbml.Model`, see `_iter_sbases_with_model`
            level: the SBML level of the document being written
            version: the SBML version of the document being written

        Returns:
            the reason, as a sentence which names the element and says what to
            do about it, `None` if the port can be written
        """
        if self.port is None or self.port is False:
            return None
        what = f"The port of {type(self).__name__} '{self.sid}'"
        if not in_model:
            return (
                f"{what} is not created: the element is nested in an uncert "
                f"parameter, an uncert span or a <comp:sBaseRef> and is "
                f"written without the model its port would live in. Put it on "
                f"an element of the model to give it a port."
            )
        if not self._port_references_self():
            return None
        reference = self._port_reference_for(level, version)
        if self._port_target(reference) is None:
            name = "metaId" if reference == "metaIdRef" else "id"
            because = (
                f" in an SBML L{level}V{version} document"
                if self._port_id_needs_l3v2
                else ""
            )
            return (
                f"{what} is not created: a port references this element by its "
                f"{name}{because}, which it does not state. Give it a {name}, "
                f"or give the port a reference of its own."
            )
        if isinstance(self.port, bool) and not libsbml.SyntaxChecker.isValidSBMLSId(
            self._port_id(reference)
        ):
            return (
                f"{what} is not created: the id '{self._port_id(reference)}' "
                f"derived from the metaid '{self.metaId}' is no valid SBML SId, "
                f"which a port requires. Give the element a metaid which is a "
                f"valid SId, or give the port an id and a reference of its own."
            )
        return None

    def create_port(self, model: libsbml.Model | None) -> libsbml.Port | None:
        """Create the port of the element, if it has one.

        A port which references nothing of its own is made to reference this
        element, by the reference `_port_reference_for` names for the
        document being written: its id, its unit id or its metaid. A port which cannot be written is
        reported here, once, and `Model._has_comp_content` asks the same
        predicate so that it does not declare comp for it, see `_port_loss`.

        Args:
            model: the model the port is created in; `None` for an element
                which is written without one

        Returns:
            the port, `None` if the element has no port or if the port cannot
            be written

        Raises:
            ValueError: if the document does not declare the comp package
        """
        if self.port is None or self.port is False:
            return None
        if model is None:
            # the element is written without a model, which `_port_loss`
            # states as one of its three reasons; the level and version are
            # not looked at on that path
            logger.error("%s", self._port_loss(False, SBML_LEVEL, SBML_VERSION))
            return None
        level: int = model.getLevel()
        version: int = model.getVersion()
        loss = self._port_loss(True, level, version)
        if loss is not None:
            logger.error("%s", loss)
            return None

        # the element is written with a model, states the name its port
        # references it by in a document of this level and version, and that
        # name gives a valid port id
        reference = self._port_reference_for(level, version)
        # the name the port references this element by; `unitRef` names a
        # unit definition by its id like `idRef` does, in the namespace of
        # the unit definitions of the model
        target: str | None = self._port_target(reference)

        p: libsbml.Port | None = None
        if isinstance(self.port, bool):
            if self.port is True:
                # manually create port for this element
                cmodel: libsbml.CompModelPlugin = _comp_plugin(
                    model, f"The port of {type(self).__name__} '{self.sid}'"
                )
                p = cmodel.createPort()
                port_sid = self._port_id(reference)
                p.setId(port_sid)
                # the name says which element the port belongs to, which is
                # its id where it has one, even when the port references it
                # by its metaid
                p.setName(f"Port of {self.sid if self.sid is not None else target}")
                p.setMetaId(port_sid)
                sbo = SBO.PORT.curie
                p.setSBOTerm(sbo)

                # the id, the name, the metaid and the sboTerm of the port are
                # derived and cannot fail: `_port_loss` has checked that the
                # derived id is a valid SId, the name is never empty and the
                # sboTerm is a constant. The reference is the caller's value
                setter = {
                    "unitRef": p.setUnitRef,
                    "metaIdRef": p.setMetaIdRef,
                    "idRef": p.setIdRef,
                }[reference]
                _check_attribute(setter(target), p, reference, target, self)
        else:
            # use the port object
            if self._port_references_self():
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

        # FIXME: check that distrib package is activated
        return [
            uncertainty.create_sbml(obj, model) for uncertainty in self.uncertainties
        ]

    def create_replaced_by(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.ReplacedBy | None:
        """Create the `<comp:replacedBy>` of the element, if it has one.

        comp allows a `<comp:replacedBy>` on every SBML element, but libsbml
        only carries one on an element it attaches a `CompSBasePlugin` to.
        Measured with libsbml 5.21.2, it attaches none to a `<priority>`, to
        a `<distrib:uncertainty>` or to any element of fbc
        (`<fbc:geneProduct>`, `<fbc:objective>`, `<fbc:fluxObjective>`,
        `<fbc:userDefinedConstraint>`,
        `<fbc:userDefinedConstraintComponent>`, `<fbc:keyValuePair>`), so it
        can neither write nor read a replacement there. Those classes do not
        offer `replacedBy`, and neither does `LocalParameter`, on which every
        form of the replacement is invalid; see their class docstrings.

        Args:
            sbase: the libsbml object the replacement is created on
            model: the `libsbml.Model` the element belongs to

        Returns:
            the created replacement, `None` if the element has none
        """
        if not self.replacedBy:
            return None

        return self.replacedBy.create_sbml(sbase, model)

    def create_key_value_pairs(
        self, sbase: libsbml.SBase, model: libsbml.Model | None = None
    ) -> list[libsbml.KeyValuePair] | None:
        """Create the fbc:keyValuePair elements of the element.

        Args:
            sbase: the libsbml object the pairs are created on
            model: the `libsbml.Model` the element belongs to, which the port
                of a pair is created in, see `Model._fill_sbml`; `None` writes
                the pairs without a model, which reports the port of a pair
                which has one

        Returns:
            the created pairs, `None` if the element has none or if the
            document cannot carry them, see `KeyValuePair.create_pairs`
        """
        return KeyValuePair.create_pairs(self.keyValuePairs, sbase, model, self)


class KeyValuePair(Sbase):
    """A key-value pair of fbc version 3, which every element can carry.

    An fbc version 3 `<fbc:keyValuePair>` carries its `key`, `value` and
    `uri` and, like every other `SBase`, an id, a name, a metaid, an sboTerm,
    notes and annotations; all of them are written and the document
    validates. The `id` and the `name` are read back from an SBML **L3V2**
    document and not from an L3V1 one, although libsbml writes them into
    both (measured with libsbml 5.21.2). That is a property of libsbml's
    reader, not of the document: what is written is in the file either way.

    **A document of fbc version 2, or one which declares no fbc at all, gets
    no key-value pair**: libsbml answers every attribute of a pair with
    `LIBSBML_UNEXPECTED_ATTRIBUTE` in fbc version 2 and attaches no fbc
    plugin without the package. Both are reported once for the element which
    carries the pairs, see `KeyValuePair.create_pairs` and
    `_fbc_version_allows`, which answers the same question for an
    `<fbc:userDefinedConstraint>`.

    Neither `uncertainties` nor a nested list of `keyValuePairs` is offered:
    libsbml creates both on the plugins of a `<fbc:keyValuePair>` without an
    error and writes neither into the XML. A `replacedBy` is not offered
    either, since libsbml attaches no `CompSBasePlugin` to the element, see
    `sbmlutils.parser._drop_replaced_by`.

    **A pair which is nested in an `UncertParameter`, an `UncertSpan` or in
    the `sBaseRef` of a comp reference gets no port.** Those three are
    written without the `libsbml.Model` a `<comp:listOfPorts>` lives in, so
    there is nowhere to create it; the port is reported and the document does
    not declare comp for it, see `Sbase._port_loss`. Measured with libsbml
    5.21.2, a pair nested in an uncert parameter cannot be the target of a
    port at all (`Model.getElementBySId` does not answer with it and the
    document fails with 1090105), while one nested in a `<comp:sBaseRef>` is
    resolvable; this package writes a port for neither.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    #: libsbml writes the `fbc:id` of a `<fbc:keyValuePair>` into an SBML
    #: L3V1 document but does not read it back, so a port names a pair by its
    #: metaid there, see `Sbase._port_id_needs_l3v2`
    _port_id_needs_l3v2: ClassVar[bool] = True

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
            port: optional comp port, which names the pair by its `fbc:id` in
                an SBML L3V2 document and by its metaid below one, see
                `Sbase._port_reference_for`; a pair nested in an uncert
                parameter, an uncert span or a `<comp:sBaseRef>` gets none,
                see the class docstring
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

    def __repr__(self) -> str:
        """Get the string representation of the key value pair.

        `Sbase.__str__` of the element which carries the pairs prints the
        list of them, and a list prints its items with `repr`, so without
        this a message which names that element puts the address of the pair
        in front of a user.

        Returns:
            the key and the value of the pair
        """
        return f"KeyValuePair({self.key} = {self.value})"

    @staticmethod
    def create_pairs(
        pairs: list[KeyValuePair] | None,
        sbase: libsbml.SBase,
        model: libsbml.Model | None,
        element: Any,
    ) -> list[libsbml.KeyValuePair] | None:
        """Create the key-value pairs of an element, if the document has fbc v3.

        The one place which decides whether a `<fbc:keyValuePair>` can be
        written at all, asked by `Sbase.create_key_value_pairs` for every
        element, the species reference a `Reaction` writes for each
        `EquationPart` of its equation included, see `_SpeciesReference`.

        A key-value pair is fbc **version 3**. In an fbc version 2 document
        libsbml creates the element and answers `setKey`, `setValue`,
        `setUri`, `setId` and `setName` with `LIBSBML_UNEXPECTED_ATTRIBUTE`
        (measured with libsbml 5.21.2), which wrote an
        `<fbc:listOfKeyValuePairs>` of empty `<fbc:keyValuePair/>` elements;
        and a document which declares no fbc at all has no fbc plugin to
        create one on. Both are reported once for the element, with the
        number of pairs which are lost, and nothing is written.

        The fbc version is read from the plugin of the created libsbml
        object, which is the version of the document being written, rather
        than from the packages of the `Model`, the way `Species._set_charge`
        reads it.

        Args:
            pairs: the key-value pairs of the element, possibly none
            sbase: the libsbml object the pairs are created on
            model: the `libsbml.Model` the element belongs to, which the port
                of a pair is created in; `None` for an element written
                without one
            element: the model element the pairs belong to, named in the
                report

        Returns:
            the created pairs, `None` if the element has none or if the
            document cannot carry them
        """
        if not pairs:
            return None

        sbase_fbc: libsbml.FbcSBasePlugin | None = sbase.getPlugin("fbc")
        if not _fbc_version_allows(
            sbase_fbc, 3, "key-value pair(s)", len(pairs), element
        ):
            return None

        return [pair.create_sbml(sbase, model) for pair in pairs]

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model | None = None
    ) -> libsbml.KeyValuePair:
        """Create the libsbml.KeyValuePair on the given element.

        Written through `KeyValuePair.create_pairs`, which decides whether
        the document can carry a pair at all; on its own this writes an empty
        `<fbc:keyValuePair/>` into an fbc version 2 document and raises on a
        document which declares no fbc.

        Args:
            sbase: the libsbml object the pair is created on
            model: the libsbml.Model the element belongs to, which the port of
                the pair is created in. It has to be handed down rather than
                looked up, and `None` writes the pair without a model, which
                reports a port of it; both are stated in `Model._fill_sbml`

        Returns:
            the created libsbml.KeyValuePair
        """
        sbase_fbc: libsbml.FbcSBasePlugin = sbase.getPlugin("fbc")
        kvp_list: libsbml.ListOfKeyValuePairs = sbase_fbc.getListOfKeyValuePairs()
        # the xmlns of the list is fixed and `setKey` is reached only for a
        # document which `create_pairs` established as fbc version 3
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
