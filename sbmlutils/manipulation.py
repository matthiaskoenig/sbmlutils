"""
Functions for model manipulation.
Like model merging.

"""
from __future__ import print_function, division
import os
import logging
import warnings
from pprint import pprint
import libsbml

from sbmlutils import comp
from sbmlutils import validation

def create_merged_doc(model_paths):
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
    model.setId('combined_model')
    
    # comp plugin
    comp_doc = doc.getPlugin("comp")
    comp_model = model.getPlugin("comp")

    for emd_id, path in model_paths.iteritems():        
        # create ExternalModelDefinitions
        emd = comp.create_ExternalModelDefinition(comp_doc, emd_id, source=path)
        # add submodel which references the external model definitions
        
        comp.add_submodel_from_emd(comp_model, submodel_id=emd_id, emd=emd)
    
    return doc

def merge_models(model_paths, validate=False):
    """ Merge models in model path.

    :param model_paths:
    :return:
    """
    # necessary to convert models to SBML L3V1, unfortunately many biomodels/models
    # only L2V?, so additional step necessary
    for mid, path in model_paths.iteritems():
        if not os.path.exists(path):
            logging.error('Path for SBML file does not exist: {}'.format(path))

        path_L3 = "{}_L3.xml".format(mid)
        doc = libsbml.readSBMLFromFile(path)
        if doc.getLevel() < 3:
            doc.setLevelAndVersion(3, 1)
        libsbml.writeSBMLToFile(doc, path_L3)
        model_paths[mid] = path_L3

    if validate is True:
        for path in model_paths:
            validation.check_sbml(path, name=path)

    # create comp model
    merged_doc = create_merged_doc(model_paths)
    if validate is True:
        validation.check_sbml(path, name=path)

    return merged_doc



################################################################
if __name__ == "__main__":
    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = ["BIOMD000000000{}".format(k) for k in range(1,5)]
    model_paths = dict(zip(model_ids, ["{}.xml".format(mid) for mid in model_ids]))
    pprint(model_paths)

    doc = merge_models(model_paths)

    # write comp model
    libsbml.writeSBMLToFile(doc, 'combined_model.xml')
    # flatten the model
    doc_flat = comp.flattenSBMLDocument(doc)
    libsbml.writeSBMLToFile(doc_flat, 'combined_model_flat.xml')



