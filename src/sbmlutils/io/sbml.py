"""Utility functions for reading, writing and validating SBML."""

import logging
from pathlib import Path

import libsbml

from sbmlutils.validation import (
    ValidationOptions,
    ValidationResult,
    log_sbml_errors_for_doc,
    validate_doc,
)

logger = logging.getLogger(__name__)


def read_sbml(
    source: Path | str,
    promote: bool = False,
    validate: bool = False,
    validation_options: ValidationOptions | None = None,
) -> libsbml.SBMLDocument:
    """Read SBMLDocument from given source.

    Local parameters can be promoted using the `promote flag.
    Allows to validate the file during reading via the `validate` flag.
    The subset of tested features in validation can be set via the
    `validation_options`.

    :param source: SBML path or string
    :param promote: promote local parameters to global parameters
    :param validate: validate file
    :param validation_options: options for validation

    :return: libsbml.SBMLDocument
    """
    doc: libsbml.SBMLDocument
    if isinstance(source, str) and "<sbml" in source:
        doc = libsbml.readSBMLFromString(source)
    else:
        if not isinstance(source, Path):
            logger.error(
                "All SBML paths should be of type 'Path', but '%s' found for: %s",
                type(source),
                source,
            )
            source = Path(source)

        doc = libsbml.readSBMLFromFile(str(source))

    # promote local parameters
    if promote:
        doc = promote_local_variables(doc)

    # check for errors
    if doc.getNumErrors() > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            err_message = "Unreadable SBML file"
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            err_message = "Problems reading SBML file: XMLFileOperationError"
        else:
            err_message = "SBMLDocumentErrors encountered while reading the SBML file."

        log_sbml_errors_for_doc(doc)
        logger.error("`read_sbml` error '%s': %s", source, err_message)

    if validate:
        validate_doc(
            doc=doc,
            options=validation_options,
            title=str(source),
        )

    return doc


def write_sbml(
    doc: libsbml.SBMLDocument,
    filepath: Path | None = None,
    validate: bool = False,
    validation_options: ValidationOptions | None = None,
    program_name: str | None = None,
    program_version: str | None = None,
) -> str | None:
    """Write SBMLDocument to file or string.

    To write the SBML to string use 'filepath=None', which returns the SBML string.

    The file can be validated during writing via the validate flag.

    :param doc: SBMLDocument to write
    :param filepath: output file to write
    :param validate: flag for validation
    :param validation_options: validation flag
    :param program_name: Program name for SBML file
    :param program_version: Program version for SBML file

    :return: None or SBML string
    """
    writer = libsbml.SBMLWriter()
    if program_name:
        writer.setProgramName(program_name)
    if program_version:
        writer.setProgramVersion(program_version)

    # write file
    source: str | Path
    sbml_str: str | None = None
    if filepath is None:
        sbml_str = writer.writeSBMLToString(doc)
        source = str(sbml_str)
    else:
        writer.writeSBMLToFile(doc, str(filepath))
        source = filepath

    # validation
    if validate:
        validate_sbml(
            source=source,
            title=str(source),
            validation_options=validation_options,
        )

    return sbml_str


def validate_sbml(
    source: str | Path,
    validation_options: ValidationOptions | None = None,
    title: str | None = None,
) -> ValidationResult:
    """Check given SBML source.

    :param source: SBML path or string
    :param validation_options: options for validation
    :param title: title for validation report (should be filname or model name)
    :return: ValidationResult
    """
    doc = read_sbml(source, promote=False, validate=False)
    return validate_doc(
        doc=doc,
        options=validation_options,
        title=title,
    )


def promote_local_variables(
    doc: libsbml.SBMLDocument, suffix: str = "_promoted"
) -> libsbml.SBMLDocument:
    """Promotes local variables in SBMLDocument.

    Manipulates SBMLDocument in place!

    :param doc: SBMLDocument
    :param suffix: str suffix for promoted SBML
    :return: SBMLDocument with promoted parameters
    """
    model: libsbml.Model = doc.getModel()
    if model.isSetId():
        model.setId(f"{model.getId()}{suffix}")

    # promote local parameters
    props = libsbml.ConversionProperties()
    props.addOption(
        "promoteLocalParameters", True, "Promotes all Local Parameters to Global ones"
    )
    if doc.convert(props) == libsbml.LIBSBML_OPERATION_SUCCESS:
        logger.info("Promotion of local parameters successful: %s", doc)
    else:
        logger.error("Promotion of local parameters failed: %s", doc)
    return doc
