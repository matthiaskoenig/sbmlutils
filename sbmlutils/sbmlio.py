"""
Utility functions for reading and writing SBML files and models.
Helper functions for path and filename manipulation.
"""
from pathlib import Path
from typing import Union
import logging
from sbmlutils import __version__
import libsbml
from sbmlutils import validation



def read_sbml(filepath):
    """ Reads an SBMLDocument.

    :param filepath:
    :return: SBMLDocument
    """

    if not isinstance(sbml_path, Path):
        logger.warning(f"All paths should be of type 'Path', but '{type(sbml_path)}' found for: {sbml_path}")
        sbml_path = Path(sbml_path)

    if name is None:
        filepath = os.path.abspath(filepath)
        if len(filepath) < 100:
            name = filepath
        else:
            name = filepath[0:99] + '...'

    doc = libsbml.readSBML(filepath)


    reader = libsbml.SBMLReader()

    doc = reader.readSBMLFromFile(filepath)
    if doc.getNumErrors() > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            # Handle case of unreadable file here.
            logging.error("Unreadable SBML file.")
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            # Handle case of other file error here.
            logging.error("Problems reading SBML file: XMLFileOperationError")
        else:
            logging.error("Problems reading SBML file.")
        raise IOError

    return doc


def write_sbml(doc: libsbml.SBMLDocument, filepath: Path,
               validate: bool = True,
               program_name: str = 'sbmlutils',
               program_version: str = str(__version__),
               **kwargs  # optional validate arguments
               ) -> None:
    """ Write SBMLDocument to file.

    Optional validation with validate flag.

    :param doc: SBMLDocument to write
    :param filepath: output file to write
    :param validate: flag for validation (True: full validation, False: no validation)
    :param program_name: Program name for SBML file
    :param program_version: Program version for SBML file

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
        validation.check_sbml(sbml=filepath, **kwargs)


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
