"""Helpers for model flattening."""

import logging
import time
from pathlib import Path

import libsbml

from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.validation import log_sbml_errors_for_doc

logger = logging.getLogger(__name__)


def flatten_sbml(
    sbml_path: Path | str,
    sbml_flat_path: Path | str,
    leave_ports: bool = True,
    validate: bool = False,
) -> libsbml.SBMLDocument:
    """Flatten given SBML file.

    A relative path is relative to the working directory, which is never
    changed. libsbml resolves the `comp:source` of an external model definition
    against the location of the document which names it, i.e. relative to the
    directory of `sbml_path`, and of the external files in turn.

    libsbml opens the file of an external model definition itself, and on
    Windows it does so with the narrow (ANSI) file API, which cannot open a
    path with a non-ASCII character: a model with external model definitions
    in such a directory cannot be flattened on Windows. `sbml_path` and
    `sbml_flat_path` themselves may be any path, a path libsbml cannot open
    is read and written by python.

    :param sbml_path: input path to SBML file to flatten (should be a comp model)
    :param sbml_flat_path: output path for flat SBML
    :param leave_ports: boolean flag to leave ports in flattened model.
    :param validate: validate the comp model before flattening it, see
        `flatten_sbml_doc`

    :return: flattened SBMLDocument

    :raises ValueError: if the file cannot be read, has no model, or libsbml
        cannot flatten the document, see `flatten_sbml_doc`
    """
    doc = read_sbml(source=Path(sbml_path))
    return flatten_sbml_doc(
        doc,
        leave_ports=leave_ports,
        sbml_flat_path=Path(sbml_flat_path),
        validate=validate,
    )


def flatten_sbml_doc(
    doc: libsbml.SBMLDocument,
    sbml_flat_path: Path | None = None,
    leave_ports: bool = True,
    validate: bool = False,
) -> libsbml.SBMLDocument:
    """Flatten SBMLDocument.

    The document is flattened in place. The comp model is not validated by
    default: the validation is the full consistency check of the document and
    most of the time of the flattening, and a model is usually validated when
    it is written (`create_model`). Validate an unvalidated comp model first or
    pass `validate=True`: without the validation an invalid comp model can be
    flattened into a wrong flat model which is itself valid, e.g. a replacement
    of a species by a parameter drops the species, a duplicate id in a model
    definition keeps one of the two elements, and a conversion factor with an
    unknown id is dropped.

    A document with errors from reading it is not flattened. A submodel, an
    external model definition or a replaced element which cannot be resolved
    fails the flattening either way; without the validation libsbml finds such
    a reference during the conversion, so the document is then left partly
    flattened.

    If an output path is provided the file is written to the output path.

    :param doc: SBMLDocument to flatten.
    :param sbml_flat_path: Path to write flattended SBMLDocument to
    :param leave_ports: flag to leave ports
    :param validate: validate the comp model before flattening it, so that an
        invalid model is not flattened and the document is left as it is

    :return: SBMLDocument

    :raises ValueError: if the document has no model, e.g. a library of comp
        model definitions, which has nothing to flatten them into
    """
    if doc.getModel() is None:
        raise ValueError(
            "SBML without a model cannot be flattened, a document with only "
            "model definitions has no model to flatten them into."
        )
    # a file which could not be read or opened has no model and is rejected
    # above, so an error here comes from the content of the document; the
    # converter flattens such a document when it does not validate it
    if _num_errors(doc) > 0:
        logger.error("SBML errors in doc, see SBMLDocument error log.")
        log_sbml_errors_for_doc(doc)
        raise ValueError("SBML could not be flattend due to errors.")

    # converter options
    props = libsbml.ConversionProperties()
    props.addOption("flatten comp", True)  # Invokes CompFlatteningConverter
    props.addOption("leave_ports", leave_ports)  # Indicates whether to leave ports
    props.addOption("abortIfUnflattenable", "none")
    props.addOption("performValidation", validate)

    # flatten
    current = time.perf_counter()
    result = doc.convert(props)
    # the converter reports a replaced element it cannot resolve in the error
    # log and still returns success
    flattened_status = (
        result == libsbml.LIBSBML_OPERATION_SUCCESS and _num_errors(doc) == 0
    )

    lines = [
        str(doc),
        f"{'flattend':<25}: {str(flattened_status).upper()}",
        f"{'flatten time (ms)':<25}: {time.perf_counter() - current:.3f}",
    ]
    info = "\n".join(lines)

    if flattened_status:
        logger.info("Flatten SBML\n%s", info)
    else:
        logger.error("Flatten SBML\n%s", info)
        log_sbml_errors_for_doc(doc)
        raise ValueError("SBML could not be flattend due to errors.")

    if sbml_flat_path is not None:
        write_sbml(doc, filepath=sbml_flat_path)
        logger.info("Flattened model created: '%s'", sbml_flat_path)

    return doc


def _num_errors(doc: libsbml.SBMLDocument) -> int:
    """Count the errors and fatal errors in the error log of a document.

    :param doc: SBMLDocument whose error log is counted

    :return: number of entries with the severity error or fatal
    """
    log: libsbml.SBMLErrorLog = doc.getErrorLog()
    return log.getNumFailsWithSeverity(
        libsbml.LIBSBML_SEV_ERROR
    ) + log.getNumFailsWithSeverity(libsbml.LIBSBML_SEV_FATAL)
