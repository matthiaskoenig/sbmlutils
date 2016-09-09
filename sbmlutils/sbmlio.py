"""
Utility objects and methods for the work with SBML.
"""

import os
from libsbml import *
from sbmlutils import validation


def filepath_from_model_id(model_id, directory):
    """
    Create a filepath from model_id in given directory.

    :param model_id:
    :param directory:
    :return: filepath
    """
    return os.path.join(directory, '{}.xml'.format(model_id))


def write_and_check(doc, filename):
    """
    Write and check a given SBMLDocument to file.

    :param doc: SBMLDocument to write and check
    :param filename: output file
    :return: None
    """
    writer = SBMLWriter()
    writer.writeSBML(doc, filename)

    validation.check_sbml(filename)


def write_sbml(doc, filename, validate=True, program_name=None, program_version=None):
    """
    Write SBMLDocument to file.

    :param doc: SBMLDocument to write
    :param filename: output file to write
    :param validate: boolean flag for validation
    :param program_name: Program name for SBML file
    :param program_version: Program version for SBML file
    :return:
    """
    writer = SBMLWriter()
    if program_name:
        writer.setProgramName(program_name)
    if program_version:
        writer.setProgramVersion(program_version)
    writer.writeSBMLToFile(doc, filename)

    # validate the model with units (only for small models)
    if validate:
        validation.validate_sbml(filename)


def writeModelToSBML(model, filepath):
    """
    Write SBML Model to output file.
    An empty SBMLDocument is created for the model.

    :param model: SBML Model
    :param filepath: output file path
    :return:
    """
    writer = SBMLWriter()
    doc = SBMLDocument()
    doc.setModel(model)
    writer.writeSBMLToFile(doc, filepath)
