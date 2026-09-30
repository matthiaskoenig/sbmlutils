"""Merging of SBML models.

The following is a helper function for merging multiple SBML models into
a single model.
"""

import logging
from collections.abc import Mapping
from pathlib import Path

import libsbml

from sbmlutils.comp import comp, flatten_sbml
from sbmlutils.io import read_sbml, validate_sbml, write_sbml
from sbmlutils.validation import ValidationOptions, log_sbml_errors_for_doc

logger = logging.getLogger(__name__)


def merge_models(
    model_paths: Mapping[str, Path | str],
    output_dir: Path | str,
    merged_id: str = "merged",
    flatten: bool = True,
    validate: bool = True,
    validate_input: bool = True,
    validation_options: ValidationOptions | None = None,
    sbml_level: int = 3,
    sbml_version: int = 1,
) -> libsbml.SBMLDocument:
    """Merge SBML models.

    Merges SBML models given in `model_paths` in the `output_dir`.
    Models are provided as dictionary
    {
        'model1_id': model1_path,
        'model2_id': model2_path,
        ...
    }
    The model ids are used as ids for the ExternalModelDefinitions.
    Every model is converted to the SBML level and version of the merged model
    and written as `<model_id>_L3.xml` next to the merged model, which names
    it by its file name. A relative path is relative to the working directory,
    which is never changed.

    The created model is either in SBML L3V1 (default) or SBML L3V2.

    :param model_paths: paths to models
    :param output_dir: existing output directory for merged model
    :param merged_id: model id of the merged model
    :param flatten: flattens the merged model
    :param validate: boolean flag to validate the merged model
    :param validate_input: boolean flag to validate the input models
    :param validation_options: ValidationOptions
    :param sbml_level: SBML Level of the merged model in [3]
    :param sbml_version: SBML Version of the merged model in [1, 2]
    :return: SBMLDocument of the merged models, its location is the written
        merged model, so its external model definitions resolve

    :raises ValueError: if the level and version is not SBML L3V1 or L3V2, or
        a model cannot be converted to it
    :raises OSError: if `output_dir` or a model path does not exist
    """
    if (sbml_level, sbml_version) not in {(3, 1), (3, 2)}:
        raise ValueError(
            f"A comp model is SBML L3V1 or L3V2, not L{sbml_level}V{sbml_version}."
        )
    output_dir = Path(output_dir)
    if not output_dir.exists():
        raise OSError(f"'output_dir' does not exist: {output_dir}")

    # the source of an external model definition is resolved relative to the
    # merged document, which is written into the same directory
    sources: dict[str, str] = {}
    for model_id, model_path in model_paths.items():
        path = Path(model_path)
        if not path.exists():
            raise OSError(f"Path for SBML file does not exist: {path}")

        doc = read_sbml(path)
        if not doc.setLevelAndVersion(sbml_level, sbml_version):
            log_sbml_errors_for_doc(doc)
            raise ValueError(
                f"SBML file cannot be converted to SBML "
                f"L{sbml_level}V{sbml_version}: {path}"
            )
        path_converted: Path = output_dir / f"{model_id}_L3.xml"
        write_sbml(doc, path_converted)
        sources[model_id] = path_converted.name

        if validate_input:
            validate_sbml(
                source=path_converted,
                title=str(path),
                validation_options=validation_options,
            )

    # create comp model
    merged_path = output_dir / f"{merged_id}.xml"
    merged_doc: libsbml.SBMLDocument = _create_merged_doc(
        sources,
        merged_path=merged_path,
        merged_id=merged_id,
        sbml_level=sbml_level,
        sbml_version=sbml_version,
    )

    # write merged doc
    write_sbml(merged_doc, filepath=merged_path)
    # the document as written: libsbml resolves the external model definitions
    # of a document it has read against its location, but the consistency
    # check of the document built in memory does not
    merged_doc = read_sbml(merged_path)
    if validate:
        validate_sbml(
            source=merged_path,
            validation_options=validation_options,
            title=str(merged_path),
        )

    if flatten:
        flat_path = output_dir / f"{merged_id}_flat.xml"
        flatten_sbml(sbml_path=merged_path, sbml_flat_path=flat_path)
        if validate:
            validate_sbml(
                source=flat_path,
                validation_options=validation_options,
                title=str(flat_path),
            )

    return merged_doc


def _create_merged_doc(
    sources: Mapping[str, str],
    merged_path: Path,
    merged_id: str = "merged",
    sbml_level: int = 3,
    sbml_version: int = 1,
) -> libsbml.SBMLDocument:
    """Create a comp model from the sources of its external models.

    Args:
        sources: id of every external model definition and its `comp:source`,
            which is resolved relative to the location of the merged document
        merged_path: path the merged document is written to, its location
        merged_id: model id of the merged model
        sbml_level: SBML level of the merged model
        sbml_version: SBML version of the merged model

    Returns:
        the comp document with a submodel for every external model
    """
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("comp", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    # the form libsbml records for a document read from a file, libsbml does
    # not decode a percent-encoded URI (`Path.as_uri`)
    doc.setLocationURI(f"file:{merged_path.resolve()}")

    model: libsbml.Model = doc.createModel()
    model.setId(merged_id)

    comp_doc: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    comp_model: libsbml.CompModelPlugin = model.getPlugin("comp")

    for emd_id, source in sources.items():
        # create ExternalModelDefinition, without a modelRef it is the main
        # model of the external document, whose id need not be `emd_id`
        emd: libsbml.ExternalModelDefinition = comp.create_ExternalModelDefinition(
            comp_doc, emd_id, source=source
        )

        # add submodel which references the external model definition
        comp.add_submodel_from_emd(comp_model, submodel_id=emd_id, emd=emd)

    return doc
