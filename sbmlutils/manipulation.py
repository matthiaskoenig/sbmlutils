"""
Functions for model manipulation.
Like model merging.

"""
from __future__ import print_function, division
from six import iteritems
import os
import logging
import warnings
from pprint import pprint
import libsbml
import tempfile

from sbmlutils import comp
from sbmlutils import validation

SBML_LEVEL = 3
SBML_VERSION = 1
SBML_COMP_VERSION = 1


def merge_models(model_paths, out_dir=None, merged_id="merged", validate=True):
    """ Merge models in model path.
    All models must be in the same subfolder.
    Relative paths are set in the merged models.
    
    Output directory must exist.

    :param model_paths: absolute paths to models
    :return:
    """
    # necessary to convert models to SBML L3V1

    # FIXME: the path should not be changed by functions (this will create problems if run concurrently)
    cur_dir = os.getcwd()
    os.chdir(out_dir)

    base_dir = None
    for model_id, path in iteritems(model_paths):
        if not os.path.exists(path):
            logging.error('Path for SBML file does not exist: {}'.format(path))

        # get base dir of all model files from first file
        if base_dir is None:
            base_dir = os.path.dirname(path)
        else:
            new_dir = os.path.dirname(path)
            if new_dir != base_dir:
                raise ValueError('All SBML files for merging must be in same directory: {} != {}'.format(
                    new_dir, base_dir))

        # convert to L3V1
        path_L3 = os.path.join(out_dir, "{}_L3.xml".format(model_id))
        doc = libsbml.readSBMLFromFile(path)
        if doc.getLevel() < SBML_LEVEL:
            doc.setLevelAndVersion(SBML_LEVEL, SBML_VERSION)
        libsbml.writeSBMLToFile(doc, path_L3)
        model_paths[model_id] = path_L3

    if validate is True:
        for path in model_paths:
            validation.check_sbml(path, name=path)

    # create comp model
    merged_doc = create_merged_doc(model_paths, merged_id=merged_id)
    if validate is True:
        validation.check_sbml(path, name=path)

    # write merged doc
    f_out = os.path.join(out_dir, '{}.xml'.format(merged_id))
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
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()
    model.setId(merged_id)

    # comp plugin
    comp_doc = doc.getPlugin("comp")
    comp_model = model.getPlugin("comp")

    for emd_id, path in iteritems(model_paths):
        # create ExternalModelDefinitions
        emd = comp.create_ExternalModelDefinition(comp_doc, emd_id, source=path)
        # add submodel which references the external model definitions

        comp.add_submodel_from_emd(comp_model, submodel_id=emd_id, emd=emd)

    return doc