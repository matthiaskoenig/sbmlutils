
# coding: utf-8

# In[14]:

import libsbml
from pprint import pprint
import sys

def create_ExternalModelDefinition(comp_doc, emd_id, source):
    """ Create comp ExternalModelDefinition.

    :param comp_doc: comp plugin
    :param emd_id: id of external model definition
    :param source: source
    :return:
    """
    extdef = comp_doc.createExternalModelDefinition()
    extdef.setId(emd_id)
    extdef.setName(emd_id)
    extdef.setModelRef(emd_id)
    extdef.setSource(source)
    return extdef


def add_submodel_from_emd(comp_model, submodel_id, emd):
    """ Adds submodel to the model from given ExternalModelDefinition.

    :param comp_model:
    :param submodel_id:
    :param emd:
    :return:
    """
    model_ref = emd.getModelRef()
    submodel = comp_model.createSubmodel()
    submodel.setId(submodel_id)
    submodel.setModelRef(model_ref)
    return submodel


def flattenSBMLDocument(doc, leave_ports=True):
    """ Flatten the given SBMLDocument.

    :param doc: SBMLDocument to flatten.
    :type doc: SBMLDocument
    :return:
    :rtype: SBMLDocument
    """    
    # validate
    doc.checkConsistency()
    Nerrors = doc.getNumErrors()
    
    if doc.getNumErrors() > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            # Handle case of unreadable file here.
            doc.printErrors()
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            # Handle case of other file error here.
            doc.printErrors()
        else:            
            # Handle other error cases here.
            stream = libsbml.ostringstream()
            doc.printErrors(stream, 2)
            sys.stdout.write(stream.str())
    
    # converter options
    props = libsbml.ConversionProperties()
    props.addOption("flatten comp", True)  # Invokes CompFlatteningConverter
    props.addOption("leave_ports", leave_ports)  # Indicates whether to leave ports

    # convert
    result = doc.convert(props)
    if result != libsbml.LIBSBML_OPERATION_SUCCESS:
        return None
    
    return doc

def create_comp(model_paths):
    """
    Create the fba model.
    FBA submodel in FBC v2 which uses parameters as flux bounds.
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
        emd = create_ExternalModelDefinition(comp_doc, emd_id, source=path)
        # add submodel which references the external model definitions
        
        add_submodel_from_emd(comp_model, submodel_id=emd_id, emd=emd)
    
    return doc

################################################################
    
# dictionary of ids & paths of models which should be combined
# here we just bring together the first Biomodels
model_ids = ["BIOMD000000000{}".format(k) for k in range(1,5)]
model_paths = dict(zip(model_ids, ["{}.xml".format(mid) for mid in model_ids]))
pprint(model_paths)

# necessary to convert models to SBML L3V1, unfortunately many biomodels/models
# only L2V?, so additional step necessary
for mid, path in model_paths.iteritems():
    path_L3 = "{}_L3.xml".format(mid)
    doc = libsbml.readSBMLFromFile(path)
    if doc.getLevel()<3:
        doc.setLevelAndVersion(3, 1)
    libsbml.writeSBMLToFile(doc, path_L3)
    model_paths[mid] = path_L3


# create comp model
doc = create_comp(model_paths)

###########
# Now you have to define the replacements and replacedBy, ports, ...
# i.e. you want to map components. 
# Your question is only about bringing in one model which the code
# is doing. The interfaces you have to write still.
###########

# write comp model
libsbml.writeSBMLToFile(doc, 'combined_model.xml')
# flatten the model
doc_flat = flattenSBMLDocument(doc)
libsbml.writeSBMLToFile(doc_flat, 'combined_model_flat.xml');


# In[ ]:



