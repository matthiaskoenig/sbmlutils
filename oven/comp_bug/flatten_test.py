import os
import libsbml
import logging
import time



def flattenSBMLFile(sbml_path, leave_ports=True, output_path=None, suffix='_flat'):
    """ Flatten given SBML file.

    :param sbml_path:
    :param leave_ports:
    :param output_path:
    :param suffix to add to model id
    :return:
    """
    # necessary to change the working directory to the sbml file directory
    # to resolve relative links to external model definitions.
    working_dir = os.getcwd()
    sbml_dir = os.path.dirname(sbml_path)
    os.chdir(sbml_dir)

    reader = libsbml.SBMLReader()
    doc = reader.readSBML(sbml_path)
    flat_doc = flattenSBMLDocument(doc, leave_ports=leave_ports, output_path=output_path, suffix=suffix)

    # change back the working dir
    os.chdir(working_dir)

    return flat_doc


def flattenSBMLDocument(doc, leave_ports=True, output_path=None, suffix='_flat'):
    """ Flatten the given SBMLDocument.

    Validation should be performed before the flattening and is not part
    of the flattening routine.

    :param doc: SBMLDocument to flatten.
    :type doc: SBMLDocument
    :return:
    :rtype: SBMLDocument
    """
    Nerrors = doc.getNumErrors()
    if Nerrors > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            # Handle case of unreadable file here.
            logging.error("SBML error in doc: libsbml.XMLFileUnreadable")
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            # Handle case of other file error here.
            logging.error("SBML error in doc: libsbml.XMLFileOperationError")
        else:
            # Handle other error cases here.
            logging.error("SBML errors in doc, see SBMLDocument error log.")

    # converter options
    props = libsbml.ConversionProperties()
    props.addOption("flatten comp", True)  # Invokes CompFlatteningConverter
    props.addOption("leave_ports", leave_ports)  # Indicates whether to leave ports

    # flatten
    current = time.clock()
    result = doc.convert(props)
    flattened_status = (result==libsbml.LIBSBML_OPERATION_SUCCESS)

    lines = [
        '',
        '-' * 120,
        str(doc),
        "{:<25}: {}".format("flattened", str(flattened_status).upper()),
        "{:<25}: {:.3f}".format("flatten time (ms)", time.clock() - current),
        '-' * 120,
    ]
    info = "\n".join(lines)

    if flattened_status:
        logging.info(info)
    else:
        logging.error(info)
        raise ValueError("SBML could not be flattend due to errors in the SBMLDocument.")

    if suffix is not None:
        model = doc.getModel()
        if model is not None:
            model.setId(model.getId() + suffix)
            if model.isSetName():
                model.setName(model.getName() + suffix)

    if output_path is not None:
        # Write the results to the output file.
        libsbml.writeSBMLToFile(doc, output_path)
        logging.info("Flattened model written to {}".format(output_path))

    return doc


def check_doc(doc, name=None, ucheck=True, internalConsistency=True, show_errors=True):
    """
        Checks the given SBML document and prints errors of the given severity.

        Individual checks can be changed via the categories
            doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, False)
            doc.setConsistencyChecks(libsbml.LIBSBML_CAT_MODELING_PRACTICE, False)

        :param sbml: SBML file or str
        :type sbml: file | str
        :return: list of number of messages, number of errors, number of warnings
        """
    if name is None:
        name = str(doc)

    # set the unit checking, similar for the other settings
    doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, ucheck)

    # time
    current = time.clock()

    # all, error, warn
    if internalConsistency:
        Nall_in, Nerr_in, Nwarn_in = _check_consistency(doc, internalConsistency=True, show_errors=show_errors)
    else:
        Nall_in, Nerr_in, Nwarn_in = (0, 0, 0)
    Nall_noin, Nerr_noin, Nwarn_noin = _check_consistency(doc, internalConsistency=False, show_errors=show_errors)

    # sum up
    Nall = Nall_in + Nall_noin
    Nerr = Nerr_in + Nerr_noin
    Nwarn = Nwarn_in + Nwarn_noin
    valid_status = (Nerr is 0)

    lines = [
        '',
        '-' * 120,
        name,
        "{:<25}: {}".format("valid", str(valid_status).upper()),
    ]
    if Nall > 0:
        lines += [
            "{:<25}: {}".format("validation error(s)", Nerr),
            "{:<25}: {}".format("validation warnings(s)", Nwarn),
        ]
    lines += [
        "{:<25}: {:.3f}".format("check time (s)", time.clock() - current),
        '-' * 120,
    ]
    info = "\n".join(lines)

    if Nall > 0:
        if Nerr > 0:
            logging.error(info)
        else:
            logging.warning(info)
    else:
        logging.info(info)

    return Nall, Nerr, Nwarn


def _check_consistency(doc: libsbml.SBMLDocument, internalConsistency=False, show_errors=True):
    Nerr = 0  # error count
    Nwarn = 0  # warning count
    if internalConsistency:
        Nall = doc.checkInternalConsistency()
    else:
        Nall = doc.checkConsistency()

    if Nall > 0:
        for i in range(Nall):
            severity = doc.getError(i).getSeverity()
            if (severity == libsbml.LIBSBML_SEV_ERROR) or (severity == libsbml.LIBSBML_SEV_FATAL):
                Nerr += 1
            else:
                Nwarn += 1

        doc.printErrors()

    return Nall, Nerr, Nwarn

if __name__ == "__main__":


    for path in ["./top_L3V1.xml", "./top_L3V2.xml"]:
        print("*" * 80)
        print(path)
        print("*" * 80)

        # validate
        doc = libsbml.readSBML(path)
        check_doc(doc, ucheck=False, show_errors=True)


        flattenSBMLFile(path)

