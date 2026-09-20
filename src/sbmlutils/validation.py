"""Helpers for validation and checking of SBML and libsbml operations."""

import logging
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Generic, TypeVar

import libsbml

from sbmlutils.console import console

logger = logging.getLogger(__name__)

#: the key a loss is grouped under; constrained rather than unbounded so that
#: the groups of a scope can be sorted for a deterministic report
K = TypeVar("K", str, tuple[str, ...])
#: what is collected for one key, e.g. a count with an example
V = TypeVar("V")


class ScopedLossCollector(Generic[K, V]):
    """Collect the losses of one document and report them once per group.

    Writing a document can lose the same thing over and over: an annotation
    resource of a collection which cannot be canonicalized, an attribute the
    level and version of the document does not have. Reporting each of them
    on its own buries the one decision which fixes all of them under
    thousands of lines. Inside a scope every loss is collected under a key
    and the detail is logged at debug by the caller; when the outermost scope
    ends, one report per key is emitted, in the order of the keys. Outside a
    scope there is nothing to report at the end, so the caller reports the
    loss directly.

    The collection is held in a `ContextVar` rather than in a module global:
    it belongs to the code which writes one document, and a thread starts
    with a fresh context in which the variable holds its default, so writing
    one document does not collect into the report of another.

    The type variable `K` is the key the losses are grouped under, a string
    or a tuple of them, and `V` is what is collected for one key.
    """

    def __init__(self, name: str, report: Callable[[K, V], None]) -> None:
        """Construct a collector.

        Args:
            name: the name of the `ContextVar`, which is used for debugging
                only and should name the package and the kind of loss
            report: called once per key when the outermost scope ends, in the
                order of the keys
        """
        self._groups: ContextVar[dict[K, V] | None] = ContextVar(name, default=None)
        self._report = report

    @contextmanager
    def scope(self) -> Iterator[None]:
        """Collect the losses recorded inside and report them when it ends.

        A scope inside an active one collects into it and reports nothing of
        its own, so that a document which is created and then annotated from
        a file is still reported once.

        Yields:
            None
        """
        if self._groups.get() is not None:
            # an inner scope reuses the collection, only the outermost reports
            yield
            return

        groups: dict[K, V] = {}
        token = self._groups.set(groups)
        try:
            yield
        finally:
            self._groups.reset(token)
            for key in sorted(groups):
                self._report(key, groups[key])

    def group(self, key: K, create: Callable[[], V]) -> V | None:
        """Get the group of a key inside a scope, `None` outside one.

        Args:
            key: the key the loss is grouped under
            create: builds the group when the key is seen for the first time

        Returns:
            the group to record the loss in, `None` if no scope is active and
            the caller has to report the loss itself
        """
        groups = self._groups.get()
        if groups is None:
            return None
        group = groups.get(key)
        if group is None:
            group = create()
            groups[key] = group
        return group


def check(value: int, message: str) -> bool:
    """Check the libsbml return value and prints message if something happened.

    If 'value' is None, prints an error message constructed using
      'message' and then exits with status code 1. If 'value' is an integer,
      it assumes it is a libSBML return status code. If the code value is
      LIBSBML_OPERATION_SUCCESS, returns without further action; if it is not,
      prints an error message constructed using 'message' along with text from
      libSBML explaining the meaning of the code, and exits with status code 1.
    """
    valid = True
    if value is None:
        logger.error("Error: LibSBML returned a null value trying to <%s>.", message)
        valid = False
    elif isinstance(value, int):
        if value != libsbml.LIBSBML_OPERATION_SUCCESS:
            logger.error("Error encountered trying to '%s'.", message)
            logger.error(
                "LibSBML returned error code %s: %s",
                value,
                libsbml.OperationReturnValue_toString(value).strip(),
            )
            valid = False

    return valid


