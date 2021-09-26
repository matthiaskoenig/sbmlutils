"""Utilities for the creation and work with comp models.

Simplifies the port linking, submodel generation, ...

Heavily used in the dynamic FBA simulator. Mainly in the model creation
process. But the flattening parts also during the simulation
of the dynamic FBA models.
"""

from typing import Any, Dict, List, Optional

import libsbml

import sbmlutils.factory as factory
from sbmlutils import log


logger = log.get_logger(__name__)


def create_ExternalModelDefinition(
    doc_comp: libsbml.CompSBMLDocumentPlugin, emd_id: str, source: str
) -> libsbml.ExternalModelDefinition:
    """Create comp ExternalModelDefinition.

    :param doc_comp: SBMLDocument comp plugin
    :param emd_id: id of external model definition
    :param source: source
    :return:
    """
    extdef: libsbml.ExternalModelDefinition = doc_comp.createExternalModelDefinition()
    extdef.setId(emd_id)
    extdef.setName(emd_id)
    extdef.setModelRef(emd_id)
    extdef.setSource(source)
    return extdef


def add_submodel_from_emd(
    model_comp: libsbml.CompModelPlugin,
    submodel_id: str,
    emd: libsbml.ExternalModelDefinition,
) -> libsbml.Submodel:
    """Add submodel to the model from given ExternalModelDefinition.

    :param model_comp: Model comp plugin
    :param submodel_id:
    :param emd:
    :return:
    """

    model_ref = emd.getModelRef()
    submodel: libsbml.Submodel = model_comp.createSubmodel()
    submodel.setId(submodel_id)
    submodel.setModelRef(model_ref)

    model_comp = emd.getReferencedModel()
    if model_comp and model_comp.isSetSBOTerm():
        submodel.setSBOTerm(model_comp.getSBOTerm())
    return submodel


def get_submodel_frameworks(doc: libsbml.SBMLDocument) -> Dict[str, Any]:
    """Read the SBO terms of the submodels.

    These are used to distinguish the different frameworks of the submodels.
    :param doc: SBMLDocument
    :return:
    """
    frameworks = {}
    # get list of submodels
    model = doc.getModel()
    mplugin = model.getPlugin("comp")

    # model.setSBOTerm(comp.SBO.CONTINOUS_FRAMEWORK)
    submodel: libsbml.Submodel
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


