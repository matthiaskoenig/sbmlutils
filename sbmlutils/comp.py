"""
Utilities for the creation and work with comp models.
Simplifies the port linking, submodel generation, ...

Heavily used in the dynamic FBA simulator.
"""
# TODO: refactor and unify with fbc & factory

from __future__ import print_function, division
import os
import libsbml
import sbmlutils.factory as factory
from sbmlutils.validation import check


# Modeling frameworks
SBO_CONTINOUS_FRAMEWORK = 'SBO:0000293'
SBO_FLUX_BALANCE_FRAMEWORK = 'SBO:0000624'


##########################################################################
# ModelDefinitions
##########################################################################
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
    comp_model = emd.getReferencedModel()
    if comp_model.isSetSBOTerm():
        submodel.setSBOTerm(comp_model.getSBOTerm())
    return submodel


def get_submodel_frameworks(doc):
    """
    Reads the SBO terms of the submodels.
    These are used to distinguish the different frameworks of the submodels.
    :param doc:
    :return:
    """
    frameworks = {}
    # get list of submodels
    model = doc.getModel()
    mplugin = model.getPlugin("comp")

    # model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    for submodel in mplugin.getListOfSubmodels():
        sid = submodel.getId()
        sbo = None
        if submodel.isSetSBOTerm():
            # This is the sbo which is set on the submodel element
            # not the SBO which is set on the model in listOfModels or
            # listOfExternalModels
            sbo = submodel.getSBOTerm()
        frameworks[sid] = {"sid": sid, "modelRef": submodel.getModelRef(), "sbo": sbo}

    return frameworks


##########################################################################
# Ports
##########################################################################
# Ports are stored in an optional child ListOfPorts object, which,  if
# present, must contain one or more Port objects.  All of the Ports
# present in the ListOfPorts collectively define the 'port interface' of
# the Model.

PORT_TYPE_PORT = "port"
PORT_TYPE_INPUT = "input port"
PORT_TYPE_OUTPUT = "output port"


def _create_port(model, pid, name=None, portRef=None, idRef=None, unitRef=None, metaIdRef=None,
                 portType=PORT_TYPE_PORT):
    """ Create port in given model.

    :param model:
    :param pid:
    :param name:
    :param portRef:
    :param idRef:
    :param unitRef:
    :param metaIdRef:
    :param portType:
    :return:
    """
    cmodel = model.getPlugin("comp")
    p = cmodel.createPort()
    p.setId(pid)
    if name is not None:
        p.setName(name)
    if portRef is not None:
        p.setPortRef(portRef)
    if idRef is not None:
        p.setIdRef(idRef)
    if unitRef is not None:
        unit_str = factory.get_unit_string(unitRef)
        res = p.setUnitRef(unit_str)
    if metaIdRef is not None:
        p.setMetaIdRef(metaIdRef)
    if portType == PORT_TYPE_PORT:
        # SBO:0000599 - port
        p.setSBOTerm(599)
    elif portType == PORT_TYPE_INPUT:
        # SBO:0000600 - input port
        p.setSBOTerm(600)
    elif portType == PORT_TYPE_OUTPUT:
        # SBO:0000601 - output port
        p.setSBOTerm(601)

    return p

##########################################################################
# Replacement helpers
##########################################################################
SBASE_REF_TYPE_PORT = "portRef"
SBASE_REF_TYPE_ID = "idRef"
SBASE_REF_TYPE_UNIT = "unitRef"
SBASE_REF_TYPE_METAID = "metIdRef"


def replace_elements(model, sid, ref_type, replaced_elements):
    """ Replace elements in comp.

    :param model:
    :param sid:
    :param ref_type:
    :param replaced_elements:
    :return:
    """
    for submodel, rep_ids in replaced_elements.iteritems():
        for rep_id in rep_ids:
            _create_replaced_element(model, sid, submodel, rep_id, ref_type=ref_type)


def replace_element_in_submodels(model, sid, ref_type, submodels):
    """ Replace elements submodels with the identical id.

    For instance to replace all the units in the submodels.

    :param model:
    :param sid:
    :param ref_type:
    :param submodels:
    :return:
    """
    for submodel in submodels:
        _create_replaced_element(model, sid, submodel, sid, ref_type=ref_type)


