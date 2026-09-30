"""Utility functions for reading, writing and validating SBML."""

import logging
from pathlib import Path

import libsbml

from sbmlutils.io import files
from sbmlutils.validation import (
    ValidationOptions,
    ValidationResult,
    log_sbml_errors_for_doc,
    validate_doc,
)

logger = logging.getLogger(__name__)


def read_sbml(
    source: Path | str,
    promote: bool = False,
    validate: bool = False,
    validation_options: ValidationOptions | None = None,
) -> libsbml.SBMLDocument:
    """Read SBMLDocument from given source.

    Local parameters can be promoted using the `promote flag.
    Allows to validate the file during reading via the `validate` flag.
    The subset of tested features in validation can be set via the
    `validation_options`.

    :param source: SBML path or string
    :param promote: promote local parameters to global parameters
    :param validate: validate file; the read errors are then logged by the
        validation, according to `ValidationOptions.log_errors`
    :param validation_options: options for validation

    :return: libsbml.SBMLDocument

    :raises ValueError: if the source cannot be read, see `_read_failures`,
        with the errors libsbml reported for it. A document without a model
        is returned as it is, SBML allows it; the errors of a document which
        was read are logged (or validated with `validate`), not raised.
    """
    doc, label = _read_document(source)
    unreadable: list[libsbml.SBMLError] = _read_failures(doc)
    if unreadable:
        raise ValueError(
            f"{label} could not be read:\n"
            + "\n".join(
                f"  E{error.getErrorId()} ({error.getSeverityAsString()}): "
                f"{error.getMessage().strip()}"
                for error in unreadable
            )
        )

    # promote local parameters
    if promote:
        doc = promote_local_variables(doc)

    # check for errors
    if doc.getNumErrors() > 0:
        if not validate:
            # with `validate` the read errors are part of the validation
            # result, which logs them once
            log_sbml_errors_for_doc(doc)
        logger.error("`read_sbml`: errors encountered while reading the %s.", label)

    if validate:
        validate_doc(
            doc=doc,
            options=validation_options,
            title=str(source),
        )

    return doc


#: the errors libsbml reports on the XML declaration; the document itself is
#: read in full, only the declaration SBML requires is missing
_XML_DECLARATION_ERRORS: frozenset[int] = frozenset(
    {libsbml.MissingXMLDecl, libsbml.MissingXMLEncoding}
)


def _shorten(source: Path | str, limit: int = 200) -> str:
    """Shorten a source for a message, a string which is not a path can be a document."""
    text = str(source)
    return text if len(text) <= limit else text[:limit] + "..."


def _read_document(source: Path | str) -> tuple[libsbml.SBMLDocument, str]:
    """Read an SBMLDocument from a path or an SBML string without raising.

    A file is read by python, see `sbmlutils.io.files`; a file which cannot
    be read is recorded in the document as libsbml's reader records it, as
    the error `XMLFileUnreadable`, or `XMLBadUTF8Content` for content which
    is not UTF-8.

    Args:
        source: SBML path or SBML string

    Returns:
        the document with the errors libsbml reported while parsing it, and
        a label of the source for messages, which does not repeat an SBML
        string
    """
    if isinstance(source, str) and "<sbml" in source:
        return libsbml.readSBMLFromString(source), "SBML string"

    if not isinstance(source, Path):
        logger.error(
            "All SBML paths should be of type 'Path', but '%s' found for: %s",
            type(source),
            _shorten(source),
        )
        source = Path(source)

    label = f"SBML file '{_shorten(source)}'"
    doc: libsbml.SBMLDocument
    try:
        # read by python, libsbml cannot open a non-ASCII path on Windows
        doc = libsbml.readSBMLFromString(files.read_text(source))
    except (OSError, ValueError) as err:
        # the error libsbml's own reader reports for the file, so that the
        # failure is part of the document as every other read error
        doc = libsbml.SBMLDocument()
        doc.getErrorLog().add(
            libsbml.SBMLError(
                libsbml.XMLBadUTF8Content
                if isinstance(err, ValueError)
                else libsbml.XMLFileUnreadable,
                doc.getLevel(),
                doc.getVersion(),
                str(err),
            )
        )
    # the location `libsbml.readSBMLFromFile` records for an absolute path;
    # libsbml resolves the `comp:source` of an external model definition
    # against it. A relative location is resolved wrongly, and a location set
    # as a percent-encoded URI (`Path.as_uri`) is not decoded.
    doc.setLocationURI(f"file:{source.resolve()}")
    return doc, label