def create_ports(
    model: libsbml.Model,
    portRefs: Optional[Any] = None,
    idRefs: Optional[Any] = None,
    unitRefs: Optional[Any] = None,
    metaIdRefs: Optional[Any] = None,
    portType: str = factory.PORT_TYPE_PORT,
    suffix: str = "_port",
) -> List[factory.Port]:
    """Create ports for given model.

    Helper function to create port creation.
    :param model: SBML model
    :param portRefs: dict of the form {pid:portRef}
    :param idRefs: dict of the form {pid:idRef}
    :param unitRefs: dict of the form {pid:unitRef}
    :param metaIdRefs: dict of the form {pid:metaIdRef}
    :param portType: type of port
    :param suffix: suffix to use in port generation

    :return:
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
            kwargs = {"pid": pid, ptype: ref}
            ports.append(_create_port(model, portType=portType, **kwargs))

    # only a list of references, port ids created via suffix appending
    elif type(data) in [list, tuple]:
        for ref in data:
            pid = ref + suffix
            kwargs = {"pid": pid, ptype: ref}
            ports.append(_create_port(model, portType=portType, **kwargs))

    return ports


def _create_port(
    model: libsbml.Model,
    pid: str,
    name: Optional[str] = None,
    portRef: Optional[str] = None,
    idRef: Optional[str] = None,
    unitRef: Optional[str] = None,
    metaIdRef: Optional[str] = None,
    portType: str = factory.PORT_TYPE_PORT,
) -> libsbml.Port:
    """Create port in given model."""
    cmodel: libsbml.CompModelPlugin = model.getPlugin("comp")
    p: libsbml.Port = cmodel.createPort()
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
        # FIXME: this is a bug
        unit_str = factory.UnitDefinition.get_unit_string(unitRef)  # type: ignore
        p.setUnitRef(unit_str)
        ref = unit_str
    if metaIdRef is not None:
        p.setMetaIdRef(metaIdRef)
        ref = metaIdRef
    if name is None and ref is not None:
        p.setName(f"port {ref}")
    if portType == factory.PORT_TYPE_PORT:
        # SBO:0000599 - port
        p.setSBOTerm(599)
    elif portType == factory.PORT_TYPE_INPUT:
        # SBO:0000600 - input port
        p.setSBOTerm(600)
    elif portType == factory.PORT_TYPE_OUTPUT:
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


def replace_elements(
    model: libsbml.Model,
    sid: str,
    ref_type: str,
    replaced_elements: Dict[str, List[str]],
) -> None:
    """Replace elements in comp.

    :param model:
    :param sid:
    :param ref_type:
    :param replaced_elements:
    :return:
    """
    for submodel, rep_ids in replaced_elements.items():
        for rep_id in rep_ids:
            _create_replaced_element(model, sid, submodel, rep_id, ref_type=ref_type)


def replace_element_in_submodels(
    model: libsbml.Model, sid: str, ref_type: str, submodels: List[str]
) -> libsbml.ReplacedElement:
    """Replace elements submodels with the identical id.

    For instance to replace all the units in the submodels.

    :param model:
    :param sid:
    :param ref_type:
    :param submodels:
    :return:
    """
    for submodel in submodels:
        _create_replaced_element(model, sid, submodel, sid, ref_type=ref_type)


def _create_replaced_element(
    model: libsbml.Model, sid: str, submodel: str, replaced_id: str, ref_type: str
) -> libsbml.ReplacedElement:
    """Create a replaced element."""
    eplugin = _get_eplugin_by_sid(model, sid)
    replaced_element: libsbml.ReplacedElement = eplugin.createReplacedElement()
    replaced_element.setSubmodelRef(submodel)
    _set_ref(replaced_element, ref_id=replaced_id, ref_type=ref_type)

    return replaced_element


def replaced_by(
    model: libsbml.Model, sid: str, ref_type: str, submodel: str, replaced_by: str
) -> libsbml.ReplacedBy:
    """Create a ReplacedBy element.

    The element with sid in the model is replaced by the
    replacing_id in the submodel with submodel_id.
    """
    eplugin = _get_eplugin_by_sid(model=model, sid=sid)
    rby: libsbml.ReplacedBy = eplugin.createReplacedBy()
    rby.setSubmodelRef(submodel)
    _set_ref(sbaseref=rby, ref_id=replaced_by, ref_type=ref_type)
    return rby


def _get_eplugin_by_sid(model: libsbml.Model, sid: str) -> Any:
    """Get the comp plugin by sid.

    :param model: SBMLModel instance
    :param sid: SBase id of object
    :return:
    """
    e = model.getElementBySId(sid)
    if not e:
        e = model.getUnitDefinition(sid)
    eplugin = e.getPlugin("comp")
    return eplugin


def _set_ref(sbaseref: libsbml.SBaseRef, ref_id: str, ref_type: str) -> None:
    """Set reference for given reference type in the object.

    Objects can be
        ReplacedBy
        ReplacedElement
    """
    if ref_type == SBASE_REF_TYPE_ID:
        sbaseref.setIdRef(ref_id)
    elif ref_type == SBASE_REF_TYPE_UNIT:
        sbaseref.setUnitRef(ref_id)
    elif ref_type == SBASE_REF_TYPE_PORT:
        sbaseref.setPortRef(ref_id)
    elif ref_type == SBASE_REF_TYPE_METAID:
        sbaseref.setMetaIdRef(ref_id)
