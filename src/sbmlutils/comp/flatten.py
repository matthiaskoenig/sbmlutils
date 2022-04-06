"""Helpers for model flattening."""
import os
import time
from pathlib import Path

import libsbml

from sbmlutils.console import console
from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.log import get_logger
from sbmlutils.validation import validate_doc


logger = get_logger(__name__)


def flatten_sbml(
    sbml_path: Path, sbml_flat_path: Path = None, leave_ports: bool = True
) -> libsbml.SBMLDocument:
    """Flatten given SBML file.

    :param sbml_path: input path to SBML file to flatten (should be a comp model)
    :param sbml_flat_path: output path for flat SBML
    :param leave_ports: boolean flag to leave ports in flattened model.

    :return: flattened SBMLDocument
    """
    # FIXME: not working with relative paths,
    # necessary to change the working directory to the sbml file directory
    # to resolve relative links to external model definitions.
    if not isinstance(sbml_path, Path):
        sbml_path = Path(sbml_path)

    working_dir = os.getcwd()
    os.chdir(str(sbml_path.parent))

    doc = read_sbml(source=sbml_path)
    flat_doc = flatten_sbml_doc(
        doc, leave_ports=leave_ports, output_path=sbml_flat_path
    )

    # change back the working dir
    os.chdir(working_dir)

    return flat_doc


def flatten_sbml_doc(
    doc: libsbml.SBMLDocument, output_path: Path = None, leave_ports: bool = True
) -> libsbml.SBMLDocument:
    """Flatten SBMLDocument.

    Validation should be performed before the flattening and is not part
    of the flattening routine.
    If an output path is provided the file is written to the output path.

    :param doc: SBMLDocument to flatten.
    :param output_path: Path to write flattended SBMLDocument to
    :param leave_ports: flag to leave ports

    :return: SBMLDocument
    """
    error_count = doc.getNumErrors()
    if error_count > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            # Handle case of unreadable file here.
            logger.error("SBML error in doc: libsbml.XMLFileUnreadable")
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            # Handle case of other file error here.
            logger.error("SBML error in doc: libsbml.XMLFileOperationError")
        else:
            # Handle other error cases here.
            logger.error("SBML errors in doc, see SBMLDocument error log.")

    # converter options
    props = libsbml.ConversionProperties()
    props.addOption("flatten comp", True)  # Invokes CompFlatteningConverter
    props.addOption("leave_ports", leave_ports)  # Indicates whether to leave ports
    props.addOption("abortIfUnflattenable", "none")

    # flatten
    current = time.perf_counter()
    result = doc.convert(props)
    flattened_status = result == libsbml.LIBSBML_OPERATION_SUCCESS

    lines = [
        str(doc),
        "{:<25}: {}".format("flattened", str(flattened_status).upper()),
        "{:<25}: {:.3f}".format("flatten time (ms)", time.perf_counter() - current),
    ]
    info = "\n".join(lines)

    if flattened_status:
        console.rule("Flatten SBML", style="success")
        console.print(info, style="success")
        console.rule(style="success")
    else:
        console.rule("Flatten SBML", style="error")
        console.print(info, style="error")
        raise ValueError(
            "SBML could not be flattend due to errors in the SBMLDocument."
        )

    if output_path is not None:
        write_sbml(doc, filepath=output_path)
        logger.info(f"Flattened model created: '{output_path}'")

    return doc


def flatten_external_model_definitions(
    doc: libsbml.SBMLDocument, validate: bool = False
) -> libsbml.SBMLDocument:
    """Convert all ExternalModelDefinitions to ModelDefinitions.

    I.e. the definition of models in external files are read
    and directly included in the top model. The resulting
    comp model consists than only of a single file.

    The model refs in the submodel do not change in the process,
    so no need to update the submodels.

    :param doc: SBMLDocument
    :param validate: validation flag
    :return: SBMLDocument with ExternalModelDefinitions replaced
    """
    logger.debug("* flattenExternalModelDefinitions")

    # FIXME: handle multiple levels of hierarchies. Recursively to handle the ExternalModelDefinitions of submodels
    logger.warning(
        "flattenExternalModelDefinitions is experimental and does not work recursively!"
    )

    comp_doc = doc.getPlugin("comp")
    if comp_doc is None:
        logger.warning("Model is not a comp model, no ExternalModelDefinitions")
        return doc
    emd_list = comp_doc.getListOfExternalModelDefinitions()
    if (emd_list is None) or (len(emd_list) == 0):
        # no ExternalModelDefinitions
        logger.warning("Model does not contain any ExternalModelDefinitions")
        return doc
    else:
        emd_ids = []
        for emd in emd_list:
            logger.debug(emd)
            emd_ids.append(emd.getId())

            # get the model definition from the model
            ref_model = emd.getReferencedModel()

            ref_doc = ref_model.getSBMLDocument()
            # print(ref_model)
            for k in range(ref_doc.getNumPlugins()):
                plugin = ref_doc.getPlugin(k)
                # print(k, plugin)

                # enable the package on the main SBMLDocument
                uri = plugin.getURI()
                prefix = plugin.getPrefix()
                doc.enablePackage(uri, prefix, True)

            # print("\n")

            # add model definition for model
            md = libsbml.ModelDefinition(ref_model)
            comp_doc.addModelDefinition(md)

        # remove the emds afterwards
        for emd_id in emd_ids:
            # remove the emd from the model
            comp_doc.removeExternalModelDefinition(emd_id)

    # validate
    if validate:
        validate_doc(doc)
    return doc
