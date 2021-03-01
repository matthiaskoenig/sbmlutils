"""
Functions for SBML model manipulation.

These functions take existing SBML model(s) and provide common manipulations.
For example merging of models or promoting of local parameters.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Iterable

import libsbml

from sbmlutils import validation
from sbmlutils.comp import comp
from sbmlutils.io import read_sbml, validate_sbml, write_sbml


logger = logging.getLogger(__name__)

SBML_LEVEL = 3
SBML_VERSION = 1
SBML_COMP_VERSION = 1


def merge_models(
    model_paths: Dict[str, Path],
    output_dir: Path = None,
    merged_id: str = "merged",
    validate: bool = True,
) -> libsbml.SBMLDocument:
    """Merge models in model path.

    All models must exist in the same subfolder.
    Relative paths are set in the merged models.

    Output directory must exist.

    :param output_dir:
    :param merged_id:
    :param validate:
    :param model_paths: absolute paths to models
    :return:
    """
    # necessary to convert models to SBML L3V1
    cur_dir = os.getcwd()
    os.chdir(str(output_dir))

    base_dir = None
    for model_id, path in model_paths.items():
        if path.exists():
            logging.error(f"Path for SBML file does not exist: {path}")

        # get base dir of all model files from first file
        if base_dir is None:
            base_dir = path.parent
        else:
            new_dir = path.parent
            if not new_dir != base_dir:
                raise IOError(
                    f"All SBML files for merging must be in same "
                    f"directory: {new_dir} != {base_dir}"
                )

        # convert to L3V1
        path_L3: Path = output_dir / f"{model_id}_L3.xml"  # type: ignore
        doc = read_sbml(path_L3)
        if doc.getLevel() < SBML_LEVEL:
            doc.setLevelAndVersion(SBML_LEVEL, SBML_VERSION)
        write_sbml(doc, path_L3)
        model_paths[model_id] = path_L3

    if validate is True:
        for path in model_paths:  # type: ignore
            validate_sbml(source=path, name=str(path))

    # create comp model
    merged_doc: libsbml.SBMLDocument = create_merged_doc(
        model_paths, merged_id=merged_id
    )
    if validate is True:
        validate_sbml(path, name=str(path))

    # write merged doc
    f_out = os.path.join(output_dir, f"{merged_id}.xml")  # type: ignore
    libsbml.writeSBMLToFile(merged_doc, f_out)

    os.chdir(cur_dir)
    return merged_doc


def create_merged_doc(
    model_paths: Dict[str, Path], merged_id: str = "merged"
) -> libsbml.SBMLDocument:
    """Create a comp model from given model paths.

    Warning: This only works if all models are in the same directory.

    :param model_paths: Dictionary of id:path
    :param merged_id:
    :return:
    """
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("comp", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model: libsbml.Model = doc.createModel()
    model.setId(merged_id)

    # comp plugin
    comp_doc: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    comp_model: libsbml.CompModelPlugin = model.getPlugin("comp")

    for emd_id, path in model_paths.items():
        # create ExternalModelDefinitions
        emd: libsbml.ExternalModelDefinition = comp.create_ExternalModelDefinition(
            comp_doc, emd_id, source=str(path)
        )

        # add submodel which references the external model definitions
        comp.add_submodel_from_emd(comp_model, submodel_id=emd_id, emd=emd)

    return doc
