"""Drive a model with interpolated data, in place or through comp.

The functions of this module implement `Interpolation.drive`,
`Interpolation.drive_comp` and `Interpolation.assignment_rules` of
`sbmlutils.data.interpolation`, which document the behaviour.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import libsbml

from sbmlutils.io.sbml import read_sbml, write_sbml
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