def _create_replaced_element(model, sid, submodel, replaced_id, ref_type):
    """ Create a replaced element.

    :param model:
    :param sid:
    :param submodel:
    :param replaced_id:
    :param ref_type:
    :return:
    """
    eplugin = _get_eplugin_by_sid(model, sid)

    # print(sid, '--rep-->', submodel, ':', replaced_id)
    rep_element = eplugin.createReplacedElement()
    rep_element.setSubmodelRef(submodel)
    _set_ref(rep_element, ref_id=replaced_id, ref_type=ref_type)

    return rep_element


def replaced_by(model, sid, ref_type, submodel, replaced_by):
    """
    The element with sid in the model is replaced by the
    replacing_id in the submodel with submodel_id.

    :param model:
    :param sid:
    :param ref_type:
    :param submodel:
    :param replaced_by:
    :return:
    """
    eplugin = _get_eplugin_by_sid(model=model, sid=sid)
    rby = eplugin.createReplacedBy()
    rby.setSubmodelRef(submodel)
    _set_ref(object=rby, ref_id=replaced_by, ref_type=ref_type)


def _get_eplugin_by_sid(model, sid):
    """ Gets the comp plugin by sid.

    :param model: SBMLModel instance
    :param sid: SBase id of object
    :return:
    """
    e = model.getElementBySId(sid)
    if not e:
        e = model.getUnitDefinition(sid)
    eplugin = e.getPlugin("comp")
    return eplugin


def _set_ref(object, ref_id, ref_type):
    """
    Sets the reference for given reference type in the object.
    Objects can be
        ReplacedBy
        ReplacedElement
    """
    if ref_type == SBASE_REF_TYPE_ID:
        object.setIdRef(ref_id)
    elif ref_type == SBASE_REF_TYPE_UNIT:
        object.setUnitRef(ref_id)
    elif ref_type == SBASE_REF_TYPE_PORT:
        object.setPortRef(ref_id)
    elif ref_type == SBASE_REF_TYPE_METAID:
        object.setMetaIdRef(ref_id)


##########################################################################
# flatten model
##########################################################################
def flattenSBMLFile(sbml_path, leave_ports=True, output_path=None):
    """ Flatten given SBML file.

    :param sbml_path:
    :param leave_ports:
    :param output_path:
    :return:
    """
    print('-> flattenSBMLFile: ', sbml_path)
    # necessary to change the working directory to the sbml file directory
    # to resolve relative links to external model definitions.
    working_dir = os.getcwd()
    sbml_dir = os.path.dirname(sbml_path)
    os.chdir(sbml_dir)

    reader = libsbml.SBMLReader()
    check(reader, 'create an SBMLReader object.')
    doc = reader.readSBML(sbml_path)
    flat_doc = flattenSBMLDocument(doc, leave_ports=leave_ports, output_path=output_path)

    # change back the working dir
    os.chdir(working_dir)

    return flat_doc


def flattenSBMLDocument(doc, leave_ports=True, output_path=None):
    """ Flatten the given SBMLDocument.

    :param doc: SBMLDocument to flatten.
    :type doc: SBMLDocument
    :return:
    :rtype: SBMLDocument
    """
    print('-> flattenSBMLDocument')

    Nerrors = doc.getNumErrors()
    if Nerrors > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            # Handle case of unreadable file here.
            doc.printErrors()
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            # Handle case of other file error here.
            doc.printErrors()
        else:
            # Handle other error cases here.
            doc.printErrors()

    # converter options
    props = libsbml.ConversionProperties()
    props.addOption("flatten comp", True)  # Invokes CompFlatteningConverter
    props.addOption("leave_ports", leave_ports)  # Indicates whether to leave ports

    # convert
    result = doc.convert(props)
    if result != libsbml.LIBSBML_OPERATION_SUCCESS:
        doc.printErrors()
        return

    if output_path is not None:
        # Write the results to the output file.
        writer = libsbml.SBMLWriter()
        check(writer, 'create an SBMLWriter object.')
        writer.writeSBML(doc, output_path)
        print("Flattened model written to {}".format(output_path))

    return doc
