"""The elements of the comp package.

External model definitions, submodels, the replacements and deletions
which reference their content, and ports.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any, ClassVar

import libsbml

from sbmlutils.factory._core import (
    KeyValuePair,
    OptionalAnnotationsType,
    Sbase,
    _check_attribute,
    _comp_plugin,
)
from sbmlutils.factory.units import UnitDefinition, _check_unit_type
from sbmlutils.metadata import SBO
from sbmlutils.notes import Notes

logger = logging.getLogger(__name__)


class ExternalModelDefinition(Sbase):
    """ExternalModelDefinition.

    `comp:modelRef` is **optional**: a definition without one refers to the
    main model of its source document, which is what
    `resources/models/sbml-test-suite-3.4.0/semantic/01168` does, and such a
    document validates. The empty string `sbmlutils.parser` hands over for a
    definition which states none is therefore not written rather than
    reported.
    """

    _hint_sbo_term: ClassVar[bool] = False

    def __init__(
        self,
        sid: str,
        source: str,
        modelRef: str,
        md5: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create an ExternalModelDefinition."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )
        self.source = source
        self.modelRef = modelRef
        self.md5 = md5

    def create_sbml(self, model: libsbml.Model) -> libsbml.ExternalModelDefinition:
        """Create ExternalModelDefinition."""
        doc = model.getSBMLDocument()
        cdoc = doc.getPlugin("comp")
        extdef = cdoc.createExternalModelDefinition()
        self._set_fields(extdef, model)
        return extdef

    def _set_fields(
        self, sbase: libsbml.ExternalModelDefinition, model: libsbml.Model
    ) -> None:
        """Set fields on ExternalModelDefinition."""
        super()._set_fields(sbase, model)
        if self.modelRef:
            _check_attribute(
                sbase.setModelRef(self.modelRef), sbase, "modelRef", self.modelRef, self
            )
        # the source and the md5 are plain strings, which libsbml accepts in
        # every form
        sbase.setSource(self.source)
        if self.md5 is not None:
            sbase.setMd5(self.md5)


class Submodel(Sbase):
    """Submodel."""

    _hint_sbo_term: ClassVar[bool] = False

    def __init__(
        self,
        sid: str,
        modelRef: str | None = None,
        timeConversionFactor: str | None = None,
        extentConversionFactor: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
    ):
        """Create a Submodel."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )
        self.modelRef = modelRef
        self.timeConversionFactor = timeConversionFactor
        self.extentConversionFactor = extentConversionFactor

    def create_sbml(self, model: libsbml.Model) -> libsbml.Submodel:
        """Create SBML Submodel."""
        cmodel = model.getPlugin("comp")
        submodel = cmodel.createSubmodel()
        self._set_fields(submodel, model)

        if self.modelRef is None:
            # comp:modelRef is a required attribute; libsbml raises a
            # SWIG TypeError for `setModelRef(None)` rather than reporting
            # an invalid value, so the guard has to sit in front of the
            # call. The document is written anyway (`create_model` reports,
            # it never blocks) and is caught by validation instead, which
            # reports id 1020607 ("Allowed <submodel> attributes") naming
            # 'comp:modelRef' as a missing required attribute, once for
            # every consistency check `ValidationOptions` runs.
            logger.error(
                "Submodel '%s' has no modelRef, which is a required "
                "attribute; the written document will not validate.",
                self.sid,
            )
        else:
            _check_attribute(
                submodel.setModelRef(self.modelRef),
                submodel,
                "modelRef",
                self.modelRef,
                self,
            )
        if self.timeConversionFactor:
            _check_attribute(
                submodel.setTimeConversionFactor(self.timeConversionFactor),
                submodel,
                "timeConversionFactor",
                self.timeConversionFactor,
                self,
            )
        if self.extentConversionFactor:
            _check_attribute(
                submodel.setExtentConversionFactor(self.extentConversionFactor),
                submodel,
                "extentConversionFactor",
                self.extentConversionFactor,
                self,
            )

        return submodel


