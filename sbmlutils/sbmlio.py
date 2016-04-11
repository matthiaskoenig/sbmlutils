"""
Utility objects and methods for the work with SBML.
"""
from libsbml import *
from ..sbmlutils import validation



### MODEL CHECKING #####################################################################################################

def check(value, message):
    """If 'value' is None, prints an error message constructed using
      'message' and then exits with status code 1. If 'value' is an integer,
      it assumes it is a libSBML return status code. If the code value is
      LIBSBML_OPERATION_SUCCESS, returns without further action; if it is not,
      prints an error message constructed using 'message' along with text from
      libSBML explaining the meaning of the code, and exits with status code 1.
    """
    if value == None:
        print('LibSBML returned a null value trying to ' + message + '.')
        print('Exiting.')
        sys.exit(1)
    elif type(value) is int:
        if value == LIBSBML_OPERATION_SUCCESS:
            return
        else:
            print('Error encountered trying to ' + message + '.')
            print('LibSBML returned error code ' + str(value) + ': "' \
                  + OperationReturnValue_toString(value).strip() + '"')
            print('Exiting.')
            sys.exit(1)
    else:
        return


### MODEL IO ###########################################################################################################

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



