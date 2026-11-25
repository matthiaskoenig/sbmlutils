"""Helpers for validation and checking of SBML and libsbml operations."""

import logging
import re
import time
from collections import Counter
from collections.abc import Callable, Generator, Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Literal
from urllib.parse import quote

import libsbml
from rich.markup import escape

if TYPE_CHECKING:
    from rich.table import Table

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
    def scope(self) -> Generator[None]:
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


@dataclass(frozen=True)
class ConstructionDiagnostic:
    """One grouped construction finding, without references to native objects."""

    code: str
    severity: Literal["info", "warning", "error"]
    message: str
    count: int = 1
    example: str | None = None


class ConstructionError(ValueError):
    """Strict construction rejected reported losses or undeclared targets."""

    def __init__(self, diagnostics: tuple[ConstructionDiagnostic, ...]) -> None:
        """Retain an immutable snapshot of all construction findings."""
        self.diagnostics = diagnostics
        super().__init__(
            "Strict construction failed: "
            + "; ".join(
                f"{d.message} (count={d.count}, example={d.example!r})"
                for d in diagnostics
                if d.severity != "info"
            )
        )


class PreservationError(ValueError):
    """A parse or write would discard reported source content."""

    def __init__(self, diagnostics: tuple[ConstructionDiagnostic, ...]) -> None:
        """Retain an immutable snapshot of the known preservation losses."""
        self.diagnostics = diagnostics
        super().__init__(
            "Round-trip preservation failed: "
            + "; ".join(
                f"{d.message} (count={d.count}, example={d.example!r})"
                for d in diagnostics
            )
        )


@dataclass
class _ConstructionScope:
    strict: bool
    groups: dict[tuple[str, str], ConstructionDiagnostic]

    @property
    def diagnostics(self) -> tuple[ConstructionDiagnostic, ...]:
        return tuple(self.groups.values())


_construction_scope: ContextVar[_ConstructionScope | None] = ContextVar(
    "sbmlutils_construction_scope", default=None
)


@contextmanager
def collect_construction_diagnostics(
    *, strict: bool = False
) -> Generator[_ConstructionScope]:
    """Collect grouped findings in an isolated context, including nested calls.

    The yielded scope exposes a ``diagnostics`` snapshot. Strictness controls
    implicit parameter creation; callers decide when to raise ConstructionError.
    """
    scope = _ConstructionScope(strict=strict, groups={})
    token = _construction_scope.set(scope)
    try:
        yield scope
    finally:
        _construction_scope.reset(token)


def record_construction_diagnostic(
    code: str,
    message: str,
    *,
    severity: Literal["info", "warning", "error"] = "warning",
    example: str | None = None,
    count: int = 1,
) -> None:
    """Record a finding if collection is active, grouping by code and cause."""
    scope = _construction_scope.get()
    if scope is None:
        return
    key = (code, message)
    previous = scope.groups.get(key)
    if previous is None:
        scope.groups[key] = ConstructionDiagnostic(
            code, severity, message, count, example
        )
    else:
        scope.groups[key] = replace(previous, count=previous.count + count)