class SbaseRef(Sbase):
    """SBaseRef.

    The base of `Port`, `ReplacedElement`, `ReplacedBy` and `Deletion`: each
    references an element by one of `portRef`, `idRef`, `unitRef`,
    `metaIdRef`. The SBML spec allows a `<comp:sBaseRef>` to hold a nested
    `<comp:sBaseRef>` child of its own, which continues the reference into a
    submodel of the referenced submodel, to arbitrary depth; `sBaseRef`
    holds that nested reference, an `SbaseRef` in its own right so the chain
    can continue.

    **A `ReplacedElement`, a `ReplacedBy` and a nested `<comp:sBaseRef>` carry
    no `sid` and no `name` into any document**, which is why both are
    optional on them. The two are the generic `id` and `name` SBML core gave
    every `SBase` in L3V2, and libsbml's comp writer serializes neither:
    measured with libsbml 5.21.2, `setIdAttribute` and `setName` answer
    `LIBSBML_UNEXPECTED_ATTRIBUTE` below L3V2 and success at L3V2, and the
    document written carries neither attribute at either version. Writing
    L3V2 is therefore no remedy, and an `sid` or a `name` given on one of the
    three is reported once per document and per kind of element, without
    advice, see `_UNWRITTEN_ID_TYPECODES`. `metaId`, `sboTerm`, notes and
    annotations are unaffected (they predate L3V2 and are written normally),
    and so are the `sid` and `name` of a `Port` and of a `Deletion`, since
    comp gives both elements an `id` and a `name` of their own, written as the
    package attributes `comp:id` and `comp:name`.

    A `Port`, a `ReplacedElement` or a `ReplacedBy` is a convenient, already
    available `SbaseRef` which a caller may reuse for a nested level, and
    whichever class builds it, a nested level is written as a plain
    `<comp:sBaseRef>`, see `_set_fields`. So a `Port` reused as one drops its
    `portType`, its `sid` and its `name`, and a `ReplacedElement` or a
    `ReplacedBy` reused as one drops its `submodelRef`, and a
    `ReplacedElement` also its `deletion` and its `conversionFactor`: none of
    those attributes exists on a `<comp:sBaseRef>`. `sbmlutils.parser` builds
    every nested level as a plain `SbaseRef`.
    """

    def __init__(
        self,
        sid: str | None = None,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
    ):
        """Create an SBaseRef."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )
        self.portRef = portRef
        self.idRef = idRef
        self.unitRef = unitRef
        _check_unit_type(self.unitRef, "unitRef", self)
        self.metaIdRef = metaIdRef
        self.sBaseRef = sBaseRef

    def _set_fields(self, sbase: Any, model: Any) -> None:
        """Set the fields of the created libsbml `SBaseRef` (or subclass).

        Args:
            sbase: the libsbml object created by `create_sbml`, one of
                `libsbml.Port`, `libsbml.ReplacedElement`,
                `libsbml.ReplacedBy`, `libsbml.Deletion` or, for a nested
                reference, `libsbml.SBaseRef` itself
            model: the `libsbml.Model` the object belongs to; `None` for a
                nested reference, which is written without a model, the
                meaning `None` has for a `KeyValuePair` and for the children
                of an uncertainty, see `Model._fill_sbml`
        """
        super()._set_fields(sbase, model)

        # exactly one of the four references is written. `<comp:port>` is the
        # one of them which cannot carry a `comp:portRef`: libsbml answers
        # `Port.setPortRef` with `LIBSBML_OPERATION_FAILED` whatever the
        # value, since comp does not let a port reference another port
        if self.portRef is not None:
            _check_attribute(
                sbase.setPortRef(self.portRef), sbase, "portRef", self.portRef, self
            )
        if self.idRef is not None:
            _check_attribute(
                sbase.setIdRef(self.idRef), sbase, "idRef", self.idRef, self
            )
        if self.unitRef is not None:
            unit_str = UnitDefinition.get_uid_for_unit(unit=self.unitRef)
            _check_attribute(
                sbase.setUnitRef(unit_str), sbase, "unitRef", unit_str, self
            )
        if self.metaIdRef is not None:
            _check_attribute(
                sbase.setMetaIdRef(self.metaIdRef),
                sbase,
                "metaIdRef",
                self.metaIdRef,
                self,
            )
        if self.sBaseRef is not None:
            nested: libsbml.SBaseRef = sbase.createSBaseRef()
            # written through the base class explicitly rather than through
            # `self.sBaseRef._set_fields`: a nested reference is always a
            # plain `<comp:sBaseRef>` in the SBML written, never a
            # `<comp:port>`, `<comp:replacedElement>` or
            # `<comp:replacedBy>`, whatever python class built it (a `Port`
            # is a convenient, already available `SbaseRef` a caller may
            # reuse for a nested level; its `portType` is a construction
            # convenience of `Port.create_sbml`, not a field of
            # `_set_fields`, so it is silently not applied to the nested
            # level, and a `ReplacedElement`/`ReplacedBy` passed here would
            # otherwise raise `AttributeError` on `setSubmodelRef`, which
            # `libsbml.SBaseRef` does not implement). `model` is passed as
            # `None`, which means the nested level is written without a
            # model, see `Model._fill_sbml`: none of the four subclasses
            # exposes `port`, `uncertainties` or `replacedBy` through its
            # constructor, so the only child a nested level carries is a
            # key-value pair, whose own port has nowhere to be created and
            # is reported, see `Sbase._port_loss`.
            SbaseRef._set_fields(self.sBaseRef, nested, None)


class ReplacedElement(SbaseRef):
    """ReplacedElement.

    comp writes a `<comp:replacedElement>` inside the element it replaces,
    and `Model.replaced_elements` holds it next to that element instead, with
    `elementRef` naming it. `elementRef` is therefore a pointer inside
    sbmlutils, it is not written into the document: `create_sbml` resolves it
    against the model the replacement is written in, as the id of an element,
    of a unit definition, which lives in a namespace of its own and which
    `getElementBySId` does not answer with, or, for an element which has no
    id at all, as its metaid. An SBML rule, an initial assignment, an event
    assignment and a kinetic law have an id only from SBML L3V2 on, and the
    SBML test suite replaces a rate rule which carries a metaid and no id.

    **The resolution order is the id of an element, then the id of a unit
    definition, then a metaid**, and it is not disambiguated: an element id
    and a unit definition id live in different namespaces, and a metaid in a
    third, so one string can name three different elements of one model, and
    the first of the three wins. A caller which names an element by its metaid
    is responsible for that metaid being the id of nothing else in the same
    model; `sbmlutils.parser` uses a metaid only for an element which has no
    id and reports the replacement as a loss instead of writing it when the
    metaid is the id of an element or of a unit definition of the same model,
    see `_replaced_element_ref`.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    def __init__(
        self,
        sid: str | None = None,
        elementRef: str = "",
        submodelRef: str = "",
        deletion: str | None = None,
        conversionFactor: str | None = None,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
    ):
        """Create a ReplacedElement.

        Args:
            sid: the id of the replacement, which libsbml writes into no
                document, see the class docstring of `SbaseRef`
            elementRef: the element of this model which is replaced, see the
                class docstring. comp requires it, and it carries an empty
                default only because the optional `sid` keeps its position in
                front of it; a replacement whose `elementRef` names no element
                of the model is refused when it is written
            submodelRef: the id of the submodel the replacing element lives
                in, `comp:submodelRef`. comp requires it, and it carries an
                empty default for the same reason; the empty string is what
                the parser hands over for a document which states none, and
                libsbml leaves the attribute unset for it
            deletion: the id of the deletion of the submodel this replacement
                refers to
            conversionFactor: the id of the parameter the values of the
                replaced element are converted with
            portRef: the port of the submodel which names the replacing element
            idRef: the id of the replacing element in the submodel
            unitRef: the id of the replacing unit definition in the submodel
            metaIdRef: the metaid of the replacing element in the submodel
            name: the name of the replacement, which libsbml writes into no
                document either
            sboTerm: the SBO term of the replacement
            metaId: the meta id of the replacement
            annotations: the annotations of the replacement
            notes: the notes of the replacement
            keyValuePairs: the fbc key value pairs of the replacement
            sBaseRef: the nested `<comp:sBaseRef>` which continues the
                reference into a submodel of the submodel
        """
        super().__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            sBaseRef=sBaseRef,
        )
        self.elementRef = elementRef
        self.submodelRef = submodelRef
        self.deletion = deletion
        self.conversionFactor = conversionFactor

    def create_sbml(self, model: libsbml.Model) -> libsbml.ReplacedElement:
        """Create the libsbml.ReplacedElement inside the element it replaces.

        Args:
            model: the libsbml.Model, or libsbml.ModelDefinition, the
                replacement is written in, which `elementRef` is resolved
                against

        Returns:
            the created libsbml.ReplacedElement

        Raises:
            ValueError: if `elementRef` names no element of the model
        """
        # resolve the element the replacement is written into, see the class
        # docstring on the three things `elementRef` can name
        e = model.getElementBySId(self.elementRef)
        if not e:
            # a unit definition lives in a namespace of its own, which
            # `getElementBySId` does not search (this shadows an element of
            # the same id, which SBML allows)
            e = model.getUnitDefinition(self.elementRef)
        if not e:
            # an element which has no id at all is named by its metaid
            e = model.getElementByMetaId(self.elementRef)
        if not e:
            raise ValueError(
                f"No SBML element, UnitDefinition or metaid found for "
                f"elementRef: '{self.elementRef}' in '{self}'"
            )

        eplugin = e.getPlugin("comp")
        obj = eplugin.createReplacedElement()
        self._set_fields(obj, model)

        return obj

    def _set_fields(self, sbase: libsbml.ReplacedElement, model: libsbml.Model) -> None:
        super()._set_fields(sbase, model)
        _check_attribute(
            sbase.setSubmodelRef(self.submodelRef),
            sbase,
            "submodelRef",
            self.submodelRef,
            self,
        )
        if self.deletion:
            _check_attribute(
                sbase.setDeletion(self.deletion), sbase, "deletion", self.deletion, self
            )
        if self.conversionFactor:
            _check_attribute(
                sbase.setConversionFactor(self.conversionFactor),
                sbase,
                "conversionFactor",
                self.conversionFactor,
                self,
            )


