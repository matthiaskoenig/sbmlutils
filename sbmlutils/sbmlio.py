"""
Utility functions for reading and writing SBML files and models.
Helper functions for path and filename manipulation.
"""
from __future__ import print_function, absolute_import

import logging
import os

import libsbml
from sbmlutils import validation


def read_sbml(filepath):
    """ Reads an SBMLDocument.

    :param filepath:
    :return: SBMLDocument
    """
    reader = libsbml.SBMLReader()
    if reader is None:
        # Handle the truly exceptional case of no object created here.
        logging.error("SBMLReader could not be created.")

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


def write_sbml(doc, filepath, validate=True, program_name=None, program_version=None, show_errors=True):
    """
    Write SBMLDocument to file.

    :param doc: SBMLDocument to write
    :param filepath: output file to write
    :param validate: flag for validation (True: full validation, False: no validation)
    :param program_name: Program name for SBML file
    :param program_version: Program version for SBML file
    :return:
    """
    writer = libsbml.SBMLWriter()
    if program_name:
        writer.setProgramName(program_name)
    if program_version:
        writer.setProgramVersion(program_version)
    writer.writeSBMLToFile(doc, filepath)

    # validate the model with units (only for small models)
    # This validates the written file
    if validate:
        if validate is True:
            validation.check_sbml(filepath)
        elif validate is validation.VALIDATION_NO_UNITS:
            validation.check_sbml(filepath, ucheck=False, show_errors=True)


def writeModelToSBML(model, filepath):
    """
    Write SBML Model to output file.
    An empty SBMLDocument is created for the model.

    :param model: SBML Model
    :param filepath: output file path
    :return:
    """
    writer = libsbml.SBMLWriter()
    doc = libsbml.SBMLDocument()
    doc.setModel(model)
    writer.writeSBMLToFile(doc, filepath)


def filepath_from_model_id(model_id, directory):
    """
    Create a filepath from model_id in given directory.

    :param model_id:
    :param directory:
    :return: filepath
    """
    return os.path.join(directory, '{}.xml'.format(model_id))
