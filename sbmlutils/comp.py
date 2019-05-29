"""
Utilities for the creation and work with comp models.
Simplifies the port linking, submodel generation, ...

Heavily used in the dynamic FBA simulator. Mainly in the model creation
process. But the flattening parts also during the simulation
of the dynamic FBA models.
"""

import os
import warnings
import logging
import time
import libsbml

from sbmlutils.logutils import bcolors

import sbmlutils.factory as factory
import sbmlutils.validation as validation
from sbmlutils.validation import check

# Modeling frameworks
SBO_CONTINOUS_FRAMEWORK = 'SBO:0000293'
SBO_FLUX_BALANCE_FRAMEWORK = 'SBO:0000624'


##########################################################################
# ModelDefinitions
##########################################################################
def create_ExternalModelDefinition(doc_comp, emd_id, source):
    """ Create comp ExternalModelDefinition.

    :param doc_comp: SBMLDocument comp plugin
    :param emd_id: id of external model definition
    :param source: source
    :return:
    """
    extdef = doc_comp.createExternalModelDefinition()
    extdef.setId(emd_id)
    extdef.setName(emd_id)
    extdef.setModelRef(emd_id)
    extdef.setSource(source)
    return extdef


def add_submodel_from_emd(model_comp: libsbml.CompModelPlugin, submodel_id,
                          emd: libsbml.ExternalModelDefinition):
    """ Adds submodel to the model from given ExternalModelDefinition.

    :param model_comp: Model comp plugin
    :param submodel_id:
    :param emd:
    :return:
    """

    model_ref = emd.getModelRef()
    submodel = model_comp.createSubmodel()
    submodel.setId(submodel_id)
    submodel.setModelRef(model_ref)

    model_comp = emd.getReferencedModel()
    if model_comp and model_comp.isSetSBOTerm():
        submodel.setSBOTerm(model_comp.getSBOTerm())
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
# ExternalModelDefinitions
##########################################################################
class ExternalModelDefinition(factory.Sbase):

    def __init__(self, sid, source, modelRef, md5=None, name=None, sboTerm=None, metaId=None):
        """ Create an ExternalModelDefinitions.
        """
        super(ExternalModelDefinition, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.source = source
        self.modelRef = modelRef
        self.md5 = md5

    def create_sbml(self, model):
        doc = model.getSBMLDocument()
        cdoc = doc.getPlugin("comp")
        extdef = cdoc.createExternalModelDefinition()
        self.set_fields(extdef)
        return extdef

        return p

    def set_fields(self, obj):
        super(ExternalModelDefinition, self).set_fields(obj)
        obj.setModelRef(self.modelRef)
        obj.setSource(self.source)
        if self.md5 is not None:
            obj.setMd5(self.md5)


##########################################################################
# Submodel
##########################################################################
class Submodel(factory.Sbase):

    def __init__(self, sid, modelRef=None, timeConversionFactor=None, extentConversionFactor=None, name=None, sboTerm=None, metaId=None):
        """ Create an ExternalModelDefinitions.
        """
        super(Submodel, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.modelRef = modelRef
        self.timeConversionFactor = timeConversionFactor
        self.extentConversionFactor = extentConversionFactor

    def create_sbml(self, model):
        cmodel = model.getPlugin("comp")
        submodel = cmodel.createSubmodel()
        self.set_fields(submodel)

        submodel.setModelRef(self.modelRef)
        if self.timeConversionFactor:
            submodel.setTimeConversionFactor(self.timeConversionFactor)
        if self.extentConversionFactor:
            submodel.setExtentConversionFactor(self.extentConversionFactor)

        return submodel

    def set_fields(self, obj):
        super(Submodel, self).set_fields(obj)


##########################################################################
# SBaseRef
##########################################################################
class SbaseRef(factory.Sbase):

    def __init__(self, sid, portRef=None, idRef=None, unitRef=None, metaIdRef=None, name=None, sboTerm=None, metaId=None):
        """ Create an SBaseRef.
        """
        super(SbaseRef, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.portRef = portRef
        self.idRef = idRef
        self.unitRef = unitRef
        self.metaIdRef = metaIdRef

    def set_fields(self, obj):
        super(SbaseRef, self).set_fields(obj)

        obj.setId(self.sid)
        if self.portRef is not None:
            obj.setPortRef(self.portRef)
        if self.idRef is not None:
            obj.setIdRef(self.idRef)
        if self.unitRef is not None:
            unit_str = factory.Unit.get_unit_string(self.unitRef)
            obj.setUnitRef(unit_str)
        if self.metaIdRef is not None:
            obj.setMetaIdRef(self.metaIdRef)


##########################################################################
# ReplacedElements
##########################################################################
class ReplacedElement(SbaseRef):

    def __init__(self, sid, elementRef, submodelRef, deletion=None, conversionFactor=None, portRef=None, idRef=None, unitRef=None, metaIdRef=None, name=None, sboTerm=None,
                 metaId=None):
        """

        :param sid:
        :param elementRef: sid of the element on which the ReplacedElement is generated.
        :param submodelRef:
        :param deletion:
        :param conversionFactor:
        :param portRef:
        :param idRef:
        :param unitRef:
        :param metaIdRef:
        :param name:
        :param sboTerm:
        :param metaId:
        """
        """ Create a ReplacedElement. """
        super(ReplacedElement, self).__init__(sid=sid, portRef=portRef, idRef=idRef, unitRef=unitRef, metaIdRef=metaIdRef,
                                              name=name, sboTerm=sboTerm, metaId=metaId)
        self.elementRef = elementRef
        self.submodelRef = submodelRef
        self.deletion = deletion
        self.conversionFactor = conversionFactor

    def create_sbml(self, model):

        # resolve port element
        e = model.getElementBySId(self.elementRef)
        if not e:
            # fallback to units (only working if no name shadowing)
            e = model.getUnitDefinition(self.elementRef)
            if not e:
                raise ValueError("Neither SBML element nor UnitDefinition found for elementRef: {}".format(self.elementRef))

        eplugin = e.getPlugin("comp")
        obj = eplugin.createReplacedElement()
        self.set_fields(obj)

        return obj

    def set_fields(self, obj):
        super(ReplacedElement, self).set_fields(obj)
        obj.setSubmodelRef(self.submodelRef)
        if self.deletion:
            obj.setDeletion(self.deletion)
        if self.conversionFactor:
            obj.setConversionFactor(self.conversionFactor)


##########################################################################
# Deletions
##########################################################################
class Deletion(SbaseRef):

    def __init__(self, sid, submodelRef, portRef=None, idRef=None,
                 unitRef=None, metaIdRef=None, name=None,
                 sboTerm=None, metaId=None):
        """ Create a Deletion. """
        super(Deletion, self).__init__(sid=sid, portRef=portRef, idRef=idRef,
                                       unitRef=unitRef, metaIdRef=metaIdRef,
                                       name=name, sboTerm=sboTerm,
                                       metaId=metaId)
        self.submodelRef = submodelRef

    def create_sbml(self, model):

        # Deletions for submodels
        cmodel = model.getPlugin("comp")  # type: libsbml.CompModelPlugin
        submodel = cmodel.getSubmodel(self.submodelRef)  # type: libsbml.Submodel
        deletion = submodel.createDeletion()  # type: libsbml.Deletion
        self.set_fields(deletion)

        return deletion

    def set_fields(self, obj):
        super(Deletion, self).set_fields(obj)

##########################################################################
# Ports
##########################################################################
# Ports are stored in an optional child ListOfPorts object, which, if
# present, must contain one or more Port objects.  All of the Ports
# present in the ListOfPorts collectively define the 'port interface' of
# the Model.
PORT_TYPE_PORT = "port"
PORT_TYPE_INPUT = "input port"
PORT_TYPE_OUTPUT = "output port"


class Port(SbaseRef):

    def __init__(self, sid, portRef=None, idRef=None, unitRef=None, metaIdRef=None, portType=PORT_TYPE_PORT, name=None, sboTerm=None, metaId=None):
        """ Create a port.
        """
        super(Port, self).__init__(sid=sid, portRef=portRef, idRef=idRef, unitRef=unitRef, metaIdRef=metaIdRef,
                                   name=name, sboTerm=sboTerm, metaId=metaId)
        self.portType = portType

    def create_sbml(self, model):
        cmodel = model.getPlugin("comp")
        p = cmodel.createPort()
        self.set_fields(p)

        if self.sboTerm is None:
            if self.portType == PORT_TYPE_PORT:
                # SBO:0000599 - port
                sbo = 599
            elif self.portType == PORT_TYPE_INPUT:
                # SBO:0000600 - input port
                sbo = 600
            elif self.portType == PORT_TYPE_OUTPUT:
                # SBO:0000601 - output port
                sbo = 601
            p.setSBOTerm(sbo)

        return p

    def set_fields(self, obj):
        super(Port, self).set_fields(obj)


def create_ports(model, portRefs=None, idRefs=None, unitRefs=None, metaIdRefs=None,
                 portType=PORT_TYPE_PORT, suffix="_port"):
    """ Create ports given model.
    Helper function to create port creation.

    :param model: SBML model
    :param portRefs: dict of the form {pid:portRef}
    :param idRefs: dict of the form {pid:idRef}
    :param unitRefs: dict of the form {pid:unitRef}
    :param metaIdRes: dict of the form {pid:metaIdRef}
    :return:
    :rtype: ports
    """
    ports = []
    if portRefs is not None:
        ptype = "portRef"
        data = portRefs
    elif idRefs is not None:
        ptype = "idRef"
        data = idRefs
    elif unitRefs is not None:
        ptype = "unitRef"
        data = unitRefs
    elif metaIdRefs is not None:
        ptype = "metaIdRef"
        data = metaIdRefs

    # dictionary, port ids are provided
    if type(data) == dict:
        for pid, ref in data.items():
            kwargs = {'pid': pid, ptype: ref}
            ports.append(
                _create_port(model, portType=portType, **kwargs)
            )

    # only a list of references, port ids created via suffix appending
    elif type(data) in [list, tuple]:
        for ref in data:
            pid = ref + suffix
            kwargs = {'pid': pid, ptype: ref}
            ports.append(
                _create_port(model, portType=portType, **kwargs)
            )

    return ports


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
    ref = None
    if portRef is not None:
        p.setPortRef(portRef)
        ref = portRef
    if idRef is not None:
        p.setIdRef(idRef)
        ref = idRef
    if unitRef is not None:
        unit_str = factory.get_unit_string(unitRef)
        p.setUnitRef(unit_str)
        ref = unit_str
    if metaIdRef is not None:
        p.setMetaIdRef(metaIdRef)
        ref = metaIdRef
    if name is None and ref is not None:
        p.setName("port {}".format(ref))
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
    for submodel, rep_ids in replaced_elements.items():
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


def comp_delete(model):
    """ Delete elements from top model.

    :param model:
    :return:
    """
    pass


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
def flattenSBMLFile(sbml_path, leave_ports=True, output_path=None, suffix='_flat'):
    """ Flatten given SBML file.

    :param sbml_path:
    :param leave_ports:
    :param output_path:
    :param suffix to add to model id
    :return:
    """
    # necessary to change the working directory to the sbml file directory
    # to resolve relative links to external model definitions.
    working_dir = os.getcwd()
    sbml_dir = os.path.dirname(sbml_path)
    os.chdir(sbml_dir)

    reader = libsbml.SBMLReader()
    check(reader, 'create an SBMLReader object.')
    doc = reader.readSBML(sbml_path)
    flat_doc = flattenSBMLDocument(doc, leave_ports=leave_ports, output_path=output_path, suffix=suffix)

    # change back the working dir
    os.chdir(working_dir)

    return flat_doc


def flattenSBMLDocument(doc, leave_ports=True, output_path=None, suffix='_flat'):
    """ Flatten the given SBMLDocument.

    Validation should be performed before the flattening and is not part
    of the flattening routine.

    :param doc: SBMLDocument to flatten.
    :type doc: SBMLDocument
    :return:
    :rtype: SBMLDocument
    """
    Nerrors = doc.getNumErrors()
    if Nerrors > 0:
        if doc.getError(0).getErrorId() == libsbml.XMLFileUnreadable:
            # Handle case of unreadable file here.
            logging.error("SBML error in doc: libsbml.XMLFileUnreadable")
        elif doc.getError(0).getErrorId() == libsbml.XMLFileOperationError:
            # Handle case of other file error here.
            logging.error("SBML error in doc: libsbml.XMLFileOperationError")
        else:
            # Handle other error cases here.
            logging.error("SBML errors in doc, see SBMLDocument error log.")

    # converter options
    props = libsbml.ConversionProperties()
    props.addOption("flatten comp", True)  # Invokes CompFlatteningConverter
    props.addOption("leave_ports", leave_ports)  # Indicates whether to leave ports

    # flatten
    current = time.clock()
    result = doc.convert(props)
    flattened_status = (result == libsbml.LIBSBML_OPERATION_SUCCESS)

    lines = [
        '',
        '-' * 120,
        str(doc),
        "{:<25}: {}".format("flattened", str(flattened_status).upper()),
        "{:<25}: {:.3f}".format("flatten time (ms)", time.clock() - current),
        '-' * 120,
    ]
    info = bcolors.BOLD + "\n".join(lines) + bcolors.ENDC

    if flattened_status:
        logging.info(bcolors.OKGREEN + info + bcolors.ENDC)
    else:
        logging.error(bcolors.FAIL + info + bcolors.ENDC)
        raise ValueError("SBML could not be flattend due to errors in the SBMLDocument.")

    if suffix is not None:
        model = doc.getModel()
        if model is not None:
            model.setId(model.getId() + suffix)
            if model.isSetName():
                model.setName(model.getName() + suffix)

    if output_path is not None:
        # Write the results to the output file.
        libsbml.writeSBMLToFile(doc, output_path)
        logging.info("Flattened model written to {}".format(output_path))

    return doc


##########################################################################
# ExternalModelDefinitions & Submodels
##########################################################################

def flattenExternalModelDefinitions(doc, validate=False):
    """ Converts all ExternalModelDefinitions to ModelDefinitions.

    I.e. the definition of models in external files are read
    and directly included in the top model. The resulting
    comp model consists than only of a single file.

    The model refs in the submodel do not change in the process,
    so no need to update the submodels.

    :param doc: SBMLDocument
    :return: SBMLDocument with ExternalModelDefinitions replaced
    """
    logging.debug('* flattenExternalModelDefinitions')

    # FIXME: handle multiple levels of hierarchies. Recursively to handle the ExternalModelDefinitions of submodels
    warnings.warn("flattenExternalModelDefinitions does not work recursively!")
    warnings.warn("flattenExternalModelDefinitions: THIS DOES NOT WORK - ONLY USE IF YOU KNOW WHAT YOU ARE DOING")

    comp_doc = doc.getPlugin("comp")
    if comp_doc is None:
        logging.warning("Model is not a comp model, no ExternalModelDefinitions")
        return doc
    emd_list = comp_doc.getListOfExternalModelDefinitions()
    if (emd_list is None) or (len(emd_list) == 0):
        # no ExternalModelDefinitions
        logging.warning("Model does not contain any ExternalModelDefinitions")
        return doc
    else:
        model = doc.getModel()
        comp_model = model.getPlugin("comp")

        emd_ids = []
        for emd in emd_list:
            logging.debug(emd)
            emd_ids.append(emd.getId())

            # get the model definition from the model
            ref_model = emd.getReferencedModel()

            ref_doc = ref_model.getSBMLDocument()
            # print(ref_model)
            for k in range(ref_doc.getNumPlugins()):
                plugin = ref_doc.getPlugin(k)
                # print(k, plugin)

                # enable the package on the main SBMLDocument
                uri = plugin.getURI()
                prefix = plugin.getPrefix()
                name = plugin.getPackageName()
                doc.enablePackage(uri, prefix, True)

                # print(k, plugin)
                # print(uri, prefix)

            # print("\n")

            # add model definition for model
            md = libsbml.ModelDefinition(ref_model)
            comp_doc.addModelDefinition(md)

        # remove the emds afterwards
        for emd_id in emd_ids:
            # remove the emd from the model
            comp_doc.removeExternalModelDefinition(emd_id)

    # validate
    if validate:
        validation.check_doc(doc)
    return doc


if __name__ == "__main__":
    from sbmlutils.tests import data
    from sbmlutils import sbmlio

    doc = sbmlio.read_sbml(data.DFBA_EMD_SBML)
    doc_no_emd = flattenExternalModelDefinitions(doc, validate=True)
