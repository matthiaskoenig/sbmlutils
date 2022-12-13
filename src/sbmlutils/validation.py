"""Helpers for validation and checking of SBML and libsbml operations."""
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional

import libsbml

from sbmlutils.console import console
from sbmlutils.log import get_logger


logger = get_logger(__name__)


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
        logger.error(f"Error: LibSBML returned a null value trying to <{message}>.")
        valid = False
    elif isinstance(value, int):
        if value != libsbml.LIBSBML_OPERATION_SUCCESS:
            logger.error(f"Error encountered trying to '{message}'.")
            logger.error(
                f"LibSBML returned error code {str(value)}: "
                f"{libsbml.OperationReturnValue_toString(value).strip()}"
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
        errors: Optional[List[libsbml.SBMLError]] = None,
        warnings: Optional[List[libsbml.SBMLError]] = None,
    ):
        """Initialize ValidationResult."""
        if errors is None:
            errors = list()
        if warnings is None:
            warnings = list()

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
        errors = list()
        warnings = list()
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
        return self.error_count == 0  # type: ignore

    def is_perfect(self) -> bool:
        """Get perfect status (perfect model), i.e., no errors and warnings."""
        return self.error_count == 0 and self.warning_count == 0  # type: ignore


def log_sbml_errors_for_doc(doc: libsbml.SBMLDocument) -> None:
    """Log errors of current SBMLDocument."""
    for k in range(doc.getNumErrors()):
        log_sbml_error(error=doc.getError(k))


def log_sbml_error(error: libsbml.SBMLError, index: Optional[int] = None) -> None:
    """Log SBMLError."""
    msg, severity = error_string(error=error, index=index)
    if severity == libsbml.LIBSBML_SEV_WARNING:
        logger.warning(msg, extra={"markup": True})
    elif severity in [libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL]:
        logger.error(msg, extra={"markup": True})
    else:
        logger.info(msg, extra={"markup": True})


def error_string(error: libsbml.SBMLError, index: Optional[int] = None) -> tuple:
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
    options: Optional[ValidationOptions] = None,
    title: Optional[str] = None,
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
        libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, options.units_consistency
    )
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_SBO_CONSISTENCY, options.sbo_consistency
    ),
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_OVERDETERMINED_MODEL, options.overdetermined_model
    )
    doc.setConsistencyChecks(
        libsbml.LIBSBML_CAT_SBO_CONSISTENCY, options.sbo_consistency
    ),

    # time
    current = time.perf_counter()

    # check the document
    results_internal: ValidationResult
    if options.internal_consistency:
        results_internal = _check_consistency(doc, internal_consistency=True)
    else:
        results_internal = ValidationResult()
    results_not_internal = _check_consistency(doc, internal_consistency=False)

    # sum up
    vresults = ValidationResult.from_results([results_internal, results_not_internal])

    lines = [str(title), f"{'valid':<25}: {str(vresults.is_valid()).upper()}"]
    if not vresults.is_perfect():
        lines += [
            f"{'validation error(s)':<25}: {vresults.error_count}",
            f"{'validation warnings(s)':<25}: {vresults.warning_count}",
        ]
    lines += [
        f"{'check time (s)':<25}: {time.perf_counter() - current:.3f}",
    ]
    info = "\n".join(lines)

    if vresults.is_perfect():
        style = "success"
    else:
        if vresults.is_valid():
            style = "warning"
        else:
            style = "error"

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
    doc: libsbml.SBMLDocument, internal_consistency: bool = False
) -> ValidationResult:
    """Calculate the type of errors.

    :param doc: SBMLDocument
    :param internal_consistency: flag for internal consistency
    :return: ValidationResult
    """
    errors = list()
    warnings = list()
    if internal_consistency:
        count = doc.checkInternalConsistency()
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
