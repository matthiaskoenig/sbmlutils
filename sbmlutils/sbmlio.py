"""
Utility functions for reading, writing and validating SBML.
"""
from pathlib import Path
from typing import Union, List
import logging

import libsbml

from sbmlutils.utils import deprecated
from sbmlutils import __version__
from sbmlutils import validation

logger = logging.getLogger(__name__)


def read_sbml(source: Union[Path, str],
              validate: bool = True,
              log_errors: bool = True,
              units_consistency: bool = True,
              modeling_practice: bool = True,
              internal_consistency: bool = True
              ) -> libsbml.SBMLDocument:
    """Read SBMLDocument from given source.

    :param source: SBML path or string
    :param validate:
    :param log_errors: validation flag
    :param units_consistency: validation flag
    :param modeling_practice: validation flag
    :param internal_consistency: validation flag

    :return: SBMLDocument
    """
    reader = libsbml.SBMLReader()
    if isinstance(source, str) and "<sbml" in source:
        doc = reader.readSBMLFromString(source)
    else:
        if not isinstance(source, Path):
            logger.error(f"All SBML paths should be of type 'Path', but "
                         f"'{type(source)}' found for: {source}")
            source = Path(source)

        doc = reader.readSBMLFromFile(str(source))

    # check for errors
    if doc.getNumErrors() > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            err_message = f"Unreadable SBML file"
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            err_message = "Problems reading SBML file: XMLFileOperationError"
        else:
            err_message = "Problems reading SBML file."

        err_message = f"read_sbml error '{source}': {err_message}"
        logger.error(err_message)
        raise IOError(err_message)

    # validate file
    if validate:
        validation.check_doc(
            doc=doc,
            log_errors=log_errors,
            units_consistency=units_consistency,
            modeling_practice=modeling_practice,
            internal_consistency=internal_consistency
        )

    return doc


def write_sbml(doc: libsbml.SBMLDocument, filepath: Path,
               program_name: str = 'sbmlutils',
               program_version: str = str(__version__),
               validate: bool = True,
               log_errors: bool = True,
               units_consistency: bool = True,
               modeling_practice: bool = True,
               internal_consistency: bool = True
               ) -> None:
    """ Write SBMLDocument to file.

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

    :return: None
    """
    writer = libsbml.SBMLWriter()
    if program_name:
        writer.setProgramName(program_name)
    if program_version:
        writer.setProgramVersion(program_version)
    writer.writeSBMLToFile(doc, str(filepath))

    # This validates the written file
    if validate:
        validate_sbml(
            source=filepath,
            log_errors=log_errors,
            units_consistency=units_consistency,
            modeling_practice=modeling_practice,
            internal_consistency=internal_consistency
        )


def validate_sbml(source: Union[str, Path], name: str = None,
                  log_errors: bool = True,
                  units_consistency: bool = True,
                  modeling_practice: bool = True,
                  internal_consistency: bool = True) -> List[int]:
    """ Checks given SBML source.

    :param source: SBML path or string
    :param name: identifier or path for report
    :param units_consistency: boolean flag units consistency
    :param modeling_practice: boolean flag modeling practise
    :param internal_consistency: boolean flag internal consistency
    :param log_errors: boolean flag of errors should be logged
    :return: Nall, Nerr, Nwarn (number of all warnings/errors, errors and warnings)
    """
    doc = read_sbml(source)
    return validation.check_doc(
        doc, name=name,
        log_errors=log_errors,
        units_consistency=units_consistency,
        modeling_practice=modeling_practice,
        internal_consistency=internal_consistency
    )


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
