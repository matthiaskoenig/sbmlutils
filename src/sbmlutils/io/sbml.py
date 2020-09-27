"""
Utility functions for reading, writing and validating SBML.
"""
import logging
from pathlib import Path
from typing import List, Union

import libsbml

from sbmlutils import __version__, program_name, validation
from sbmlutils.utils import deprecated


logger = logging.getLogger(__name__)


def read_sbml(
    source: Union[Path, str],
    promote: bool = False,
    validate: bool = False,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
) -> libsbml.SBMLDocument:
    """Read SBMLDocument from given source.

    :param source: SBML path or string
    :param promote: promote local parameters to global parameters
    :param validate: validate file
    :param log_errors: validation flag
    :param units_consistency: validation flag
    :param modeling_practice: validation flag
    :param internal_consistency: validation flag

    :return: SBMLDocument
    """
    if isinstance(source, str) and "<sbml" in source:
        doc = libsbml.readSBMLFromString(source)
    else:
        if not isinstance(source, Path):
            logger.error(
                f"All SBML paths should be of type 'Path', but "
                f"'{type(source)}' found for: {source}"
            )
            source = Path(source)

        doc = libsbml.readSBMLFromFile(str(source))  # type: libsbml.SBMLDocument

    # promote local parameters
    if promote:
        doc = promote_local_variables(doc)  # type: libsbml.SBMLDocument

    # check for errors
    if doc.getNumErrors() > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            err_message = f"Unreadable SBML file"
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            err_message = "Problems reading SBML file: XMLFileOperationError"
        else:
            err_message = "SBMLDocumentErrors encountered while reading the SBML file."

        validation.log_sbml_errors_for_doc(doc)
        err_message = f"read_sbml error '{source}': {err_message}"
        logger.error(err_message)

    # validate file
    if validate:
        validation.validate_doc(
            doc=doc,
            name=source,
            log_errors=log_errors,
            units_consistency=units_consistency,
            modeling_practice=modeling_practice,
            internal_consistency=internal_consistency,
        )

    return doc


def write_sbml(
    doc: libsbml.SBMLDocument,
    filepath: Union[Path] = None,
    program_name: str = program_name,
    program_version: str = str(__version__),
    validate: bool = False,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
) -> str:
    """Write SBMLDocument to file or string.

    To write the SBML to string use 'filepath=None', which returns the SBML string.

    Optional validation with validate flag.

    :param doc: SBMLDocument to write
    :param filepath: output file to write
    :param validate: flag for validation (True: full validation, False: no validation)
    :param program_name: Program name for SBML file
    :param program_version: Program version for SBML file
    :param log_errors: validation flag
    :param units_consistency: validation flag
    :param modeling_practice: validation flag
    :param internal_consistency: validation flag

    :return: None or SBML string
    """
    writer = libsbml.SBMLWriter()
    if program_name:
        writer.setProgramName(program_name)
    if program_version:
        writer.setProgramVersion(program_version)

    if filepath is None:
        sbml_str = writer.writeSBMLToString(doc)
        source = sbml_str
    else:
        writer.writeSBMLToFile(doc, str(filepath))
        sbml_str = None
        source = filepath

    # This validates the written file or sbml string
    if validate:
        validate_sbml(
            source=source,
            name=source,
            log_errors=log_errors,
            units_consistency=units_consistency,
            modeling_practice=modeling_practice,
            internal_consistency=internal_consistency,
        )
    return sbml_str


def validate_sbml(
    source: Union[str, Path],
    name: str = None,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
) -> validation.ValidationResult:
    """Checks given SBML source.

    :param source: SBML path or string
    :param name: identifier or path for report
    :param units_consistency: boolean flag units consistency
    :param modeling_practice: boolean flag modeling practise
    :param internal_consistency: boolean flag internal consistency
    :param log_errors: boolean flag of errors should be logged
    :return: Nall, Nerr, Nwarn (number of all warnings/errors, errors and warnings)
    """
    doc = read_sbml(source)
    return validation.validate_doc(
        doc,
        name=name,
        log_errors=log_errors,
        units_consistency=units_consistency,
        modeling_practice=modeling_practice,
        internal_consistency=internal_consistency,
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
    model = doc.getModel()  # type: libsbml.Model
    model.setId(f"{model.id}{suffix}")

    # promote local parameters
    props = libsbml.ConversionProperties()
    props.addOption(
        "promoteLocalParameters", True, "Promotes all Local Parameters to Global ones"
    )

    if doc.convert(props) != libsbml.LIBSBML_OPERATION_SUCCESS:
        logger.error(f"Promotion of local parameters failed: {doc}")
    else:
        logger.info(f"Promotion of local paramters successful: {doc}")
    return doc


@deprecated
def write_model_to_sbml(model: libsbml.Model, filepath: Path) -> None:
    """Write SBML Model to file.

    An empty SBMLDocument is created for the model.

    :param model: SBML Model
    :param filepath: output path

    :return: None
    """
    doc = libsbml.SBMLDocument()
    doc.setModel(model)
    write_sbml(doc=doc, filepath=filepath)
