"""
Utils for the creation and work with comp models.
"""
from __future__ import print_function, division
from validation import check

import factory
import libsbml

# TODO: allow generic arguments the factory function and use them to set
#   metaId, sbo, name, id,

# Modeling frameworks
SBO_CONTINOUS_FRAMEWORK = 'SBO:0000062'
SBO_DISCRETE_FRAMEWORK = 'SBO:0000063'
SBO_FLUX_BALANCE_FRAMEWORK = 'SBO:0000624'


##########################################################################
# ModelDefinitions
##########################################################################
def create_ExternalModelDefinition(mdoc, cid, sbml_file):
    extdef = mdoc.createExternalModelDefinition()
    extdef.setId(cid)
    extdef.setName(cid)
    extdef.setModelRef(cid)
    extdef.setSource(sbml_file)
    return extdef


def add_submodel_from_emd(mplugin, submodel_sid, emd):
    model_ref = emd.getModelRef()
    submodel = mplugin.createSubmodel()
    submodel.setId(submodel_sid)
    submodel.setModelRef(model_ref)
    # copy the SBO term to the submodel

    # ! gets the model belonging the SBASe !
    # model = emd.getModel()
    model = emd.getReferencedModel()
    if model.isSetSBOTerm():
        submodel.setSBOTerm(model.getSBOTerm())
    return submodel


def get_submodel_frameworks(doc):
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


def _create_port(model, pid, name=None, portRef=None, idRef=None, unitRef=None, metaIdRef=None, portType=PORT_TYPE_PORT):
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
        print("set unitRef")
        print(unit_str)
        res = p.setUnitRef(unit_str)
        print(res)
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
    """
    Replace elements in comp.
    """
    for submodel, rep_ids in replaced_elements.iteritems():
        for rep_id in rep_ids:
            _create_replaced_element(model, sid, submodel, rep_id, ref_type=ref_type)


def replace_element_in_submodels(model, sid, ref_type, submodels):
    """
    Replace elements submodels with the identical id.
    For instance to replace all the units in the submodels.
    """
    for submodel in submodels:
        _create_replaced_element(model, sid, submodel, sid, ref_type=ref_type)


def _create_replaced_element(model, sid, submodel, replaced_id, ref_type):
    eplugin = _get_eplugin_by_sid(model, sid)

    print(sid, '--rep-->', submodel, ':', replaced_id)
    rep_element = eplugin.createReplacedElement()
    rep_element.setSubmodelRef(submodel)
    _set_ref(rep_element, ref_id=replaced_id, ref_type=ref_type)

    return rep_element


def replaced_by(model, sid, ref_type, submodel, replaced_by):
    """
    The element with sid in the model is replaced by the
    replacing_id in the submodel with submodel_id.
    """
    eplugin = _get_eplugin_by_sid(model=model, sid=sid)
    rby = eplugin.createReplacedBy()
    rby.setSubmodelRef(submodel)
    _set_ref(object=rby, ref_id=replaced_by, ref_type=ref_type)


def _get_eplugin_by_sid(model, sid):
    """
    Gets the comp plugin by sid.
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
def flattenSBMLFile(sbml_file, leave_ports=True, output_file=None):
    """
    Flatten the given SBML file.
    """
    reader = libsbml.SBMLReader()
    check(reader, 'create an SBMLReader object.')
    doc = reader.readSBML(sbml_file)
    return flattenSBMLDocument(doc, leave_ports=leave_ports, output_file=output_file)


def flattenSBMLDocument(doc, leave_ports=True, output_file=None):
    """ Flatten the given SBMLDocument.

    :param doc: SBMLDocument to flatten.
    :type doc: SBMLDocument
    :return:
    :rtype:
    """

    if doc.getNumErrors() > 0:
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

    if output_file is not None:
        # Write the results to the output file.
        writer = libsbml.SBMLWriter()
        check(writer, 'create an SBMLWriter object.')
        writer.writeSBML(doc, output_file)
        print("Flattened model written to {}".format(output_file))

    return doc