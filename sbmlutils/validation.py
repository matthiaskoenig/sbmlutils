# -*- coding: utf-8 -*-
"""
Validation and checking functions.
Helper functions for simple validation and display of problems.
Helper functions if setting sbml information was successful.
"""
# TODO: clean up
# TODO: unittests for various files


from __future__ import print_function, division

import os.path
import logging
import time
import warnings
import libsbml


def check(value, message):
    """
    Checks the libsbml return value and prints message if something happened.

    If 'value' is None, prints an error message constructed using
      'message' and then exits with status code 1. If 'value' is an integer,
      it assumes it is a libSBML return status code. If the code value is
      LIBSBML_OPERATION_SUCCESS, returns without further action; if it is not,
      prints an error message constructed using 'message' along with text from
      libSBML explaining the meaning of the code, and exits with status code 1.

    """
    if value is None:
        print('Error: LibSBML returned a null value trying to <' + message + '>.')
    elif type(value) is int:
        if value == libsbml.LIBSBML_OPERATION_SUCCESS:
            return
        else:
            print('Error encountered trying to <' + message + '>.')
            print('LibSBML returned error code ' + str(value) + ': "'
                  + libsbml.OperationReturnValue_toString(value).strip() + '"')
    else:
        return


def check_sbml(filepath, name=None, ucheck=True):
    """ Checks the given SBML file path or String for validation errors.

    :param filepath: path of SBML file
    :param ucheck: boolen if unit checks should be performed
    :return: number of errors
    """
    # FIXME: check if this is also working for SBML strings
    if name is None:
        if len(filepath) < 100:
            name = filepath
        else:
            name = filepath[0:99] + '...'

    doc = libsbml.readSBML(filepath)
    return check_doc(doc, name=name, ucheck=ucheck)


def check_doc(doc, name=None, ucheck=True):
    """
        Checks the given SBML document and prints errors of the given severity.

        Individual checks can be changed via the categories
            doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, False)
            doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MODELING_PRACTICE, False)

        :param sbml: SBML file or str
        :type sbml: file | str
        :return: number of errors
        """
    if name is None:
        name = str(doc)

    # set the unit checking, similar for the other settings
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, ucheck)

    numCCErr = 0  # error count
    numCCWarn = 0  # warning count
    current = time.clock()
    Nerrors = doc.checkConsistency()

    if Nerrors > 0:
        valid_status = True
        for i in range(Nerrors):
            severity = doc.getError(i).getSeverity()
            if (severity == libsbml.LIBSBML_SEV_ERROR) or (severity == libsbml.LIBSBML_SEV_FATAL):
                numCCErr += 1
                valid_status = False
            else:
                numCCWarn += 1

    lines = [
        '-' * 80,
        name,
        "{>15:}: {}".format("check time (ms)", str(time.clock() - current)),
        "{>15:}: {}".format("valid", valid_status),
        "{>15:}: {}".format("validation error(s)", numCCErr),
        "{>15:}: {}".format("validation warnings(s)", numCCWarn),
        '-' * 80,
    ]
    info = "\n".join(lines)
    if numCCWarn > 0:
        if numCCErr > 0:
            logging.error(info)
        else:
            logging.warn(info)
    else:
        logging.debug(info)

    # FIXME: print to logging
    print_errors(doc)
    return Nerrors


def print_errors(doc):
    """ Prints errors of SBMLDocument.

    :param doc:
    :return:
    """
    for k in range(doc.getNumErrors()):
        error = doc.getError(k)
        error_str = error_string(error, k)
        print(error_str)


def error_string(error, k=None):
    """ String representation of SBMLError.

    :param error:
    :return:
    """
    package = error.getPackage()
    if package == '':
        package = 'core'

    error_str = 'E{}: {} ({}, L{}, {})  \n' \
                '{}\n' \
                '[{}] {}\n' \
                '{}\n'.format(
        k, error.getCategoryAsString(), package, error.getLine(), 'code',
        '-' * 60,
        error.getSeverityAsString(), error.getShortMessage(),
        error.getMessage())
    return error_str