def allow_implicit_parameter(symbol: str, element: str) -> bool:
    """Record an undeclared assignment target and apply the authoring policy."""
    scope = _construction_scope.get()
    strict = scope is not None and scope.strict
    record_construction_diagnostic(
        "implicit_parameter",
        f"{element} targets an undeclared symbol; declare its parameter explicitly.",
        severity="error" if strict else "warning",
        example=symbol,
    )
    return not strict


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

    if not valid:
        record_construction_diagnostic(
            "libsbml_operation_failed",
            f"libSBML operation failed (status {value}).",
            severity="error",
            example=message,
        )
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

    * `comp_flat_model`: Flatten a comp document and check the flat model as
    well, as libsbml's validation of the comp package does by default. A
    flat model which is not valid is reported as `CompFlatModelNotValid`
    followed by its errors. Turn it off when the flat model is validated
    separately, e.g. after `flatten_sbml`; it has no effect on a document
    without comp.

    * `log_errors` Boolean flag to log errors.

    * `max_logged_per_error`: how many findings with the same error id are
    logged one by one, `None` logs all of them. A large model easily repeats
    one finding thousands of times, e.g. a unit warning on every reaction;
    the remaining ones are summarized in one line. The `ValidationResult`
    always holds every finding.
    """

    log_errors: bool = True
    max_logged_per_error: int | None = 10
    internal_consistency: bool = True

    general_consistency: bool = True
    identifier_consistency: bool = True
    mathml_consistency: bool = True
    units_consistency: bool = True
    sbo_consistency: bool = True
    overdetermined_model: bool = True
    modeling_practice: bool = True
    comp_flat_model: bool = True

    @classmethod
    def fast(cls, *, log_errors: bool = True) -> "ValidationOptions":
        """Check structure and identifiers without expensive unit analysis.

        Use the default options for comprehensive validation before sharing
        or simulating a model. This preset leaves all other checks enabled.
        """
        return cls(units_consistency=False, log_errors=log_errors)


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


@dataclass
class ValidationGroup:
    """The findings of a validation which share one error id.

    Attributes:
        error_id: the libsbml error id
        severity: the libsbml severity code
        severity_string: the severity as string
        package: the SBML package, `core` for SBML core
        category: the category of the finding
        short_message: the short message of the finding
        count: how many findings have the error id
        lines: the line of every finding, 0 if libsbml has none
    """

    error_id: int
    severity: int
    severity_string: str
    package: str
    category: str
    short_message: str
    count: int
    lines: list[int]


#: the log level of a libsbml severity
_LOG_LEVELS: dict[int, int] = {
    libsbml.LIBSBML_SEV_INFO: logging.INFO,
    libsbml.LIBSBML_SEV_WARNING: logging.WARNING,
    libsbml.LIBSBML_SEV_ERROR: logging.ERROR,
    libsbml.LIBSBML_SEV_FATAL: logging.ERROR,
}

#: the rich style of a libsbml severity, see `sbmlutils.console`
_SEVERITY_STYLES: dict[int, str] = {
    libsbml.LIBSBML_SEV_INFO: "blue",
    libsbml.LIBSBML_SEV_WARNING: "orange3",
    libsbml.LIBSBML_SEV_ERROR: "red",
    libsbml.LIBSBML_SEV_FATAL: "bold red",
}


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

    def log(self, max_per_error: int | None = None) -> None:
        """Log errors and warnings.

        Args:
            max_per_error: how many findings with the same error id are logged
                one by one, `None` logs all of them; the rest of every error id
                is summarized in one line
        """
        logged: Counter[int] = Counter()
        for findings in (self.errors, self.warnings):
            for k, error in enumerate(findings):
                error_id = error.getErrorId()
                logged[error_id] += 1
                if max_per_error is None or logged[error_id] <= max_per_error:
                    log_sbml_error(error, index=k)

        if max_per_error is None:
            return
        for group in self.groups():
            skipped = group.count - max_per_error
            if skipped > 0:
                logger.log(
                    _LOG_LEVELS.get(group.severity, logging.INFO),
                    "%s further finding(s) %s (%s) are not logged, "
                    "they are in the ValidationResult.",
                    skipped,
                    group.error_id,
                    group.short_message,
                )

    def groups(self) -> list["ValidationGroup"]:
        """Group the findings by error id, the most severe and frequent first.

        Returns:
            one group per error id, errors before warnings, then by count
        """
        groups: dict[int, ValidationGroup] = {}
        for error in [*self.errors, *self.warnings]:
            error_id = error.getErrorId()
            group = groups.get(error_id)
            if group is None:
                groups[error_id] = ValidationGroup(
                    error_id=error_id,
                    severity=error.getSeverity(),
                    severity_string=error.getSeverityAsString(),
                    package=error.getPackage() or "core",
                    category=error.getCategoryAsString(),
                    short_message=error.getShortMessage(),
                    count=1,
                    lines=[error.getLine()],
                )
            else:
                group.count += 1
                group.lines.append(error.getLine())
        # ranked by the log level of the severity: libsbml numbers its
        # severities, but not in the order of how severe they are
        return sorted(
            groups.values(),
            key=lambda g: (
                -_LOG_LEVELS.get(g.severity, logging.INFO),
                -g.count,
                g.error_id,
            ),
        )

    def __repr__(self) -> str:
        """Get the counts of the result."""
        return (
            f"ValidationResult(errors={self.error_count}, "
            f"warnings={self.warning_count})"
        )

    def __rich__(self) -> "Table":
        """Render the findings grouped by error id as a rich table.

        `console.print(result)` gives an overview of a validation, also of a
        large model which repeats one finding thousands of times.

        Returns:
            the table
        """
        from rich.table import Table

        if self.is_perfect():
            title = "[green]valid[/green], no errors or warnings"
        else:
            status = "[green]valid[/green]" if self.is_valid() else "[red]invalid[/red]"
            title = (
                f"{status}, {self.error_count} error(s), "
                f"{self.warning_count} warning(s)"
            )
        table = Table(title=title, title_justify="left", show_lines=False)
        table.add_column("severity", no_wrap=True)
        table.add_column("id", justify="right", no_wrap=True)
        table.add_column("package", no_wrap=True)
        table.add_column("count", justify="right", no_wrap=True)
        table.add_column("message", ratio=3)
        table.add_column("lines", ratio=1)
        for group in self.groups():
            style = _SEVERITY_STYLES.get(group.severity, "")
            lines = sorted({line for line in group.lines if line > 0})
            lines_str = ", ".join(str(line) for line in lines[:5])
            if len(lines) > 5:
                lines_str += ", ..."
            table.add_row(
                f"[{style}]{group.severity_string}[/{style}]"
                if style
                else group.severity_string,
                str(group.error_id),
                group.package,
                str(group.count),
                escape(group.short_message),
                lines_str,
            )
        return table

    def is_valid(self) -> bool:
        """Get valid status (valid model), i.e., no errors."""
        return self.error_count == 0

    def is_perfect(self) -> bool:
        """Get perfect status (perfect model), i.e., no errors and warnings."""
        return self.error_count == 0 and self.warning_count == 0


class SBMLValidationError(ValueError):
    """Validation failed, with the immutable result available to the caller."""

    def __init__(self, result: ValidationResult, message: str):
        """Keep the findings available without requiring another validation."""
        super().__init__(message)
        self.result = result


def log_sbml_errors_for_doc(doc: libsbml.SBMLDocument) -> None:
    """Log errors of current SBMLDocument."""
    for k in range(doc.getNumErrors()):
        log_sbml_error(error=doc.getError(k))


def log_sbml_error(
    error: libsbml.SBMLError | SBMLErrorInfo, index: int | None = None
) -> None:
    """Log SBMLError at the level of its severity.

    The message is plain text, so that it reads the same on every handler; a
    rich handler colors it by its level.
    """
    msg, severity = error_string(error=error, index=index)
    logger.log(_LOG_LEVELS.get(severity, logging.INFO), "%s", msg)


def error_string(
    error: libsbml.SBMLError | SBMLErrorInfo, index: int | None = None
) -> tuple[str, int]:
    """Get string representation and severity of SBMLError.

    The first line names the finding: its index in the result, the severity,
    the error id, the category, the package and the position in the file.
    The short message and the explanation of the specification follow.

    Returns:
        the message and the libsbml severity code
    """
    package: str = error.getPackage() or "core"
    severity: int = error.getSeverity()
    position = f"line {error.getLine()}"
    if error.getColumn():
        position += f", column {error.getColumn()}"
    prefix = f"E{index} " if index is not None else ""
    lines = [
        f"{prefix}[{error.getSeverityAsString()}] {error.getErrorId()} "
        f"{error.getCategoryAsString()} ({package}, {position})",
        error.getShortMessage().strip(),
        error.getMessage().strip(),
    ]
    return "\n".join(line for line in lines if line), severity


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


#: how many error ids the summary of a validation report lists
_REPORTED_GROUPS: int = 10


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
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_MODELING_PRACTICE, options.modeling_practice
    )

    # libsbml copies the setting into the documents it validates on the way,
    # the copies of the model definitions and the flat model
    comp_doc: libsbml.CompSBMLDocumentPlugin | None = doc.getPlugin("comp")
    override_flattening = None
    if comp_doc is not None:
        override_flattening = comp_doc.getOverrideCompFlattening()
        comp_doc.setOverrideCompFlattening(not options.comp_flat_model)

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
        if comp_doc is not None:
            comp_doc.setOverrideCompFlattening(override_flattening)

    # sum up
    vresults = ValidationResult.from_results(
        [results_read, results_internal, results_not_internal]
    )

    lines = [str(title), f"{'valid':<25}: {str(vresults.is_valid()).upper()}"]
    if not vresults.is_perfect():
        lines += [
            f"{'validation error(s)':<25}: {vresults.error_count}",
            f"{'validation warning(s)':<25}: {vresults.warning_count}",
        ]
        lines += [
            f"{'    general':<25}: {options.general_consistency}",
            f"{'    identifier':<25}: {options.identifier_consistency}",
            f"{'    mathml':<25}: {options.mathml_consistency}",
            f"{'    overdetermined':<25}: {options.overdetermined_model}",
            f"{'    sbo':<25}: {options.sbo_consistency}",
            f"{'    units':<25}: {options.units_consistency}",
        ]
        if comp_doc is not None:
            lines.append(f"{'    comp flat model':<25}: {options.comp_flat_model}")
    groups = vresults.groups()
    # the overview pays off where the findings are not all logged one by one
    # or repeat an error id, which is what buries the one fix in a large model
    if groups and (not options.log_errors or vresults.all_count > len(groups)):
        lines.append("findings by error id:")
        for group in groups[:_REPORTED_GROUPS]:
            lines.append(
                f"    {group.error_id:>7} {group.severity_string.lower():<8} "
                f"x{group.count:<6} {group.short_message}"
            )
        if len(groups) > _REPORTED_GROUPS:
            lines.append(
                f"    ... and {len(groups) - _REPORTED_GROUPS} more error id(s)"
            )
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
        vresults.log(max_per_error=options.max_logged_per_error)

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
