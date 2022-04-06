"""Merging of SBML models.

The following is a helper function for merging multiple SBML models into
a single model.
"""
import os
from pathlib import Path
from typing import Dict, Iterable, List, Union

import libsbml

from sbmlutils import log, validation
from sbmlutils.comp import comp, flatten_sbml
from sbmlutils.io import read_sbml, validate_sbml, write_sbml
from sbmlutils.test import TESTDATA_DIR


logger = log.get_logger(__name__)


def merge_models(
    model_paths: Dict[str, Path],
    output_dir: Path,
    merged_id: str = "merged",
    flatten: bool = True,
    validate: bool = True,
    validate_input: bool = True,
    units_consistency: bool = False,
    modeling_practice: bool = False,
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
    Relative paths are set in the merged models.

    The created model is either in SBML L3V1 (default) or SBML L3V2.

    :param model_paths: absolute paths to models
    :param output_dir: output directory for merged model
    :param merged_id: model id of the merged model
    :param flatten: flattens the merged model
    :param validate: boolean flag to validate the merged model
    :param validate_input: boolean flag to validate the input models
    :param units_consistency: boolean flag to check units consistency
    :param modeling_practice: boolean flag to check modeling practise
    :param sbml_level: SBML Level of the merged model in [3]
    :param sbml_version: SBML Version of the merged model in [1, 2]
    :return: SBMLDocument of the merged models
    """
    # necessary to convert models to SBML L3V1
    if isinstance(output_dir, str):
        logger.warning(f"'output_dir' should be a Path but: '{type(output_dir)}'")
        output_dir = Path(output_dir)
    if not output_dir.exists():
        raise IOError(f"'output_dir' does not exist: {output_dir}")

    validate_kwargs: Dict[str, bool] = {
        "units_consistency": units_consistency,
        "modeling_practice": modeling_practice,
    }

    for model_id, path in model_paths.items():
        if not path.exists():
            raise IOError(f"Path for SBML file does not exist: {path}")
        if isinstance(path, str):
            path = Path(path)

        # convert to L3V1
        path_L3: Path = output_dir / f"{model_id}_L3.xml"
        doc = read_sbml(path)
        doc.setLevelAndVersion(sbml_level, sbml_version)
        write_sbml(doc, path_L3)
        model_paths[model_id] = path_L3

        if validate_input:
            validate_sbml(
                source=path_L3,
                name=str(path),
                **validate_kwargs,
            )

    # create comp model
    cur_dir = os.getcwd()
    os.chdir(str(output_dir))
    merged_doc: libsbml.SBMLDocument = _create_merged_doc(
        model_paths, merged_id=merged_id
    )
    os.chdir(cur_dir)

    # write merged doc
    merged_path = output_dir / f"{merged_id}.xml"
    write_sbml(merged_doc, filepath=merged_path)
    if validate:
        validate_sbml(merged_path, name=str(merged_path), **validate_kwargs)

    if flatten:
        flat_path = output_dir / f"{merged_id}_flat.xml"
        flatten_sbml(sbml_path=merged_path, sbml_flat_path=flat_path)
        if validate:
            validate_sbml(flat_path, name=str(flat_path), **validate_kwargs)

    return merged_doc


def _create_merged_doc(
    model_paths: Dict[str, Path],
    merged_id: str = "merged",
    sbml_level: int = 3,
    sbml_version: int = 1,
) -> libsbml.SBMLDocument:
    """Create a comp model from given model paths.

    Warning: This only works if all models are in the same directory.
    """
    sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)
    sbmlns.addPackageNamespace("comp", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    model: libsbml.Model = doc.createModel()
    model.setId(merged_id)

    comp_doc: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    comp_model: libsbml.CompModelPlugin = model.getPlugin("comp")

    for emd_id, path in model_paths.items():
        # create ExternalModelDefinition
        emd: libsbml.ExternalModelDefinition = comp.create_ExternalModelDefinition(
            comp_doc, emd_id, source=str(path)
        )

        # add submodel which references the external model definition
        comp.add_submodel_from_emd(comp_model, submodel_id=emd_id, emd=emd)

    return doc