class ReplacedBy(SbaseRef):
    """ReplacedBy: an element of this model is replaced by one of a submodel."""

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    def __init__(
        self,
        sid: str | None = None,
        elementRef: str = "",
        submodelRef: str = "",
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
    ):
        """Create a ReplacedBy.

        Args:
            sid: the id of the replacement, which libsbml writes into no
                document, see the class docstring of `SbaseRef`
            elementRef: the element of this model which is replaced. A
                `<comp:replacedBy>` is written inside that element, which
                `create_sbml` is handed, so this is a pointer inside sbmlutils
                and is not written; it carries an empty default only because
                the optional `sid` keeps its position in front of it
            submodelRef: the id of the submodel the replacing element lives
                in, `comp:submodelRef`. comp requires it, and it carries an
                empty default for the same reason; the empty string is what
                the parser hands over for a document which states none, and
                libsbml leaves the attribute unset for it
            portRef: the port of the submodel which names the replacing element
            idRef: the id of the replacing element in the submodel
            unitRef: the id of the replacing unit definition in the submodel
            metaIdRef: the metaid of the replacing element in the submodel
            name: the name of the replacement, which libsbml writes into no
                document either
            sboTerm: the SBO term of the replacement
            metaId: the meta id of the replacement
            annotations: the annotations of the replacement
            notes: the notes of the replacement
            keyValuePairs: the fbc key value pairs of the replacement
            sBaseRef: the nested `<comp:sBaseRef>` which continues the
                reference into a submodel of the submodel
        """
        super().__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            sBaseRef=sBaseRef,
        )
        self.elementRef = elementRef
        self.submodelRef = submodelRef

    def create_sbml(
        self, sbase: libsbml.SBase, model: libsbml.Model
    ) -> libsbml.ReplacedBy:
        """Create SBML ReplacedBy."""
        sbase_comp: libsbml.CompSBasePlugin = _comp_plugin(
            sbase, f"The replacedBy of {sbase.getElementName()} '{sbase.getId()}'"
        )
        rby: libsbml.ReplacedBy = sbase_comp.createReplacedBy()
        self._set_fields(rby, model)

        return rby

    def _set_fields(self, sbase: libsbml.ReplacedBy, model: libsbml.Model) -> None:
        """Set fields in ReplacedBy."""
        super()._set_fields(sbase, model)
        _check_attribute(
            sbase.setSubmodelRef(self.submodelRef),
            sbase,
            "submodelRef",
            self.submodelRef,
            self,
        )


