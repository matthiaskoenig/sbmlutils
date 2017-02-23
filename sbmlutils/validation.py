# -*- coding: utf-8 -*-
"""
SBMLValidator based on the sbml.org validator example code.

"""
# TODO: only one SBML checking functionality (-> remove duplicate code between check_sbml and validate_SBML)

from __future__ import print_function, division

import os.path
import sys
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


def validate_sbml(sbml_file, ucheck=True):
    """
    Validate the SBML file.
    :param sbml_file:
    :param ucheck:
    :return:
    """
    validator = SBMLValidator(ucheck=ucheck)
    return validator.validate(sbml_file)


def check_sbml(sbml):
    """
    Checks the given SBML document and prints errors of the given severity.

    Individual checks can be changed via the categories
        doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, False)
        doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MODELING_PRACTICE, False)

    :param sbml: SBML file or str
    :type sbml: file | str
    :return: number of errors
    """

    current = time.clock()
    doc = libsbml.readSBML(sbml)
    doc.checkConsistency()
    Nerrors = doc.getNumErrors()

    if len(sbml) < 100:
        name = sbml
    else:
        name = sbml[0:99] + '...'

    print('-'*80)
    print(name)
    print("read time (ms): " + str(time.clock() - current))
    print("validation error(s): " + str(Nerrors))
    print('-' * 80)

    for k in range(Nerrors):
        error = doc.getError(k)
        error_str = error_string(error, k)
        print(error_str)

    return Nerrors


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

class SBMLValidator:
    def __init__(self, ucheck):
        self.reader = libsbml.SBMLReader()
        self.ucheck = ucheck
        self.numinvalid = 0
 
    def validate(self, infile):
        """
        Based on the libsbml validation code.
        :param infile:
        :return:
        """

        if not os.path.exists(infile):
            warnings.warn("[Error] {} : No such file.".format(infile))
            self.numinvalid += 1
            return
 
        start = time.time()
        sbmlDoc = libsbml.readSBML(infile)
        stop = time.time()
        timeRead = (stop - start)*1000
        errors = sbmlDoc.getNumErrors()

        seriousErrors = False
 
        numReadErr = 0
        numReadWarn = 0
        errMsgRead = ""

        if errors > 0:
            for i in range(errors):
                severity = sbmlDoc.getError(i).getSeverity()
                if (severity == libsbml.LIBSBML_SEV_ERROR) or (severity == libsbml.LIBSBML_SEV_FATAL):
                    seriousErrors = True
                    numReadErr += 1
                else:
                    numReadWarn += 1

                errMsgRead = sbmlDoc.getErrorLog().toString()

        # If serious errors are encountered while reading an SBML document, it
        # does not make sense to go on and do full consistency checking because
        # the model may be nonsense in the first place.
 
        numCCErr = 0
        numCCWarn = 0
        errMsgCC = ""
        skipCC = False
        timeCC = 0.0

        if seriousErrors:
            skipCC = True
            errMsgRead += "Further consistency checking and validation aborted."
            self.numinvalid += 1
        else:
            sbmlDoc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, self.ucheck)
            start = time.time()
            failures = sbmlDoc.checkConsistency()
            stop = time.time()
            timeCC = (stop - start)*1000

            if failures > 0:

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
        
        return {"numCCErr": numCCErr,
                 "numCCWarn": numCCWarn,
                 "errMsgCC": errMsgCC,
                 "skipCC": skipCC,
                 "timeCC": timeCC
                }


if __name__ == "__main__":
    # TODO: fix
    from sbmlutils.tests.testdata import test_sbml
    check_sbml(test_sbml)

    from sbmlutils.tests.testdata import vdp_sbml
    check_sbml(vdp_sbml)

