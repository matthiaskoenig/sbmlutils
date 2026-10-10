"""Drive a model with interpolated data, in place or through comp.

The functions of this module implement `Interpolation.drive`,
`Interpolation.drive_comp` and `Interpolation.assignment_rules` of
`sbmlutils.data.interpolation`, which document the behaviour.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import libsbml

from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.utils import all_elements
from sbmlutils.validation import ValidationOptions, check, validate_doc

if TYPE_CHECKING:
    from sbmlutils.data.interpolation import Interpolator

logger = logging.getLogger(__name__)

#: an element a column can drive
type Target = libsbml.Parameter | libsbml.Species | libsbml.Compartment

#: the validation of a driven model, the numbers of a formula carry no units
_OPTIONS = ValidationOptions(units_consistency=False)


def check_sid(sid: str, what: str) -> None:
    """Check that a name used as an id is an SBML id.

    Args:
        sid: the name
        what: what the name is, for the message, e.g. "Column"

    Raises:
        ValueError: if the name is not an SBML id
    """
    if not libsbml.SyntaxChecker.isValidSBMLSId(sid):
        raise ValueError(f"{what} '{sid}' is not an SBML id.")


def resolve_targets(
    interpolators: Sequence[Interpolator],
    xid: str,
    targets: Mapping[str, str] | None,
) -> dict[str, Interpolator]:
    """Map the id of every driven element to the interpolator of its column.

    Args:
        interpolators: the interpolators of the columns
        xid: the name of x
        targets: column to the id it drives, `None` for every column driving
            the element of its own id

    Returns:
        the id of every driven element to the interpolator of its column

    Raises:
        ValueError: for a column which is not in the data or is x, for two
            columns driving one id, for an id which is not an SBML id
    """
    by_column = {interpolator.yid: interpolator for interpolator in interpolators}
    if targets is None:
        targets = {column: column for column in by_column}
    driven: dict[str, Interpolator] = {}
    for column, target in targets.items():
        if column == xid:
            raise ValueError(
                f"'{column}' is x of the interpolation, it drives nothing."
            )
        if column not in by_column:
            raise ValueError(
                f"The data has no column '{column}', its columns are "
                f"{', '.join(repr(c) for c in by_column)}."
            )
        check_sid(target, "Target")
        if target in driven:
            raise ValueError(
                f"'{target}' is driven by two columns, '{driven[target].yid}' and "
                f"'{column}'."
            )
        driven[target] = by_column[column]
    return driven


def read_document(source: Path | str | libsbml.SBMLDocument) -> libsbml.SBMLDocument:
    """The document of a source: a document itself, an SBML string or a path."""
    if isinstance(source, libsbml.SBMLDocument):
        return source
    if isinstance(source, str) and "<sbml" not in source:
        source = Path(source)
    return read_sbml(source)


def _find_target(model: libsbml.Model, sid: str) -> Target:
    """The parameter, species or compartment `sid` of the model.

    Raises:
        ValueError: if the model has no element `sid`, or one of another class
    """
    element: Target | None = (
        model.getParameter(sid) or model.getSpecies(sid) or model.getCompartment(sid)
    )
    if element is not None:
        return element
    other: libsbml.SBase | None = model.getElementBySId(sid)
    if other is None:
        raise ValueError(f"'{sid}' is not an element of the model '{model.getId()}'.")
    raise ValueError(
        f"'{sid}' is a {other.getElementName()}; only a parameter, a species or a "
        f"compartment can be driven."
    )


def _mentions(ast: libsbml.ASTNode | None, sid: str) -> bool:
    """Whether a math names `sid`."""
    if ast is None:
        return False
    if ast.isName() and ast.getName() == sid:
        return True
    return any(_mentions(ast.getChild(k), sid) for k in range(ast.getNumChildren()))


def _determined_by(model: libsbml.Model, sid: str) -> str | None:
    """What of the model determines `sid` already, `None` if nothing does."""
    rule: libsbml.Rule
    for rule in model.getListOfRules():
        if rule.isAlgebraic():
            if _mentions(rule.getMath(), sid):
                return "an algebraic rule"
        elif rule.getVariable() == sid:
            return "an assignment rule" if rule.isAssignment() else "a rate rule"
    event: libsbml.Event
    for event in model.getListOfEvents():
        assignment: libsbml.EventAssignment
        for assignment in event.getListOfEventAssignments():
            if assignment.getVariable() == sid:
                return f"an event assignment of the event '{event.getId()}'"
    return None


def check_model(
    model: libsbml.Model, driven: Mapping[str, Interpolator], xid: str
) -> dict[str, Target]:
    """Check that x exists and the targets can be driven, before anything changes.

    Args:
        model: the model to drive
        driven: the id of every driven element to its interpolator
        xid: the name of x

    Returns:
        the id of every driven element to the element

    Raises:
        ValueError: for a missing x, a target which is x, is missing, is of
            another class, or which the model determines already
    """
    if xid != "time" and model.getElementBySId(xid) is None:
        raise ValueError(
            f"x of the interpolation, '{xid}', is not an element of the model "
            f"'{model.getId()}'; name the first column 'time' or after the quantity "
            f"of the model it is."
        )
    elements: dict[str, Target] = {}
    for target in driven:
        if target == xid:
            raise ValueError(
                f"'{target}' is x of the interpolation, it cannot be driven."
            )
        element = _find_target(model, target)
        determined = _determined_by(model, target)
        if determined is not None:
            raise ValueError(
                f"'{target}' is determined by {determined} of the model already; "
                f"driving it would replace that, remove it first."
            )
        elements[target] = element
    return elements


def write_interpolation(
    model: libsbml.Model, target: str, interpolator: Interpolator
) -> libsbml.AssignmentRule:
    """Write the interpolation of a column as the assignment rule of `target`."""
    rule: libsbml.AssignmentRule = model.createAssignmentRule()
    check(rule.setVariable(target), f"Set the variable '{target}' of an interpolation")
    check(
        rule.setMath(interpolator.ast()),
        f"Set the interpolation of '{interpolator.yid}' on '{target}'",
    )
    return rule


def _make_variable(element: Target) -> None:
    """Make a target non constant, a species a boundary species as well."""
    check(element.setConstant(False), f"Set '{element.getId()}' non constant")
    if isinstance(element, libsbml.Species):
        check(
            element.setBoundaryCondition(True),
            f"Set '{element.getId()}' a boundary species",
        )


def drive(
    source: Path | str | libsbml.SBMLDocument,
    interpolators: Sequence[Interpolator],
    xid: str,
    targets: Mapping[str, str] | None,
    filepath: Path | None,
) -> libsbml.SBMLDocument:
    """Drive the model of a document in place, see `Interpolation.drive`."""
    doc = read_document(source)
    model: libsbml.Model | None = doc.getModel()
    if model is None:
        raise ValueError("The document has no model to drive.")
    driven = resolve_targets(interpolators, xid, targets)
    elements = check_model(model, driven, xid)
    for target, interpolator in driven.items():
        if model.getInitialAssignmentBySymbol(target) is not None:
            model.removeInitialAssignment(target)
            logger.info(
                "The initial assignment of '%s' is removed, the interpolation of "
                "'%s' determines it.",
                target,
                interpolator.yid,
            )
        _make_variable(elements[target])
        write_interpolation(model, target, interpolator)
    validate_doc(doc, options=_OPTIONS)
    if filepath is not None:
        write_sbml(doc, filepath=Path(filepath))
    return doc


#: the units of a model which the top model of a comp document takes over
_MODEL_UNITS = (
    "TimeUnits",
    "SubstanceUnits",
    "ExtentUnits",
    "VolumeUnits",
    "AreaUnits",
    "LengthUnits",
)


def _source_path(source: Path | str | libsbml.SBMLDocument) -> Path | None:
    """The file of a source, `None` for a document or an SBML string."""
    if isinstance(source, Path):
        return source.resolve()
    if isinstance(source, str) and "<sbml" not in source:
        return Path(source).resolve()
    return None


def _is_hierarchical(doc: libsbml.SBMLDocument) -> bool:
    """Whether the document has comp content: model definitions or submodels."""
    doc_plugin: libsbml.CompSBMLDocumentPlugin | None = doc.getPlugin("comp")
    model_plugin: libsbml.CompModelPlugin | None = doc.getModel().getPlugin("comp")
    definitions = (
        0
        if doc_plugin is None
        else doc_plugin.getNumModelDefinitions()
        + doc_plugin.getNumExternalModelDefinitions()
    )
    submodels = 0 if model_plugin is None else model_plugin.getNumSubmodels()
    return definitions + submodels > 0


def _deletions(model: libsbml.Model, driven: Mapping[str, Interpolator]) -> list[str]:
    """The metaids of the initial assignments of the targets, to delete.

    Raises:
        ValueError: for an initial assignment without a metaid
    """
    metaids: list[str] = []
    for target in driven:
        assignment: libsbml.InitialAssignment | None = (
            model.getInitialAssignmentBySymbol(target)
        )
        if assignment is None:
            continue
        if not assignment.isSetMetaId():
            raise ValueError(
                f"'{target}' has an initial assignment without a metaid, which a "
                f"comp model cannot remove in the original; give it a metaid or "
                f"drive the model in place with `drive`."
            )
        metaids.append(assignment.getMetaId())
    return metaids


def _comp_document(original: libsbml.SBMLDocument, embed: bool) -> libsbml.SBMLDocument:
    """An empty comp document, with the packages of the original if it embeds it."""
    version = 2 if original.getVersion() == 2 else 1
    doc = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, version, "comp", 1))
    check(doc.setPackageRequired("comp", True), "Set comp required")
    if embed:
        for k in range(original.getNumPlugins()):
            plugin: libsbml.SBasePlugin = original.getPlugin(k)
            name = plugin.getPackageName()
            if name == "comp":
                continue
            check(
                doc.enablePackage(plugin.getURI(), plugin.getPrefix(), True),
                f"Enable the package '{name}'",
            )
            check(
                doc.setPackageRequired(name, original.getPackageRequired(name)),
                f"Set the package '{name}' required",
            )
    return doc


def _reference(model: libsbml.Model, sid: str) -> tuple[str, str]:
    """How the comp model names an element of the original: its port, else its id."""
    plugin: libsbml.CompModelPlugin | None = model.getPlugin("comp")
    if plugin is not None:
        port: libsbml.Port
        for port in plugin.getListOfPorts():
            if port.isSetIdRef() and port.getIdRef() == sid:
                return "portRef", port.getId()
    return "idRef", sid


def _set_reference(
    sbase_ref: libsbml.Replacing, submodel: str, reference: tuple[str, str]
) -> None:
    """Point a replacement at an element of the submodel."""
    check(sbase_ref.setSubmodelRef(submodel), f"Set the submodel '{submodel}'")
    kind, value = reference
    status = (
        sbase_ref.setPortRef(value) if kind == "portRef" else sbase_ref.setIdRef(value)
    )
    check(status, f"Set the {kind} '{value}'")


def _placeholder(top: libsbml.Model, element: Target) -> Target:
    """An element of the top model of the class of `element`, with its units."""
    sid = element.getId()
    placeholder: Target
    if isinstance(element, libsbml.Species):
        species: libsbml.Species = top.createSpecies()
        check(species.setCompartment(element.getCompartment()), "Set compartment")
        check(
            species.setHasOnlySubstanceUnits(element.getHasOnlySubstanceUnits()),
            "Set hasOnlySubstanceUnits",
        )
        check(species.setBoundaryCondition(True), "Set boundaryCondition")
        if element.isSetSubstanceUnits():
            check(species.setSubstanceUnits(element.getSubstanceUnits()), "Set units")
        placeholder = species
    elif isinstance(element, libsbml.Compartment):
        compartment: libsbml.Compartment = top.createCompartment()
        if element.isSetSpatialDimensions():
            check(
                compartment.setSpatialDimensions(
                    element.getSpatialDimensionsAsDouble()
                ),
                "Set spatialDimensions",
            )
        if element.isSetSize():
            check(compartment.setSize(element.getSize()), "Set size")
        if element.isSetUnits():
            check(compartment.setUnits(element.getUnits()), "Set units")
        placeholder = compartment
    else:
        parameter: libsbml.Parameter = top.createParameter()
        if element.isSetUnits():
            check(parameter.setUnits(element.getUnits()), "Set units")
        placeholder = parameter
    check(placeholder.setId(sid), f"Set the id '{sid}'")
    check(placeholder.setConstant(False), f"Set '{sid}' non constant")
    return placeholder


def _copy_units(top: libsbml.Model, model: libsbml.Model) -> None:
    """Take over the model units and the unit definitions the top model uses."""
    used: set[str] = set()
    for name in _MODEL_UNITS:
        if getattr(model, f"isSet{name}")():
            unit: str = getattr(model, f"get{name}")()
            check(getattr(top, f"set{name}")(unit), f"Set the model {name}")
            used.add(unit)
    for parameter in top.getListOfParameters():
        used.add(parameter.getUnits())
    for species in top.getListOfSpecies():
        used.add(species.getSubstanceUnits())
    for compartment in top.getListOfCompartments():
        used.add(compartment.getUnits())
    for uid in sorted(used - {""}):
        definition: libsbml.UnitDefinition | None = model.getUnitDefinition(uid)
        if definition is not None:
            check(top.addUnitDefinition(definition), f"Copy the unit '{uid}'")


def _free_id(sid: str, taken: set[str]) -> str:
    """`sid`, or `sid_1`, `sid_2`, ... if it is taken."""
    candidate = sid
    k = 0
    while candidate in taken:
        k += 1
        candidate = f"{sid}_{k}"
    return candidate


def _embed(
    doc_plugin: libsbml.CompSBMLDocumentPlugin, model: libsbml.Model, mid: str
) -> None:
    """Copy the original into the comp document as the model definition `mid`.

    The model definition is created empty, with the plugins of the packages
    of the document, and filled by `Model.appendFrom`, which copies the
    content of the model and of its packages; its attributes and its ports
    are copied here. The copy constructor `libsbml.ModelDefinition(model)`
    crashes the validation for a model without the comp plugin.

    `fbc:strict` is not copied, `appendFrom` does not copy it either:
    libsbml 5.21.2 writes it twice on a `<comp:modelDefinition>`, into a file
    which cannot be read back, see `ModelDefinition` of `sbmlutils.factory`.
    A model definition with fbc content therefore carries the libsbml error
    2020209, as one written by the factory does.
    """
    definition: libsbml.ModelDefinition = doc_plugin.createModelDefinition()
    check(definition.setId(mid), f"Set the id of the model definition '{mid}'")
    check(definition.appendFrom(model), "Copy the original into the definition")
    for name in ("Name", "MetaId", "SBOTerm", "ConversionFactor", *_MODEL_UNITS):
        if getattr(model, f"isSet{name}")():
            value = getattr(model, f"get{name}")()
            check(getattr(definition, f"set{name}")(value), f"Copy the model {name}")
    if model.isSetNotes():
        check(definition.setNotes(model.getNotes()), "Copy the notes")
    if model.isSetAnnotation():
        check(definition.setAnnotation(model.getAnnotation()), "Copy the annotation")
    source_comp: libsbml.CompModelPlugin | None = model.getPlugin("comp")
    if source_comp is not None:
        target_comp: libsbml.CompModelPlugin = definition.getPlugin("comp")
        port: libsbml.Port
        for port in source_comp.getListOfPorts():
            check(target_comp.addPort(port), f"Copy the port '{port.getId()}'")


def drive_comp(
    source: Path | str | libsbml.SBMLDocument,
    interpolators: Sequence[Interpolator],
    xid: str,
    targets: Mapping[str, str] | None,
    filepath: Path | None,
    embed: bool,
) -> libsbml.SBMLDocument:
    """Drive a model through a comp model, see `Interpolation.drive_comp`."""
    original = read_document(source)
    if original.getLevel() != 3:
        raise ValueError(
            f"The model is SBML Level {original.getLevel()} Version "
            f"{original.getVersion()}; the comp package is SBML Level 3, convert the "
            f"model to Level 3 first or drive it in place with `drive`."
        )
    model: libsbml.Model | None = original.getModel()
    if model is None:
        raise ValueError("The document has no model to drive.")
    source_path = _source_path(source)
    if not embed and source_path is None:
        raise ValueError(
            "An SBML string or a document is no file a comp model can reference; "
            "write it to a file or pass embed=True."
        )
    if embed and _is_hierarchical(original):
        raise ValueError(
            "A hierarchical model (with submodels or model definitions) cannot be "
            "embedded; reference it from its file, embed=False."
        )
    driven = resolve_targets(interpolators, xid, targets)
    elements = check_model(model, driven, xid)
    deletions = _deletions(model, driven)

    # the placeholders of the top model take the ids of the original, the
    # submodel and the model definition are named after the original, so a
    # name for an original without an id must be none of its ids
    taken: set[str] = {
        element.getId() for element in all_elements(model) if element.isSetId()
    }
    mid = model.getId() or _free_id("model", taken)
    doc = _comp_document(original, embed)
    doc_plugin: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    if embed:
        _embed(doc_plugin, model, mid)
    else:
        if source_path is None:
            raise RuntimeError("A referenced original has a file.")
        emd: libsbml.ExternalModelDefinition = (
            doc_plugin.createExternalModelDefinition()
        )
        if filepath is not None:
            out = Path(filepath).resolve()
            try:
                reference = Path(os.path.relpath(source_path, out.parent)).as_posix()
            except ValueError:
                # on Windows a file on another drive has no relative path
                reference = source_path.as_posix()
            # libsbml resolves `comp:source` against the location of the document
            doc.setLocationURI(f"file:{out}")
        else:
            reference = source_path.as_posix()
        check(emd.setId(mid), f"Set the id '{mid}'")
        check(emd.setSource(reference), f"Set the source '{reference}'")
        if model.isSetId():
            check(emd.setModelRef(model.getId()), "Set the modelRef")

    top: libsbml.Model = doc.createModel()
    top_id = _free_id(f"{mid}_driven", taken)
    check(top.setId(top_id), f"Set the id of the top model '{top_id}'")
    top_plugin: libsbml.CompModelPlugin = top.getPlugin("comp")
    submodel: libsbml.Submodel = top_plugin.createSubmodel()
    check(submodel.setId(mid), f"Set the submodel '{mid}'")
    check(submodel.setModelRef(mid), f"Set the modelRef '{mid}'")
    for metaid in deletions:
        deletion: libsbml.Deletion = submodel.createDeletion()
        check(
            deletion.setMetaIdRef(metaid), f"Delete the initial assignment '{metaid}'"
        )

    # the targets replace the elements of the original, compartments first,
    # so that a driven compartment is the compartment of a driven species
    for target in sorted(
        driven, key=lambda t: not isinstance(elements[t], libsbml.Compartment)
    ):
        placeholder = _placeholder(top, elements[target])
        replaced: libsbml.ReplacedElement = placeholder.getPlugin(
            "comp"
        ).createReplacedElement()
        _set_reference(replaced, mid, _reference(model, target))
        write_interpolation(top, target, driven[target])
    # the compartment of a driven species, and x, read the original
    readers = [species.getCompartment() for species in top.getListOfSpecies()]
    if xid != "time":
        readers.append(xid)
    for sid in readers:
        if top.getElementBySId(sid) is not None:
            continue
        compartment: libsbml.Compartment | None = model.getCompartment(sid)
        reader: Target
        if compartment is not None:
            reader = _placeholder(top, compartment)
            check(reader.setConstant(compartment.getConstant()), "Set constant")
        else:
            reader = top.createParameter()
            check(reader.setId(sid), f"Set the id '{sid}'")
            check(reader.setConstant(False), f"Set '{sid}' non constant")
        replaced_by: libsbml.ReplacedBy = reader.getPlugin("comp").createReplacedBy()
        _set_reference(replaced_by, mid, _reference(model, sid))
    _copy_units(top, model)

    validate_doc(doc, options=_OPTIONS)
    if filepath is not None:
        write_sbml(doc, filepath=Path(filepath))
    return doc
