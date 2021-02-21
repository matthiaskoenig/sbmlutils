"""Helpers for validation and checking of SBML and libsbml operations."""
import logging
import time
from typing import Iterable, List, Optional

import libsbml

from sbmlutils.utils import bcolors


logger = logging.getLogger(__name__)


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
            logger.error(f"Error encountered trying to <{message}>.")
            logger.error(
                f"LibSBML returned error code {str(value)}: "
                f"{libsbml.OperationReturnValue_toString(value).strip()}"
            )
            valid = False

    return valid


class ValidationResult:
    """Results of an SBMLDocument validation."""

    def __init__(
        self,
        errors: List[libsbml.SBMLError] = None,
        warnings: List[libsbml.SBMLError] = None,
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


def log_sbml_error(error: libsbml.SBMLError, index: int = None) -> None:
    """Log SBMLError."""
    msg, severity = error_string(error=error, index=index)
    if severity == libsbml.LIBSBML_SEV_WARNING:
        logger.warning(msg)
    elif severity in [libsbml.LIBSBML_SEV_ERROR, libsbml.LIBSBML_SEV_FATAL]:
        logger.error(msg)
    else:
        logger.info(msg)


def error_string(error: libsbml.SBMLError, index: int = None) -> tuple:
    """Get string representation and severity of SBMLError.

    :param error: SBML error
    :param index: index of error
    :return:
    """
    package = error.getPackage()
    if package == "":
        package = "core"

    severity = error.getSeverity()
    lines = [
        bcolors.BGWHITE
        + bcolors.BLACK
        + "E{}: {} ({}, L{}, {})".format(
            index, error.getCategoryAsString(), package, error.getLine(), "code"
        )
        + bcolors.ENDC
        + bcolors.ENDC,
        bcolors.FAIL
        + "[{}] {}".format(error.getSeverityAsString(), error.getShortMessage())
        + bcolors.ENDC,
        bcolors.OKBLUE + error.getMessage() + bcolors.ENDC,
    ]
    error_str = "\n".join(lines)
    return error_str, severity


def validate_doc(
    doc: libsbml.SBMLDocument,
    name: Optional[str] = None,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
) -> ValidationResult:
    """Validate SBMLDocument.

    :param doc: SBMLDocument to check
    :param name: identifier or path for report
    :param log_errors: boolean flag of errors should be logged
    :param units_consistency: boolean flag units consistency
    :param modeling_practice: boolean flag modeling practise
    :param internal_consistency: boolean flag internal consistency

    :return: ValidationResult
    """
    if not name:
        name = str(doc)

    # set the unit checking, similar for the other settings
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, units_consistency)
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MODELING_PRACTICE, modeling_practice)

    # time
    current = time.perf_counter()

    # all, error, warn
    if internal_consistency:
        results_internal = _check_consistency(doc, internal_consistency=True)
    else:
        results_internal = ValidationResult()
    results_not_internal = _check_consistency(doc, internal_consistency=False)

    # sum up
    vresults = ValidationResult.from_results([results_internal, results_not_internal])

    lines = [
        "",
        "-" * 80,
        str(name),
        "{:<25}: {}".format("valid", str(vresults.is_valid()).upper()),
    ]
    if not vresults.is_perfect():
        lines += [
            "{:<25}: {}".format("validation error(s)", vresults.error_count),
            "{:<25}: {}".format("validation warnings(s)", vresults.warning_count),
        ]
    lines += [
        "{:<25}: {:.3f}".format("check time (s)", time.perf_counter() - current),
        "-" * 80,
        "",
    ]
    info = "\n".join(lines)

    if vresults.is_valid():
        info = bcolors.OKGREEN + info + bcolors.ENDC
    else:
        info = bcolors.FAIL + info + bcolors.ENDC
    info = bcolors.BOLD + info + bcolors.ENDC

    # overall validation report
    if vresults.is_perfect():
        print(info)
    else:
        if vresults.is_valid():
            logging.warning(info)
        else:
            logging.error(info)

    # individual error and warning report
    if log_errors:
        vresults.log()

    return vresults


def _check_consistency(
    doc: libsbml.SBMLDocument, internal_consistency: bool = False
) -> ValidationResult:
    """Calculate the type of errors.

    :param doc:
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