class Deletion(SbaseRef):
    """Deletion."""

    def __init__(
        self,
        sid: str,
        submodelRef: str,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
    ):
        """Initialize Deletion."""
        super().__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            sBaseRef=sBaseRef,
        )
        self.submodelRef = submodelRef

    def create_sbml(self, model: libsbml.Model) -> libsbml.Deletion:
        """Create the libsbml.Deletion inside the submodel it deletes from.

        Args:
            model: the libsbml.Model, or libsbml.ModelDefinition, the
                submodel of the deletion lives in

        Returns:
            the created libsbml.Deletion

        Raises:
            ValueError: if the document does not declare the comp package, or
                if `submodelRef` names no submodel of the model
        """
        cmodel: libsbml.CompModelPlugin = _comp_plugin(model, f"The deletion '{self}'")
        submodel: libsbml.Submodel | None = cmodel.getSubmodel(self.submodelRef)
        if submodel is None:
            # a `<comp:deletion>` is written inside the submodel it names, so
            # a name which is no submodel of this model has nowhere to go;
            # named the way `ReplacedElement` names an `elementRef` it cannot
            # resolve
            raise ValueError(
                f"No submodel found for submodelRef: '{self.submodelRef}' in '{self}'"
            )
        deletion: libsbml.Deletion = submodel.createDeletion()
        self._set_fields(deletion, model)

        return deletion