@dataclass
class ValidationOptions:
    """Options for SBML validator.

    Controls the consistency checks that are performed when
    SBMLDocument.checkConsistency() is called.

    * `general_consistency`: Correctness and consistency of
    specific SBML language constructs. Performing this set of checks is
    highly recommended.  With respect to the SBML specification, these
    concern failures in applying the validation rules numbered 2xxxx in
    the Level 2 Versions 2-4 and Level 3 Versions 1-2 specifications.

    * `ìdentifier_consistency`: Correctness and consistency of
    identifiers used for model entities.  An example of inconsistency
    would be using a species identifier in a reaction rate formula without
    first having declared the species.  With respect to the SBML
    specification, these concern failures in applying the validation rules
    numbered 103xx in the Level 2 Versions 2-4 and Level 3 Versions 1-2
    specifications.

    * `units_consistency`: Consistency of measurement units
    associated with quantities in a model. With respect to the SBML
    specification, these concern failures in applying the validation rules
    numbered 105xx in the Level 2 Versions 2-4 and Level 3 Versions 1-2
    specifications.

    * `mathml_consistency`: Syntax of MathML constructs.  With
    respect to the SBML specification, these concern failures in applying
    the validation rules numbered 102xx in the Level 2 Versions 2-4 and
    Level 3 Versions 1-2 specifications.

    * `sbo_consistency`: Consistency and validity of SBO
    identifiers (if any) used in the model. With respect to the SBML
    specification, these concern failures in applying the validation rules
    numbered 107xx in the Level 2 Versions 2-4 and Level 3 Versions 1-2
    specifications.

    * `overdetermined_model`: Static analysis of whether the
    system of equations implied by a model is mathematically
    overdetermined.  With respect to the SBML specification, this is
    validation rule #10601 in the Level 2 Versions 2-4 and Level 3
    Versions 1-2 specifications.

    * `modeling_practise`: Additional checks for recommended
    good modeling practice. (These are tests performed by libSBML and do
    not have equivalent SBML validation rules.)  By default, all
    validation checks are applied to the model in an SBMLDocument object
    unless SBMLDocument.setConsistencyChecks() is called to indicate that
    only a subset should be applied.  Further, this default (i.e.,
    performing all checks) applies separately to each new SBMLDocument
    object created.  In other words, each time a model is read using
    SBMLReader.readSBML(), SBMLReader.readSBMLFromString(), or the global
    functions readSBML() and readSBMLFromString(), a new SBMLDocument is
    created and for that document, a call to
    SBMLDocument.checkConsistency() will default to applying all possible
    checks. Calling programs must invoke
    SBMLDocument.setConsistencyChecks() for each such new model if they
    wish to change the consistency checks applied.

    * `internal_consistency`: Additional checks that model is consistent XML.

    * `log_errors` Boolean flag to log errors.
    """

    log_errors: bool = True
    internal_consistency: bool = True

    general_consistency: bool = True
    identifier_consistency: bool = True
    mathml_consistency: bool = True
    units_consistency: bool = True
    sbo_consistency: bool = True
    overdetermined_model: bool = True
    modeling_practice: bool = True


