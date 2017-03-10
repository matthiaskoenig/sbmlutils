# -*- coding: utf-8 -*-
"""
Validation and checking functions.
Helper functions for simple validation and display of problems.
Helper functions if setting sbml information was successful.
"""

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

    current = time.clock()
    Nerrors = doc.checkConsistency()

    if Nerrors > 0:

        isinvalid = False
        for i in range(failures):
            severity = sbmlDoc.getError(i).getSeverity()
            if (severity == libsbml.LIBSBML_SEV_ERROR) or (severity == libsbml.LIBSBML_SEV_FATAL):
                numCCErr += 1
                isinvalid = True
            else:
                numCCWarn += 1

        if isinvalid:
            self.numinvalid += 1

        errMsgCC = sbmlDoc.getErrorLog().toString()
        #
        # print results
        #


    lines = []
    lines.append(" filename : %s" % (infile))
    lines.append(" file size (byte) : %d" % (os.path.getsize(infile)))
    lines.append(" read time (ms) : %f" % (timeRead))

    if not skipCC:
        lines.append(" c-check time (ms) : %f" % (timeCC))
    else:
        lines.append(" c-check time (ms) : skipped")

    lines.append(" validation error(s) : %d" % (numReadErr + numCCErr))
    if not skipCC:
        lines.append(" consistency error(s): %d" % (numCCErr))
    else:
        lines.append(" consistency error(s): skipped")

    lines.append(" validation warning(s) : %d" % (numReadWarn + numCCWarn))
    if not skipCC:
        lines.append(" consistency warning(s): %d" % (numCCWarn))
    else:
        lines.append(" consistency warning(s): skipped")

    if errMsgRead or errMsgCC:
        lines.append('')
        lines.append("===== validation error/warning messages =====\n")
        if errMsgRead:
            lines.append(errMsgRead)
        if errMsgCC:
            lines.append("*** consistency check ***\n")
            lines.append(errMsgCC)
    val_string = '\n'.join(lines)
    print(val_string, '\n')


    logging.info('-' * 80)
    logging.info(name)
    logging.info("read time (ms): " + str(time.clock() - current))
    logging.info("validation error(s): " + str(Nerrors))
    logging.info('-' * 80)

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