class PortType(StrEnum):
    """Supported port types."""

    PORT = "port"
    INPUT_PORT = "input port"
    OUTPUT_PORT = "output port"


class Port(SbaseRef):
    """Port.

    Ports are stored in an optional child ListOfPorts object, which, if
    present, must contain one or more Port objects.  All of the Ports
    present in the ListOfPorts collectively define the 'port interface' of
    the Model.

    `portType` is an authoring convenience: a port which states no `sboTerm`
    is given the SBO term of its port type, `SBO:0000599` for the plain
    `PortType.PORT` of the default. `portType=None` asks for neither, which is
    what a port read from a document states: SBML has no port type, the
    document either carries an sboTerm or it does not, and inventing one would
    make a round trip of a port without an sboTerm write one.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    #: the SBO term which stands for each port type
    _SBO_FOR_PORT_TYPE: ClassVar[dict[PortType, SBO]] = {
        PortType.PORT: SBO.PORT,
        PortType.INPUT_PORT: SBO.INPUT_PORT,
        PortType.OUTPUT_PORT: SBO.OUTPUT_PORT,
    }

    def __init__(
        self,
        sid: str,
        portRef: str | None = None,
        idRef: str | None = None,
        unitRef: str | None = None,
        metaIdRef: str | None = None,
        portType: PortType | None = PortType.PORT,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        sBaseRef: SbaseRef | None = None,
    ):
        """Create a Port."""
        super().__init__(
            sid=sid,
            portRef=portRef,
            idRef=idRef,
            unitRef=unitRef,
            metaIdRef=metaIdRef,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
            sBaseRef=sBaseRef,
        )
        self.portType = portType

    def create_sbml(self, model: libsbml.Model) -> libsbml.Port:
        """Create the libsbml.Port in the given model.

        Args:
            model: the libsbml.Model, or libsbml.ModelDefinition, the port is
                created in

        Returns:
            the created libsbml.Port

        Raises:
            ValueError: if the document does not declare the comp package
        """
        cmodel: libsbml.CompModelPlugin = _comp_plugin(model, f"Port '{self.sid}'")
        p = cmodel.createPort()
        self._set_fields(p, model)

        if self.sboTerm is None and self.portType is not None:
            sbo: SBO = Port._SBO_FOR_PORT_TYPE[self.portType]
            p.setSBOTerm(sbo.value.replace("_", ":"))

        return p
