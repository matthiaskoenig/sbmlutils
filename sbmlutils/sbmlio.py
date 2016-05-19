"""
Utility objects and methods for the work with SBML.
"""
from libsbml import *
from sbmlutils import validation


def write_and_check(doc, sbml_file):
    # write and check the SBML file
    writer = SBMLWriter()
    writer.writeSBML(doc, sbml_file)
    from validation import check_sbml
    check_sbml(sbml_file)


def write_sbml(doc, sbml_file, validate=True, program_name=None, program_version=None):
    """ Write SBML to file. """
    writer = SBMLWriter()
    if program_name:
        writer.setProgramName(program_name)
    if program_version:
        writer.setProgramVersion(program_version)
    writer.writeSBMLToFile(doc, sbml_file)

    # validate the model with units (only for small models)
    if validate:
        validation.validate_sbml(sbml_file)


def writeModelToSBML(model, filename):
    writer = SBMLWriter()
    doc = SBMLDocument()
    doc.setModel(model)
    writer.writeSBMLToFile(doc, filename)


def createSBMLFileNameFromModelId(modelId, folder):
    return folder + '/' + modelId + '.xml'

########################################################################################################################



