"""Utilities for the creation and work with comp models.

Simplifies the port linking, submodel generation, ...

Heavily used in the dynamic FBA simulator. Mainly in the model creation
process. But the flattening parts also during the simulation
of the dynamic FBA models.
"""

import logging
from typing import Any

import libsbml

import sbmlutils.factory as factory

logger = logging.getLogger(__name__)


def create_ExternalModelDefinition(
    doc_comp: libsbml.CompSBMLDocumentPlugin,
    emd_id: str,
    source: str,
    model_ref: str | None = None,
) -> libsbml.ExternalModelDefinition:
    """Create comp ExternalModelDefinition.

    :param doc_comp: SBMLDocument comp plugin
    :param emd_id: id of external model definition
    :param source: source, resolved relative to the location of the document
    :param model_ref: id of the model in the external document; without it the
        definition is the main model of the external document
    :return: the created external model definition
    """
    extdef: libsbml.ExternalModelDefinition = doc_comp.createExternalModelDefinition()
    extdef.setId(emd_id)
    extdef.setName(emd_id)
    if model_ref is not None:
        extdef.setModelRef(model_ref)
    extdef.setSource(source)
    return extdef


def add_submodel_from_emd(
    model_comp: libsbml.CompModelPlugin,
    submodel_id: str,
    emd: libsbml.ExternalModelDefinition,
) -> libsbml.Submodel:
    """Add submodel to the model from given ExternalModelDefinition.

    The `comp:modelRef` of a submodel is the id of the external model
    definition in the same document, not the `comp:modelRef` of the definition,
    which is the id of the model in the external document.

    :param model_comp: Model comp plugin
    :param submodel_id: id of the submodel
    :param emd: external model definition the submodel instantiates
    :return: the created submodel
    """
    submodel: libsbml.Submodel = model_comp.createSubmodel()
    submodel.setId(submodel_id)
    submodel.setModelRef(emd.getId())

    referenced_model: libsbml.Model | None = emd.getReferencedModel()
    if referenced_model and referenced_model.isSetSBOTerm():
        submodel.setSBOTerm(referenced_model.getSBOTerm())
    return submodel


def create_ports(
    model: libsbml.Model,
    portRefs: Any | None = None,
    idRefs: Any | None = None,
    unitRefs: Any | None = None,
    metaIdRefs: Any | None = None,
    portType: factory.PortType = factory.PortType.PORT,
    suffix: str = factory.PORT_SUFFIX,
) -> list[libsbml.Port]:
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
    ports: list[libsbml.Port] = []
    data: Any
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
    else:
        raise ValueError(
            "One of 'portRefs', 'idRefs', 'unitRefs' or 'metaIdRefs' is required."
        )

    # dictionary, port ids are provided
    if isinstance(data, dict):
        for pid, ref in data.items():
            kwargs = {"pid": pid, ptype: ref}
            ports.append(_create_port(model, portType=portType, **kwargs))

    # only a list of references, port ids created via suffix appending
    elif isinstance(data, (list, tuple)):
        for ref in data:
            pid = ref + suffix
            kwargs = {"pid": pid, ptype: ref}
            ports.append(_create_port(model, portType=portType, **kwargs))

    return ports


def _create_port(
    model: libsbml.Model,
    pid: str,
    name: str | None = None,
    portRef: str | None = None,
    idRef: str | None = None,
    unitRef: str | None = None,
    metaIdRef: str | None = None,
    portType: factory.PortType = factory.PortType.PORT,
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
        # the unit reference is the id of a UnitDefinition of the model
        p.setUnitRef(unitRef)
        ref = unitRef
    if metaIdRef is not None:
        p.setMetaIdRef(metaIdRef)
        ref = metaIdRef
    if name is None and ref is not None:
        p.setName(f"port {ref}")
    if portType == factory.PortType.PORT:
        # SBO:0000599 - port
        p.setSBOTerm(599)
    elif portType == factory.PortType.INPUT_PORT:
        # SBO:0000600 - input port
        p.setSBOTerm(600)
    elif portType == factory.PortType.OUTPUT_PORT:
        # SBO:0000601 - output port
        p.setSBOTerm(601)

    return p