class ValidationResult:
    """Results of an SBMLDocument validation."""

    def __init__(
        self,
        errors: list[libsbml.SBMLError] | None = None,
        warnings: list[libsbml.SBMLError] | None = None,
    ):
        """Initialize ValidationResult."""
        if errors is None:
            errors = []
        if warnings is None:
            warnings = []

        self.errors = errors
        self.warnings = warnings

    @property
    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get number of warnings."""
        return len(self.warnings)

    @property
    def all_count(self) -> int:
        """Get number of errors and warnings."""
        return self.error_count + self.warning_count

    @staticmethod
    def from_results(results: Iterable["ValidationResult"]) -> "ValidationResult":
        """Parse from ValidationResult."""
        errors = []
        warnings = []
        for vres in results:
            errors.extend(vres.errors)
            warnings.extend(vres.warnings)
        return ValidationResult(errors=errors, warnings=warnings)

    def log(self) -> None:
        """Log errors and warnings."""
        for k, error in enumerate(self.errors):
            log_sbml_error(error, index=k)
        for k, warning in enumerate(self.warnings):
            log_sbml_error(warning, index=k)

    def is_valid(self) -> bool:
        """Get valid status (valid model), i.e., no errors."""
        return self.error_count == 0

    def is_perfect(self) -> bool:
        """Get perfect status (perfect model), i.e., no errors and warnings."""
        return self.error_count == 0 and self.warning_count == 0


def log_sbml_errors_for_doc(doc: libsbml.SBMLDocument) -> None:
    """Log errors of current SBMLDocument."""
    for k in range(doc.getNumErrors()):
        log_sbml_error(error=doc.getError(k))


def log_sbml_error(error: libsbml.SBMLError, index: int | None = None) -> None:
    """Log SBMLError."""
    msg, severity = error_string(error=error, index=index)
    if severity == libsbml.LIBSBML_SEV_WARNING:
        logger.warning(msg, extra={"markup": True})
    elif severity in [libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL]:
        logger.error(msg, extra={"markup": True})
    else:
        logger.info(msg, extra={"markup": True})


def error_string(error: libsbml.SBMLError, index: int | None = None) -> tuple:
    """Get string representation and severity of SBMLError."""
    package: str = error.getPackage()
    if package == "":
        package = "core"

    severity = error.getSeverity()
    lines = [
        "[black on white]"
        + "E{}: {} ({}, L{}, {})".format(
            index, error.getCategoryAsString(), package, error.getLine(), "code"
        )
        + "[/black on white]",
        f"[{error.getSeverityAsString().lower()}][on black][{error.getSeverityAsString()}] {error.getShortMessage()}[/on black][/{error.getSeverityAsString().lower()}]",
        f"{error.getMessage()}",
    ]
    error_str = "\n".join(lines)
    return error_str, severity


def validate_doc(
    doc: libsbml.SBMLDocument,
    options: ValidationOptions | None = None,
    title: str | None = None,
) -> ValidationResult:
    """Validate SBMLDocument.

    :param doc: SBMLDocument to check
    :param title: identifier or path for validation report
    :param options: validation options and settings.

    :return: ValidationResult
    """
    if options is None:
        options = ValidationOptions()

    if not title:
        title = str(doc)
    if str(title).startswith("/"):
        title = f"file://{title}"

    # set the consistency
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_GENERAL_CONSISTENCY, options.general_consistency
    )
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_IDENTIFIER_CONSISTENCY, options.identifier_consistency
    )
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_MATHML_CONSISTENCY, options.mathml_consistency
    )
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_OVERDETERMINED_MODEL, options.overdetermined_model
    )
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_SBO_CONSISTENCY, options.sbo_consistency
    )
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, options.units_consistency
    )

    # time
    current = time.perf_counter()

    # check the document
    results_internal: ValidationResult
    if options.internal_consistency:
        results_internal = _check_consistency(doc, internal_consistency=True)
    else:
        results_internal = ValidationResult()

    results_not_internal = _check_consistency(
        doc, internal_consistency=False, units_consistency=options.units_consistency
    )

    # sum up
    vresults = ValidationResult.from_results([results_internal, results_not_internal])

    lines = [str(title), f"{'valid':<25}: {str(vresults.is_valid()).upper()}"]
    if not vresults.is_perfect():
        lines += [
            f"{'validation error(s)':<25}: {vresults.error_count}",
            f"{'validation warnings(s)':<25}: {vresults.warning_count}",
        ]
        lines += [
            f"{'    general':<25}: {options.general_consistency}",
            f"{'    identifier':<25}: {options.identifier_consistency}",
            f"{'    mathml':<25}: {options.mathml_consistency}",
            f"{'    overdetermined':<25}: {options.overdetermined_model}",
            f"{'    sbo':<25}: {options.sbo_consistency}",
            f"{'    units':<25}: {options.units_consistency}",
        ]
    lines += [
        f"{'check time (s)':<25}: {time.perf_counter() - current:.3f}",
    ]
    info = "\n".join(lines)

    if vresults.is_perfect():
        style = "success"
    else:
        style = "warning" if vresults.is_valid() else "error"

    # validation report
    console.print()
    console.rule("Validate SBML", style=style)
    console.print(info, style=style)
    console.rule(style=style)
    console.print()

    # individual error and warning report
    if options.log_errors:
        vresults.log()

    return vresults


def _check_consistency(
    doc: libsbml.SBMLDocument,
    internal_consistency: bool = False,
    units_consistency: bool = False,
) -> ValidationResult:
    """Calculate the type of errors.

    :param doc: SBMLDocument
    :param internal_consistency: flag for internal consistency
    :return: ValidationResult
    """
    errors = []
    warnings = []
    if internal_consistency:
        count = doc.checkInternalConsistency()
    else:
        if units_consistency:
            count = doc.checkConsistencyWithStrictUnits()
        else:
            count = doc.checkConsistency()

    if count > 0:
        for i in range(count):
            error = doc.getError(i)
            severity = error.getSeverity()
            if (severity == libsbml.LIBSBML_SEV_ERROR) or (
                severity == libsbml.LIBSBML_SEV_FATAL
            ):
                errors.append(error)
            else:
                warnings.append(error)

    return ValidationResult(errors=errors, warnings=warnings)