def _read_failures(doc: libsbml.SBMLDocument) -> list[libsbml.SBMLError]:
    """Get the errors which mean that a document could not be read.

    These are the errors of severity error or fatal which the file system or
    the XML parser reported: a file which cannot be opened, or content which
    is not well-formed XML. The document libsbml returns for them is empty
    or truncated. The errors of the SBML content, e.g. an attribute which an
    element does not have, are not among them: the document was read and
    what is wrong with it is for the validation to report.

    Args:
        doc: the document as libsbml read it

    Returns:
        the errors which made the document unreadable, empty if it was read
    """
    failures: list[libsbml.SBMLError] = []
    for k in range(doc.getNumErrors()):
        error: libsbml.SBMLError = doc.getError(k)
        if (
            error.getSeverity() >= libsbml.LIBSBML_SEV_ERROR
            and error.getCategory()
            in (libsbml.LIBSBML_CAT_SYSTEM, libsbml.LIBSBML_CAT_XML)
            and error.getErrorId() not in _XML_DECLARATION_ERRORS
        ):
            failures.append(error)
    return failures


def write_sbml(
    doc: libsbml.SBMLDocument,
    filepath: Path | None = None,
    validate: bool = False,
    validation_options: ValidationOptions | None = None,
    program_name: str | None = None,
    program_version: str | None = None,
) -> str | None:
    """Write SBMLDocument to file or string.

    To write the SBML to string use 'filepath=None', which returns the SBML string.

    The file can be validated during writing via the validate flag.

    :param doc: SBMLDocument to write
    :param filepath: output file to write
    :param validate: flag for validation
    :param validation_options: validation flag
    :param program_name: Program name for SBML file
    :param program_version: Program version for SBML file

    :return: None or SBML string

    :raises OSError: if the file could not be written. The parent directory
        of `filepath` is created if it does not exist, which is the one such
        failure a writer can repair; anything else is raised, naming the
        path. A caller who asks for a file and gets none must not be told
        that the model is valid, which is what happened while the result of
        libsbml's writer was ignored: it answers `False` and writes nothing,
        and the validation which follows re-reads the path, gets an empty
        document from a file which is not there and reports it as valid. The
        file is written by python, see `sbmlutils.io.files`, and compressed
        by its suffix as libsbml does (`.gz`, `.bz2`, `.zip`).
    """
    writer = libsbml.SBMLWriter()
    if program_name:
        writer.setProgramName(program_name)
    if program_version:
        writer.setProgramVersion(program_version)

    # write file
    source: str | Path
    sbml_str: str | None = None
    if filepath is None:
        sbml_str = writer.writeSBMLToString(doc)
        source = str(sbml_str)
    else:
        filepath = Path(filepath)
        # serialized by libsbml, written by python: libsbml's writer cannot
        # open a non-ASCII path on Windows
        text: str = writer.writeSBMLToString(doc)
        if not text:
            raise OSError(
                f"SBML could not be written to '{filepath}': libsbml could not "
                f"serialize the document."
            )
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            files.write_text(filepath, text)
        except OSError as err:
            raise OSError(f"SBML could not be written to '{filepath}': {err}") from err
        source = filepath

    # validation
    if validate:
        validate_sbml(
            source=source,
            title=str(source),
            validation_options=validation_options,
        )

    return sbml_str


def validate_sbml(
    source: str | Path,
    validation_options: ValidationOptions | None = None,
    title: str | None = None,
) -> ValidationResult:
    """Check given SBML source.

    Validation reports, it never raises for the content of the source: a
    source which cannot be read as SBML, e.g. malformed XML, gives a result
    with the read errors.

    :param source: SBML path or string
    :param validation_options: options for validation
    :param title: title for validation report (should be filname or model name)
    :return: ValidationResult

    :raises FileNotFoundError: if `source` is no SBML string and no existing file
    """
    if not (isinstance(source, str) and "<sbml" in source) and not files.is_file(
        source
    ):
        raise FileNotFoundError(f"SBML file does not exist: '{_shorten(source)}'")
    doc, _ = _read_document(source)
    return validate_doc(
        doc=doc,
        options=validation_options,
        title=title,
    )


def promote_local_variables(
    doc: libsbml.SBMLDocument, suffix: str = "_promoted"
) -> libsbml.SBMLDocument:
    """Promotes local variables in SBMLDocument.

    Manipulates SBMLDocument in place!

    :param doc: SBMLDocument
    :param suffix: str suffix for promoted SBML
    :return: SBMLDocument with promoted parameters
    """
    model: libsbml.Model | None = doc.getModel()
    if model is None:
        # local parameters live in the kinetic laws of a model
        logger.info("No model in SBMLDocument, no local parameters to promote.")
        return doc
    if model.isSetId():
        model.setId(f"{model.getId()}{suffix}")

    # promote local parameters
    props = libsbml.ConversionProperties()
    props.addOption(
        "promoteLocalParameters", True, "Promotes all Local Parameters to Global ones"
    )
    if doc.convert(props) == libsbml.LIBSBML_OPERATION_SUCCESS:
        logger.info("Promotion of local parameters successful: %s", doc)
    else:
        logger.error("Promotion of local parameters failed: %s", doc)
    return doc
