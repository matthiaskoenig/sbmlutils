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
from sbmlutils.io import read_sbml, write_sbml


logger = logging.getLogger(__name__)

SBML_LEVEL = 3
SBML_VERSION = 1
SBML_COMP_VERSION = 1


def merge_models(
    model_paths: Dict[str, Path],
    out_dir: Path = None,
    merged_id: str = "merged",
    validate: bool = True,
) -> libsbml.SBMLDocument:
    """Merge models in model path.

    All models must exist in the same subfolder.
    Relative paths are set in the merged models.

    Output directory must exist.

    :param model_paths: absolute paths to models
    :return:
    """
    # necessary to convert models to SBML L3V1
    cur_dir = os.getcwd()
    os.chdir(out_dir)

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
        path_L3 = out_dir / f"{model_id}_L3.xml"
        doc = read_sbml(path_L3)
        if doc.getLevel() < SBML_LEVEL:
            doc.setLevelAndVersion(SBML_LEVEL, SBML_VERSION)
        write_sbml(doc, path_L3)
        model_paths[model_id] = path_L3

    if validate is True:
        for path in model_paths:
            validation.check_sbml(path, name=path)

    # create comp model
    merged_doc = create_merged_doc(
        model_paths, merged_id=merged_id
    )  # type: libsbml.SBMLDocument
    if validate is True:
        validation.check_sbml(path, name=path)

    # write merged doc
    f_out = os.path.join(out_dir, "{}.xml".format(merged_id))
    libsbml.writeSBMLToFile(merged_doc, f_out)

    os.chdir(cur_dir)
    return merged_doc


def create_merged_doc(model_paths, merged_id="merged"):
    """
    Create a comp model from the given model paths.

    Warning: This only works if all models are in the same directory.
    """
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("comp", 1)
    doc = libsbml.SBMLDocument(sbmlns)  # type: libsbml.SBMLDocument
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()  # type: libsbml.Model
    model.setId(merged_id)

    # comp plugin
    comp_doc = doc.getPlugin("comp")  # type: libsbml.CompSBMLDocumentPlugin
    comp_model = model.getPlugin("comp")  # type: libsbml.CompModelPlugin

    for emd_id, path in model_paths.items():
        # create ExternalModelDefinitions
        emd = comp.create_ExternalModelDefinition(
            comp_doc, emd_id, source=path
        )  # type: libsbml.ExternalModelDefinition

        # add submodel which references the external model definitions
        comp.add_submodel_from_emd(comp_model, submodel_id=emd_id, emd=emd)

    return doc
