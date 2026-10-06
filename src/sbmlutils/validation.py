"""Helpers for validation and checking of SBML and libsbml operations."""

import logging
import re
import time
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from urllib.parse import quote

import libsbml

logger = logging.getLogger(__name__)


# `K` is the key a loss is grouped under, constrained rather than unbounded so
# that the groups of a scope can be sorted for a deterministic report; `V` is
# what is collected for one key, e.g. a count with an example
class ScopedLossCollector[K: (str, tuple[str, ...]), V]:
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
            # a group which fails to report must neither hide the remaining
            # groups nor replace the exception of the body
            for key in sorted(groups):
                try:
                    self._report(key, groups[key])
                except Exception:
                    logger.exception("Failed to report the losses of '%s'.", key)

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


def check(value: int | None, message: str) -> bool:
    """Check the libsbml return value and log an error if something happened.

    Args:
        value: the return value of a libsbml call. `None` means libsbml returned
            a null value and is logged as an error. An integer is a libsbml
            return status code: `LIBSBML_OPERATION_SUCCESS` is fine, any other
            code is logged with the text libsbml has for it.
        message: what was attempted, used to construct the error message

    Returns:
        True if the call succeeded, False if an error was logged. The function
        neither raises nor exits, the caller decides what a failure means.
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


@dataclass(frozen=True)
class SBMLErrorInfo:
    """Immutable snapshot of a libsbml `SBMLError`.

    A libsbml error belongs to the error log of its document and is gone with
    the document, so a `ValidationResult` which holds the libsbml objects
    returns garbage once the validated document is freed. The snapshot holds
    plain values and offers the getters of `libsbml.SBMLError` which are used
    on results, so code written against the libsbml object keeps working.
    """

    error_id: int
    severity: int
    severity_string: str
    category: int
    category_string: str
    line: int
    column: int
    message: str
    short_message: str
    package: str

    @staticmethod
    def from_error(error: libsbml.SBMLError) -> "SBMLErrorInfo":
        """Take a snapshot of a libsbml error."""
        return SBMLErrorInfo(
            error_id=error.getErrorId(),
            severity=error.getSeverity(),
            severity_string=error.getSeverityAsString(),
            category=error.getCategory(),
            category_string=error.getCategoryAsString(),
            line=error.getLine(),
            column=error.getColumn(),
            message=error.getMessage(),
            short_message=error.getShortMessage(),
            package=error.getPackage(),
        )

    def getErrorId(self) -> int:
        """Get the error id."""
        return self.error_id

    def getSeverity(self) -> int:
        """Get the severity code."""
        return self.severity

    def getSeverityAsString(self) -> str:
        """Get the severity as string."""
        return self.severity_string

    def getCategory(self) -> int:
        """Get the category code."""
        return self.category

    def getCategoryAsString(self) -> str:
        """Get the category as string."""
        return self.category_string

    def getLine(self) -> int:
        """Get the line."""
        return self.line

    def getColumn(self) -> int:
        """Get the column."""
        return self.column

    def getMessage(self) -> str:
        """Get the message."""
        return self.message

    def getShortMessage(self) -> str:
        """Get the short message."""
        return self.short_message

    def getPackage(self) -> str:
        """Get the package."""
        return self.package

    def isInfo(self) -> bool:
        """Check if the severity is informational (libsbml `isInfo`)."""
        return self.severity in (
            libsbml.LIBSBML_SEV_INFO,
            libsbml.LIBSBML_SEV_NOT_APPLICABLE,
        )

    def isWarning(self) -> bool:
        """Check if the severity is warning (libsbml `isWarning`)."""
        return self.severity == libsbml.LIBSBML_SEV_WARNING

    def isError(self) -> bool:
        """Check if the severity is error or fatal (libsbml `isError`)."""
        return self.severity in (libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL)

    def isFatal(self) -> bool:
        """Check if the severity is fatal (libsbml `isFatal`)."""
        return self.severity == libsbml.LIBSBML_SEV_FATAL


class ValidationResult:
    """Results of an SBMLDocument validation.

    The errors and warnings are snapshots, they stay valid when the validated
    document is freed.
    """

    def __init__(
        self,
        errors: list[SBMLErrorInfo] | None = None,
        warnings: list[SBMLErrorInfo] | None = None,
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


def log_sbml_error(
    error: libsbml.SBMLError | SBMLErrorInfo, index: int | None = None
) -> None:
    """Log SBMLError."""
    msg, severity = error_string(error=error, index=index)
    if severity == libsbml.LIBSBML_SEV_WARNING:
        logger.warning(msg, extra={"markup": True})
    elif severity in [libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL]:
        logger.error(msg, extra={"markup": True})
    else:
        logger.info(msg, extra={"markup": True})


def error_string(
    error: libsbml.SBMLError | SBMLErrorInfo, index: int | None = None
) -> tuple:
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


_WINDOWS_PATH = re.compile(r"^[A-Za-z]:[\\/]")


def _file_uri(title: str) -> str:
    """Get the file URI of a title which is an absolute path.

    Posix and windows paths are converted, everything else (URLs, the string
    representation of a document, relative paths) is returned unchanged.

    Args:
        title: identifier or path of a validation report

    Returns:
        the file URI for an absolute path, else the title.
    """
    if _WINDOWS_PATH.match(title):
        return "file:///" + quote(title.replace("\\", "/"), safe="/:")
    if title.startswith("/"):
        return "file://" + quote(title, safe="/")
    return title


def validate_doc(
    doc: libsbml.SBMLDocument,
    options: ValidationOptions | None = None,
    title: str | None = None,
) -> ValidationResult:
    """Validate SBMLDocument.

    The error log of the document is cleared and restored during the validation,
    so an `SBMLError` proxy obtained from `doc.getError()` before the call is
    invalid afterwards; take a new one from the document (or use the snapshots
    of the result).

    :param doc: SBMLDocument to check
    :param title: identifier or path for validation report
    :param options: validation options and settings.

    :return: ValidationResult
    """
    if options is None:
        options = ValidationOptions()

    if not title:
        title = str(doc)
    title = _file_uri(str(title))

    # the checks append to the error log of the document, validating leaves the
    # log as it found it: the entries are copied here and restored below (a
    # clone of the document is not an option, it is checked differently)
    results_read = _errors_to_result(doc, 0)
    saved_log = libsbml.SBMLErrorLog(doc.getErrorLog())

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

    # the errors in the log of `doc`, i.e. the ones of reading it, are part of
    # the result exactly once; every check below reports only what it added
    # check the document
    try:
        results_internal: ValidationResult
        if options.internal_consistency:
            results_internal = _check_consistency(doc, internal_consistency=True)
        else:
            results_internal = ValidationResult()

        results_not_internal = _check_consistency(
            doc, internal_consistency=False, units_consistency=options.units_consistency
        )
    finally:
        doc.getErrorLog().clearLog()
        for i in range(saved_log.getNumErrors()):
            doc.getErrorLog().add(saved_log.getError(i))

    # sum up
    vresults = ValidationResult.from_results(
        [results_read, results_internal, results_not_internal]
    )

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
        level = logging.INFO
    else:
        level = logging.WARNING if vresults.is_valid() else logging.ERROR

    # validation report
    logger.log(level, "Validate SBML\n%s", info)

    # individual error and warning report
    if options.log_errors:
        vresults.log()

    return vresults


def _errors_to_result(doc: libsbml.SBMLDocument, start: int) -> ValidationResult:
    """Split the entries of the error log from `start` on into errors and warnings.

    Args:
        doc: SBMLDocument
        start: index of the first entry to read

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []
    for i in range(start, doc.getNumErrors()):
        error = SBMLErrorInfo.from_error(doc.getError(i))
        severity = error.getSeverity()
        if severity in (libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL):
            errors.append(error)
        else:
            warnings.append(error)
    return ValidationResult(errors=errors, warnings=warnings)


def _check_consistency(
    doc: libsbml.SBMLDocument,
    internal_consistency: bool = False,
    units_consistency: bool = False,
) -> ValidationResult:
    """Run one consistency check and get the errors it found.

    libsbml appends the findings of a check to the error log of the document,
    which already holds the read errors and the findings of earlier checks.
    Only the entries added by this check are returned, the return value of the
    check (the number of failures) is not an index into the log.

    Args:
        doc: SBMLDocument
        internal_consistency: flag for internal consistency
        units_consistency: check units strictly

    Returns:
        ValidationResult
    """
    n_before = doc.getNumErrors()
    if internal_consistency:
        doc.checkInternalConsistency()
    elif units_consistency:
        doc.checkConsistencyWithStrictUnits()
    else:
        doc.checkConsistency()

    return _errors_to_result(doc, n_before)
