"""The model, its definitions and the document, and `create_model`.

`Model` holds the elements of a model definition and writes them in
the order SBML needs, `ModelDefinition` is a model inside a comp
document, `Document` writes the SBML document and `create_model`
writes, validates and reports it.
"""

from __future__ import annotations

import datetime
import inspect
import json
import logging
from collections.abc import Iterable, Iterator, Sequence
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    TypedDict,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

import libsbml
import xmltodict
from pymetadata.core.creator import Creator

from sbmlutils.converters.odefac import SBML2ODE
from sbmlutils.factory._core import (
    SBML_LEVEL,
    SBML_VERSION,
    AnnotationsType,
    AnnotationType,
    KeyValuePair,
    OptionalAnnotationsType,
    Sbase,
    _append_to_xhtml_body,
    _check_attribute,
    _comp_plugin,
    _create_object,
    _xhtml_body_content,
    collect_attribute_losses,
    collect_content_losses,
    create_objects,
)
from sbmlutils.factory.comp import (
    Deletion,
    ExternalModelDefinition,
    Port,
    ReplacedElement,
    SbaseRef,
    Submodel,
)
from sbmlutils.factory.core_elements import (
    AlgebraicRule,
    AssignmentRule,
    Compartment,
    Constraint,
    Event,
    Function,
    InitialAssignment,
    Parameter,
    RateRule,
    Reaction,
    Species,
    _ModelSymbols,
)
from sbmlutils.factory.distrib import _UncertChild
from sbmlutils.factory.fbc import GeneProduct, Objective, UserDefinedConstraint
from sbmlutils.factory.units import ModelUnits, UnitDefinition, Units
from sbmlutils.io import sbml_to_antimony, write_sbml
from sbmlutils.metadata import annotator
from sbmlutils.notes import Notes
from sbmlutils.utils import FrozenClass, create_metaid
from sbmlutils.validation import ValidationOptions, check

if TYPE_CHECKING:
    # the layout package builds on this module, see `Model.__init__`
    from sbmlutils.layout.layout import Layout

logger = logging.getLogger(__name__)


def set_model_history(
    sbase: libsbml.SBase, creators: list[Creator], set_timestamps: bool = True
) -> None:
    """Set the model history from given creators.

    :param sbase: SBML model
    :param creators: list of creators
    :param set_timestamps: boolean flag to set timestamps on history.
    :return:
    """
    if not sbase.isSetMetaId():
        # a model history is attached to the metaid of the model, so a
        # document which has no metaid at all (SBML L1) cannot carry one
        metaid = create_metaid(sbase=sbase)
        _check_attribute(
            sbase.setMetaId(metaid),
            sbase,
            "metaid",
            metaid,
            f"Model({sbase.getId()})",
        )

    # create and set model history
    h = _create_history(creators=creators, set_timestamps=set_timestamps)
    check(sbase.setModelHistory(h), "set model history")


def _create_history(
    creators: Iterable[Creator], set_timestamps: bool = True
) -> libsbml.ModelHistory:
    """Create the model history.

    Sets the create and modified date to the current time.
    The `set_timestamps` flag allows to set no timestamps.
    """
    h: libsbml.ModelHistory = libsbml.ModelHistory()

    for creator in creators:
        c: libsbml.ModelCreator = libsbml.ModelCreator()
        if creator.familyName:
            c.setFamilyName(creator.familyName)
        if creator.givenName:
            c.setGivenName(creator.givenName)
        if creator.email:
            c.setEmail(creator.email)
        if creator.organization:
            c.setOrganization(creator.organization)
        check(h.addCreator(c), "add creator")

    # create time is now
    if set_timestamps:
        datetime = date_now()
        check(h.setCreatedDate(datetime), "set creation date")
        check(h.setModifiedDate(datetime), "set modified date")
    else:
        datetime = libsbml.Date("1900-01-01T00:00:00")
        check(h.setCreatedDate(datetime), "set creation date")
        check(h.setModifiedDate(datetime), "set modified date")

    return h


def date_now() -> libsbml.Date:
    """Get current time stamp for history.

    :return: current libsbml Date
    """
    time = datetime.datetime.now()
    timestr = time.strftime("%Y-%m-%dT%H:%M:%S")
    return libsbml.Date(timestr)


def _iter_sbases_with_model(
    value: Any, in_model: bool = True, seen: set[int] | None = None
) -> Iterator[tuple[Sbase, bool]]:
    """Iterate every `Sbase` reachable from a value with how it is written.

    The walk descends into the attributes of every `Sbase` and into lists,
    tuples, sets and the values of dicts. So it finds an element wherever a
    model definition nests it: in a list of the model, among the parameters
    and rules of a reaction, the local parameters of a kinetic law, the
    assignments of an event or the glyphs of a layout.

    It also carries **whether the element is written with the
    `libsbml.Model`** of the document, which is what its port needs: the port
    of an element lives in the `<comp:listOfPorts>` of a model, so an element
    written without one cannot have a port at all. Two places write an
    element without the model, which is where the flag turns over:

    - everything below an `UncertParameter` or an `UncertSpan`, since
      `_UncertChild._set_fields` hands `None` down,
    - everything below the nested `sBaseRef` of a comp reference, since
      `SbaseRef._set_fields` hands `None` down for it.

    The walk yields every `Sbase` once, so an element which is reachable both
    ways keeps the first answer, which is the one that wrote it.

    Args:
        value: the value to walk, e.g. a `Model`
        in_model: whether the value and everything below it is written with
            the `libsbml.Model`; `True` for a whole model
        seen: the ids of the `Sbase` objects already yielded, which the
            recursion shares; every `Sbase` is yielded once, which also ends
            the walk on a cycle

    Yields:
        every `Sbase` reachable from the value, with whether it is written
        with the model
    """
    if seen is None:
        seen = set()
    if isinstance(value, Sbase):
        if id(value) in seen:
            return
        seen.add(id(value))
        yield value, in_model
        # the children of an uncert parameter or span are written without the
        # model, whatever wrote the child itself
        below = in_model and not isinstance(value, _UncertChild)
        for name, attribute in vars(value).items():
            # a scalar holds no element, not descending into it keeps the walk
            # from creating a generator for every string and number
            if isinstance(attribute, (Sbase, list, tuple, set, frozenset, dict)):
                nested = below and not (
                    isinstance(value, SbaseRef) and name == "sBaseRef"
                )
                yield from _iter_sbases_with_model(attribute, nested, seen)
    elif isinstance(value, (list, tuple, set, frozenset, dict)):
        for item in value.values() if isinstance(value, dict) else value:
            if isinstance(item, (Sbase, list, tuple, set, frozenset, dict)):
                yield from _iter_sbases_with_model(item, in_model, seen)


class Package(StrEnum):
    """Supported/tested packages.

    The definition order is the order the packages are declared on the
    `<sbml>` element in, see `packages_in_canonical_order`.
    """

    COMP = "comp"
    COMP_V1 = "comp-v1"
    DISTRIB = "distrib"
    DISTRIB_V1 = "distrib-v1"
    FBC = "fbc"
    FBC_V2 = "fbc-v2"
    FBC_V3 = "fbc-v3"


#: the libsbml package namespace of every `Package`, as `(name, package
#: version)`. The members which name no version map to the namespace `Model`
#: normalizes them to, see `Model.check_packages`.
_PACKAGE_NAMESPACES: dict[Package, tuple[str, int]] = {
    Package.COMP: ("comp", 1),
    Package.COMP_V1: ("comp", 1),
    Package.DISTRIB: ("distrib", 1),
    Package.DISTRIB_V1: ("distrib", 1),
    Package.FBC: ("fbc", 3),
    Package.FBC_V2: ("fbc", 2),
    Package.FBC_V3: ("fbc", 3),
}


def packages_in_canonical_order(packages: Iterable[Package]) -> list[Package]:
    """Order the packages of a model canonically, without repetition.

    The packages of a model were collected in a `set`, which the namespace
    declarations and the `required` attributes of the `<sbml>` element were
    written from in iteration order: the order of a set of `Package` members
    depends on the hash seed, so the same model definition wrote a different
    `<sbml>` element in every process. The declaration order of a namespace
    carries no meaning in XML, but a file which changes between two runs
    cannot be compared byte by byte at all. The definition order of `Package`
    is the order used instead, which is the alphabetical one, `comp`,
    `distrib`, `fbc`.

    Args:
        packages: the packages of a model, in any order and with repetition

    Returns:
        the packages in the definition order of `Package`, each one once
    """
    given = set(packages)
    return [package for package in Package if package in given]


class ModelDict(TypedDict, total=False):
    """ModelDict.

    The ModelDict allows to define the Model as dictionary and then
    use:

      md: ModelDict
      Model(**md)

    For model construction. If possible use the Model object directly.
    """

    sid: str
    name: str | None
    sboTerm: str | None
    metaId: str | None
    annotations: OptionalAnnotationsType
    notes: str | None
    keyValuePairs: list[KeyValuePair] | None
    packages: list[Package] | None
    creators: list[Creator] | None
    model_units: ModelUnits | None
    conversionFactor: str | None
    objects: list[Sbase] | None

    units: type[Units] | list[UnitDefinition] | None
    functions: list[Function] | None
    compartments: list[Compartment] | None
    species: list[Species] | None
    parameters: list[Parameter] | None
    assignments: list[InitialAssignment] | None
    rules: list[AssignmentRule] | None
    rate_rules: list[RateRule] | None
    algebraic_rules: list[AlgebraicRule] | None
    reactions: list[Reaction] | None
    events: list[Event] | None
    constraints: list[Constraint] | None
    # comp
    external_model_definitions: list[ExternalModelDefinition] | None
    model_definitions: list[ModelDefinition] | None
    submodels: list[Submodel] | None
    ports: list[Port] | None
    replaced_elements: list[ReplacedElement] | None
    deletions: list[Deletion] | None
    # fbc
    strict: bool | None
    user_defined_constraints: list[UserDefinedConstraint] | None
    objectives: list[Objective] | None
    gene_products: list[GeneProduct] | None
    # layout
    layouts: list[Layout] | None


def _math_symbols(math: libsbml.ASTNode | None) -> set[str]:
    """Get the names the math refers to.

    Args:
        math: the math, `None` for an element without math

    Returns:
        the name of every `AST_NAME` node of the math
    """
    if math is None:
        return set()
    symbols: set[str] = set()
    nodes: list[libsbml.ASTNode] = [math]
    while nodes:
        node = nodes.pop()
        if node.getType() == libsbml.AST_NAME:
            symbols.add(node.getName())
        nodes.extend(node.getChild(k) for k in range(node.getNumChildren()))
    return symbols


def _has_comp_replacement(sbase: libsbml.SBase) -> bool:
    """Say whether an element replaces an element of a submodel or is replaced.

    Args:
        sbase: the element

    Returns:
        `True` if the element carries a `<comp:replacedElement>` or a
        `<comp:replacedBy>`, `False` if not or if the document has no comp
    """
    plugin: libsbml.CompSBasePlugin | None = sbase.getPlugin("comp")
    if plugin is None:
        return False
    return bool(plugin.getNumReplacedElements() > 0 or plugin.isSetReplacedBy())


def _warn_never_changed(model: libsbml.Model) -> None:
    """Report the parameters and compartments which vary and never change.

    `constant=False` says that the value of a parameter or the size of a
    compartment changes during the simulation. That takes something which
    changes it: an assignment rule or a rate rule with the element as its
    variable, an event assignment to it, or an algebraic rule, which names no
    variable and determines one of the symbols of its math, so that every one
    of them counts. A parameter which is the variable of a component of a
    `<fbc:userDefinedConstraint>` counts as well: it is a variable of the
    optimization problem, whose value the solver determines, which is why fbc
    requires it to be `constant=False`. An initial assignment does not count,
    it sets the value once and does so for a constant as well. An element with none of them is
    a constant which says it is not, which is as a rule the trace of a rule
    which was forgotten or of a target which was misspelled.

    In a hierarchical model what changes an element can live in another
    model, so the elements of the comp interface are left out: one with a
    `<comp:port>` is there to be replaced by the model which instantiates
    this one, and one which replaces an element of a submodel, or is replaced
    by one, is the target of the rules of that submodel.

    This reads the created libsbml model rather than the model definition,
    because that is where the targets are complete: a `Parameter` with a
    formula creates its assignment rule, and a rule creates the parameter it
    assigns to if it is missing. It reports once per kind of element, with
    every id, and changes nothing: whether the rule or the `constant` is
    wrong is not something which can be decided here.

    It is an authoring hint, advice for a model definition being written. A
    model which was parsed from a file says what its source said, so nothing
    is reported inside `Sbase.no_authoring_hints`.

    Args:
        model: the libsbml model after all of its content was created
    """
    if not Sbase._authoring_hints.get():
        return

    changed: set[str] = set()
    for k in range(model.getNumRules()):
        rule: libsbml.Rule = model.getRule(k)
        if rule.isAlgebraic():
            changed |= _math_symbols(rule.getMath())
        else:
            changed.add(rule.getVariable())
    for k in range(model.getNumEvents()):
        event: libsbml.Event = model.getEvent(k)
        for j in range(event.getNumEventAssignments()):
            event_assignment: libsbml.EventAssignment = event.getEventAssignment(j)
            changed.add(event_assignment.getVariable())

    fbc_model: libsbml.FbcModelPlugin | None = model.getPlugin("fbc")
    if fbc_model is not None:
        for k in range(fbc_model.getNumUserDefinedConstraints()):
            constraint: libsbml.UserDefinedConstraint = (
                fbc_model.getUserDefinedConstraint(k)
            )
            for j in range(constraint.getNumUserDefinedConstraintComponents()):
                component: libsbml.UserDefinedConstraintComponent = (
                    constraint.getUserDefinedConstraintComponent(j)
                )
                changed.add(component.getVariable())

    comp_model: libsbml.CompModelPlugin | None = model.getPlugin("comp")
    if comp_model is not None:
        for k in range(comp_model.getNumPorts()):
            port: libsbml.Port = comp_model.getPort(k)
            if port.isSetIdRef():
                changed.add(port.getIdRef())

    compartments: list[libsbml.Compartment] = [
        model.getCompartment(k) for k in range(model.getNumCompartments())
    ]
    parameters: list[libsbml.Parameter] = [
        model.getParameter(k) for k in range(model.getNumParameters())
    ]
    elements: dict[str, list[libsbml.Compartment] | list[libsbml.Parameter]] = {
        "Compartment": compartments,
        "Parameter": parameters,
    }
    for kind, sbases in elements.items():
        never_changed: list[str] = [
            sbase.getId()
            for sbase in sbases
            if not sbase.getConstant()
            and sbase.getId() not in changed
            and not _has_comp_replacement(sbase)
        ]
        if never_changed:
            logger.warning(
                "%s '%s' element(s) %s of the model '%s' are 'constant=False', "
                "but none is ever changed by an assignment rule, a rate rule, "
                "an algebraic rule, an event assignment or a user defined "
                "constraint of fbc. Set 'constant=True' or add what changes "
                "them.",
                len(never_changed),
                kind,
                never_changed,
                model.getId(),
            )


class Model(Sbase, FrozenClass):
    """Model.

    The field annotations below document the model structure. `Model` used to
    declare `pydantic.BaseModel` as a base, but `Model.__init__` never reached
    `BaseModel.__init__` and `FrozenClass.__setattr__` shadowed pydantic's, so
    no validation ever ran and `deepcopy`, `==` and `model_dump` raised.
    `FrozenClass` rejects unknown attributes, which is what the freeze was for.
    """

    _hint_sbo_term: ClassVar[bool] = False

    sid: str
    name: str | None
    sboTerm: str | None
    metaId: str | None
    annotations: AnnotationsType
    notes: str | None
    keyValuePairs: list[KeyValuePair] | None
    port: Any | None
    packages: list[Package]
    creators: list[Creator]
    model_units: ModelUnits | None
    conversionFactor: str | None
    units: list[UnitDefinition]
    functions: list[Function]
    compartments: list[Compartment]
    species: list[Species]
    parameters: list[Parameter]
    assignments: list[InitialAssignment]
    rules: list[AssignmentRule]
    rate_rules: list[RateRule]
    algebraic_rules: list[AlgebraicRule]
    reactions: list[Reaction]
    events: list[Event]
    constraints: list[Constraint]
    # comp
    external_model_definitions: list[ExternalModelDefinition]
    model_definitions: list[ModelDefinition]
    submodels: list[Submodel]
    ports: list[Port]
    replaced_elements: list[ReplacedElement]
    deletions: list[Deletion]
    # fbc
    #: `fbc:strict` of the model, `None` keeps today's default of writing it
    #: `False` when the model declares fbc, and unset otherwise (see
    #: `Document._create_sbml`). It is a scalar in `_keys` (not `list`-typed), so
    #: `merge_models` overwrites it with the value of the last model that
    #: sets it, like `conversionFactor` and every other scalar field.
    strict: bool | None
    user_defined_constraints: list[UserDefinedConstraint]
    objectives: list[Objective]
    gene_products: list[GeneProduct]
    # layout
    layouts: list[Layout] | None
    parsed: bool

    #: field name -> merge kind read by `merge_models` to decide whether a
    #: field of two models is concatenated (`list`) or overwritten (`None`).
    #: Derived from the annotations above by `_derive_model_keys`, called once
    #: right after this class is defined, once every field annotation this
    #: class references is itself defined; see the comment there.
    _keys: ClassVar[dict[str, Any]] = {}

    _supported_packages: ClassVar[set[str]] = {
        Package.COMP,
        Package.COMP_V1,
        Package.DISTRIB,
        Package.DISTRIB_V1,
        Package.FBC,
        Package.FBC_V2,
        Package.FBC_V3,
    }

    #: field name -> why this kind of model does not support it, checked by
    #: `_check_fields`. Empty for the model of a document, which supports
    #: every field it declares; `ModelDefinition` fills it with the fields
    #: which have no place on a `<comp:modelDefinition>`.
    _unsupported_fields: ClassVar[dict[str, str]] = {}

    def __str__(self) -> str:
        """Get string."""
        # FIXME: issue with access
        # field_str = ", ".join(f"{a}={v!r}" for a, v in self.__repr_args__() if a and v and not a.startswith("_"))
        # return f"{self.__class__.__name__}({field_str})"
        return f"{self.__class__.__name__}"

    def __init__(
        self,
        sid: str,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        keyValuePairs: list[KeyValuePair] | None = None,
        packages: list[Package] | None = None,
        creators: list[Creator] | None = None,
        model_units: ModelUnits | None = None,
        conversionFactor: str | None = None,
        units: type[Units] | list[UnitDefinition] | None = None,
        objects: list[Sbase] | None = None,
        external_model_definitions: list[ExternalModelDefinition] | None = None,
        model_definitions: list[ModelDefinition] | None = None,
        submodels: list[Submodel] | None = None,
        functions: list[Function] | None = None,
        compartments: list[Compartment] | None = None,
        species: list[Species] | None = None,
        parameters: list[Parameter] | None = None,
        assignments: list[InitialAssignment] | None = None,
        rules: list[AssignmentRule] | None = None,
        rate_rules: list[RateRule] | None = None,
        algebraic_rules: list[AlgebraicRule] | None = None,
        reactions: list[Reaction] | None = None,
        events: list[Event] | None = None,
        constraints: list[Constraint] | None = None,
        ports: list[Port] | None = None,
        replaced_elements: list[ReplacedElement] | None = None,
        deletions: list[Deletion] | None = None,
        strict: bool | None = None,
        user_defined_constraints: list[UserDefinedConstraint] | None = None,
        objectives: list[Objective] | None = None,
        gene_products: list[GeneProduct] | None = None,
        layouts: list[Layout] | None = None,
    ):
        """Model constructor."""
        super().__init__(
            sid=sid,
            name=name,
            sboTerm=sboTerm,
            metaId=metaId,
            annotations=annotations,
            notes=notes,
            keyValuePairs=keyValuePairs,
        )

        self.packages = self.check_packages(packages)

        self.creators = list(creators) if creators else []
        self.model_units = model_units
        self.conversionFactor = conversionFactor
        self.units = Model._normalize_units(units)
        self.external_model_definitions = (
            list(external_model_definitions) if external_model_definitions else []
        )
        self.model_definitions = list(model_definitions) if model_definitions else []

        self.submodels: list[Submodel] = list(submodels) if submodels else []
        self.functions: list[Function] = list(functions) if functions else []
        self.compartments: list[Compartment] = (
            list(compartments) if compartments else []
        )
        self.species: list[Species] = list(species) if species else []
        self.parameters: list[Parameter] = list(parameters) if parameters else []
        self.assignments: list[InitialAssignment] = (
            list(assignments) if assignments else []
        )
        self.rules: list[AssignmentRule] = list(rules) if rules else []
        self.rate_rules: list[RateRule] = list(rate_rules) if rate_rules else []
        self.algebraic_rules: list[AlgebraicRule] = (
            list(algebraic_rules) if algebraic_rules else []
        )
        self.reactions: list[Reaction] = list(reactions) if reactions else []
        self.events: list[Event] = list(events) if events else []
        self.constraints: list[Constraint] = list(constraints) if constraints else []
        self.ports: list[Port] = list(ports) if ports else []
        self.replaced_elements: list[ReplacedElement] = (
            list(replaced_elements) if replaced_elements else []
        )
        self.deletions: list[Deletion] = list(deletions) if deletions else []
        self.strict = strict
        self.user_defined_constraints: list[UserDefinedConstraint] = (
            list(user_defined_constraints) if user_defined_constraints else []
        )
        self.objectives: list[Objective] = list(objectives) if objectives else []
        self.gene_products: list[GeneProduct] = (
            list(gene_products) if gene_products else []
        )

        self.layouts: list[Layout] | None = (
            list(layouts) if layouts is not None else None
        )

        #: `True` when the model was created by `sbmlutils.parser`, which
        #: suppresses the authoring hints when it is written back out
        self.parsed = False

        if objects:
            self._sort_objects(objects)

        self._check_fields()
        self._freeze()  # no new attributes after this point

    def _sort_objects(self, objects: list[Sbase]) -> None:
        """Append each of the `objects` to the field of `Model` for its type.

        Args:
            objects: the elements of the model, in any order

        Raises:
            ValueError: if an object has no field on `Model`, which would
                otherwise be dropped from the model in silence
        """
        # the layout package builds on the factory, so it is imported here
        # rather than at the top of the module, which it imports
        from sbmlutils.layout.layout import Layout

        fields: list[tuple[type, str]] = [
            (UnitDefinition, "units"),
            (ExternalModelDefinition, "external_model_definitions"),
            (ModelDefinition, "model_definitions"),
            (Submodel, "submodels"),
            (Function, "functions"),
            (Compartment, "compartments"),
            (Species, "species"),
            (Parameter, "parameters"),
            (InitialAssignment, "assignments"),
            (AssignmentRule, "rules"),
            (RateRule, "rate_rules"),
            (AlgebraicRule, "algebraic_rules"),
            (Reaction, "reactions"),
            (Event, "events"),
            (Constraint, "constraints"),
            (Port, "ports"),
            (ReplacedElement, "replaced_elements"),
            (Deletion, "deletions"),
            (UserDefinedConstraint, "user_defined_constraints"),
            (Objective, "objectives"),
            (GeneProduct, "gene_products"),
            (Layout, "layouts"),
        ]
        for sbase in objects:
            for object_type, field in fields:
                if isinstance(sbase, object_type):
                    if field == "layouts" and self.layouts is None:
                        self.layouts = []
                    getattr(self, field).append(sbase)
                    break
            else:
                raise ValueError(
                    f"'{type(sbase).__name__}' in the objects of model "
                    f"'{self.sid}' has no field on 'Model': '{sbase}'"
                )

    @staticmethod
    def _normalize_units(
        units: type[Units] | list[UnitDefinition] | None,
    ) -> list[UnitDefinition]:
        """Normalize the units of a model to a list of UnitDefinitions.

        A model definition declares its units as a `class U(Units)`, which is
        the documented authoring style; the parser passes a list. Both are
        stored as a list.

        Args:
            units: a `Units` subclass, a list of UnitDefinitions, or None

        Returns:
            the unit definitions of the model

        Raises:
            ValueError: if an attribute of the `Units` class is neither a unit
                string nor a UnitDefinition
        """
        if units is None:
            return []
        if isinstance(units, list):
            return list(units)

        udefs: list[UnitDefinition] = []
        for uid, definition in units.attributes():
            if isinstance(definition, str):
                udefs.append(UnitDefinition(sid=uid, definition=definition))
            elif isinstance(definition, UnitDefinition):
                udefs.append(definition)
            else:
                raise ValueError(
                    f"Units attributes must be a unit string or UnitDefinition, "
                    f"but '{type(definition)}' for '{definition}'."
                )
        return udefs

    def create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.Model:
        """Create Model.

        To create the complete SBMLDocument with the model use:

          doc = Document(model=model).create_sbml()

        Args:
            doc: the libsbml.SBMLDocument the model is created on. A
                `ModelDefinition` is created on the comp plugin of the
                document as well, which is what it inherits this from

        Returns:
            the created and filled libsbml.Model

        Raises:
            ValueError: if `doc` is not a libsbml.SBMLDocument. A model
                definition used to be created in the `libsbml.Model` it
                belonged to, and a caller which still passes one would
                otherwise reach the comp plugin of that model and fail with
                an `AttributeError` about `createModelDefinition`
        """
        if not isinstance(doc, libsbml.SBMLDocument):
            raise ValueError(
                f"`{type(self).__name__}.create_sbml` takes the "
                f"libsbml.SBMLDocument the model is created on, but got a "
                f"'{type(doc).__name__}'. A model definition is created on "
                f"the document next to the model of the document, and is "
                f"written by putting it in the `model_definitions` of a "
                f"`Model`."
            )
        if self.parsed:
            with Sbase.no_authoring_hints():
                return self._create_sbml(doc)
        return self._create_sbml(doc)

    def _create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.Model:
        """Create the libsbml.Model of this model on the document and fill it.

        Args:
            doc: the libsbml.SBMLDocument the model is created on

        Returns:
            the created and filled libsbml.Model
        """
        model: libsbml.Model = doc.createModel()
        self._fill_sbml(model)
        return model

    def _fill_sbml(self, model: libsbml.Model) -> None:
        """Write the content of this model into the libsbml model created for it.

        Filling a libsbml model is separated from creating it, because the two
        kinds of model the factory writes are created differently but hold the
        same content: the model of a document is created on the document with
        `createModel`, a `ModelDefinition` is created on the comp plugin of the
        document, and both are filled from here.

        **Everything created here is handed the model it is created in.** An
        element writer must not reach for its model itself: libsbml answers
        `getModel()` of an element inside a `<comp:modelDefinition>` with the
        model of the *document*, not with the model definition the element
        belongs to (measured with libsbml 5.21.2). Math parsed against that
        model resolves the ids of the wrong model, silently: a `time`
        parameter of the model definition is written as the SBML csymbol, and
        the document validates. So a new element type which creates something
        of its own passes the model on, as `Reaction` does to its
        `KineticLaw`, `Uncertainty` to its children, `Objective` to its flux
        objectives and `UserDefinedConstraint` to its components.

        **The model is a required argument** of every writer which parses
        math against it or creates something in it, `LocalParameter`,
        `KineticLaw`, `FluxObjective`, `UserDefinedConstraintComponent` and
        the children of an `Uncertainty` included, so that no writer falls
        back to the lookup. **`model=None` has one meaning**, *written
        without a model*, for `KeyValuePair` and `Sbase.create_port`, which
        need the model only to create the `<comp:listOfPorts>` a port lives
        in: the element has nowhere to put a port and the port is reported,
        see `Sbase._port_loss`. `_UncertChild._set_fields` hands `None` down
        to `Sbase._set_fields` for that reason, which is what keeps a child
        of an uncertainty from writing a port.

        Args:
            model: the created libsbml.Model, or the libsbml.ModelDefinition
                created for a `ModelDefinition`, which subclasses it

        Raises:
            ValueError: if a field this kind of model does not support is set
        """
        self._check_fields()
        self._set_fields(model, model)

        # history
        if self.creators:
            set_model_history(model, self.creators)

        # conversion factor
        if self.conversionFactor is not None:
            check(
                model.setConversionFactor(self.conversionFactor),
                f"Set conversionFactor on model '{self.sid}'",
            )

        # units
        for udef in self.units:
            udef.create_sbml(model=model)

        # model units
        if self.model_units:
            ModelUnits.set_model_units(model, self.model_units)

        # the two document level lists of comp: a `<comp:externalModelDefinition>`
        # and a `<comp:modelDefinition>` are children of the `<sbml>` element,
        # not of the `<model>`, so they are created on the document rather
        # than in the model, which is why they are not in the loop below. They
        # are created before the content of the model, as they were when they
        # were the first two keys of it: a `Submodel` of the model
        # instantiates them by `modelRef`. A `ModelDefinition` supports
        # neither of them, see its class docstring, so both lists are empty
        # for one and only the model of the document writes them.
        # an external model definition resolves the document from the model
        # it is given, a model definition is created on the document itself
        create_objects(
            model,
            obj_iter=self.external_model_definitions,
            key="external_model_definitions",
        )
        for model_definition in self.model_definitions:
            _create_object(model_definition, model.getSBMLDocument())

        # `fbc:strict` cannot be written on a model definition, see
        # `ModelDefinition`. Reported once for the document and only for a
        # model definition which claims `True`: `False` is what a reader of
        # the written document sees for an unset `fbc:strict` anyway. After
        # the model definitions were written, so that a model definition
        # which is rejected reports nothing but its rejection.
        strict_definitions = [
            model_definition.sid
            for model_definition in self.model_definitions
            if model_definition.strict
        ]
        if strict_definitions:
            logger.warning(
                "'strict' is not written on the model definitions %s: libsbml "
                "writes 'fbc:strict' twice on a <comp:modelDefinition>, which "
                "makes the written document unreadable, so a reader sees "
                "'fbc:strict' unset on them. See the class docstring of "
                "`ModelDefinition`.",
                strict_definitions,
            )

        # lists ofs
        self._create_lists(
            model,
            [
                "submodels",
                "functions",
                "parameters",
                "compartments",
                "species",
                "gene_products",
                "reactions",
            ],
        )
        # the rules and initial assignments check their variables against
        # the ids of the model, which are indexed once for all of them
        with _ModelSymbols.indexed(model):
            self._create_lists(
                model, ["assignments", "rules", "rate_rules", "algebraic_rules"]
            )
        self._create_lists(
            model,
            [
                "events",
                "constraints",
                "ports",
                "replaced_elements",
                "deletions",
                "user_defined_constraints",
                "objectives",
                "layouts",
            ],
        )

        # after everything which can change a value was created
        _warn_never_changed(model)

    def _create_lists(self, model: libsbml.Model, attrs: list[str]) -> None:
        """Create the elements of the lists of this model, in the given order.

        Args:
            model: the created libsbml.Model the elements are created in
            attrs: the names of the lists, e.g. `parameters`
        """
        for attr in attrs:
            objects = getattr(self, attr)
            if objects:
                create_objects(model, obj_iter=objects, key=attr)

    def get_sbml(self) -> str:
        """Create SBML model."""
        return Document(model=self).get_sbml()

    def check_packages(self, packages: list[Package] | None) -> list[Package]:
        """Check that all provided packages are supported.

        Args:
            packages: the packages of the model definition, in any order

        Returns:
            the packages, normalized to their version and in the canonical
            order of `packages_in_canonical_order`

        Raises:
            ValueError: if a package is not a `Package`, given twice, or not
                supported
        """
        if packages is None:
            packages = []
        packages_set: set[Package] = set(packages)
        for p in packages_set:
            if not isinstance(p, Package):
                msg = (
                    f"Packages must be provided as `Package`, but package "
                    f"`{p}` is `{type(p)}`."
                )
                logger.error(msg)
                raise ValueError(msg)

        # normalize package versions
        if Package.COMP in packages_set:
            packages_set.remove(Package.COMP)
            packages_set.add(Package.COMP_V1)

        if Package.FBC in packages_set:
            packages_set.remove(Package.FBC)
            packages_set.add(Package.FBC_V3)

        if Package.DISTRIB in packages_set:
            packages_set.remove(Package.DISTRIB)
            packages_set.add(Package.DISTRIB_V1)

        if len(packages_set) < len(packages):
            raise ValueError(f"Duplicate packages in `{packages}`.")

        for p in packages_set:
            if not isinstance(p, str):
                raise ValueError(
                    f"Packages must be provided as `Package`, but type `{type(p)}` "
                    f"for package `{p}`."
                )
            if p not in self._supported_packages:
                raise ValueError(
                    f"Supported packages are: '{self._supported_packages}', "
                    f"but package '{p}' found."
                )

        return packages_in_canonical_order(packages_set)

    def _check_fields(self) -> None:
        """Check that no field this kind of model does not support is set.

        Checked when the model is constructed and again when it is written,
        since the lists of a model are commonly populated by assignment after
        it was constructed, which the constructor cannot see.

        Raises:
            ValueError: if a field of `_unsupported_fields` is set
        """
        for field, reason in self._unsupported_fields.items():
            if getattr(self, field, None):
                raise ValueError(
                    f"'{field}' is not supported on "
                    f"{type(self).__name__} '{self.sid}': {reason}"
                )

    def _has_comp_content(self, level: int, version: int) -> bool:
        """Determine whether writing this model requires the comp package.

        The `submodels`/`ports`/`replaced_elements`/`deletions`/
        `model_definitions`/`external_model_definitions` lists are the
        explicit comp constructs, but comp is also engaged by the
        `port=True`/`Port(...)` and `replacedBy=...` shorthand any
        `Sbase`-derived element can carry (`Sbase.create_port`,
        `Sbase.create_replaced_by`), which does not populate `ports` at all.
        Such an element need not be in a list of the model: the parameters
        and rules of a `Reaction` are written as elements of the model, a
        `KineticLaw` holds its local parameters, an `Event` its assignments.
        So every `Sbase` reachable from the model is checked, see
        `_iter_sbases_with_model`, rather than a list of the places an element
        can be nested in, which would miss the next one.
        This is checked here, once every element list of the model is
        populated, rather than defaulted in `check_packages`, which runs
        from `__init__` before any of them are.

        **A port which cannot be written is not comp content.** Whether it
        can is decided by `Sbase._port_loss`, the same predicate the writer
        asks, so that a model whose only comp construct is such a port
        declares no comp package instead of leaving an empty comp namespace
        behind. The writer reports the port, once; this only counts. How a
        port names its element depends on the SBML level and version being
        written, so both are handed over, see `Sbase._port_reference_for`.

        Args:
            level: the SBML level of the document being written, which is
                required: the answer depends on it and a caller which does
                not say which document it means would get the answer for a
                different one
            version: the SBML version of the document being written

        The answer is read off `_required_packages`, which walks the model
        once for every package.

        Returns:
            True if the model uses a comp construct anywhere
        """
        return Package.COMP_V1 in self._required_packages(level, version)

    def _required_packages(self, level: int, version: int) -> set[Package]:
        """Determine the packages the content of this model requires.

        The model of a document declares the packages of the document itself,
        but a model definition has no way to declare one: a package is
        declared on the `<sbml>` element. So the document reads off the
        content of its model definitions which packages they need, see
        `Document._create_sbml`. Every `Sbase` reachable from the model is
        walked, once for all packages, see `_iter_sbases_with_model`, rather
        than a list of the places an element can be nested in, which would
        miss the next one. What makes content comp content is stated in
        `_has_comp_content`.

        Args:
            level: the SBML level of the document being written, which a port
                decides by how it names its element; required for the same
                reason as in `_has_comp_content`
            version: the SBML version of the document being written

        Returns:
            the packages the content of this model requires, at the version
            the factory writes; fbc content contributes `Package.FBC_V3`,
            since the content says that it is fbc content and not which
            version of fbc writes it
        """
        packages: set[Package] = set()
        if (
            self.submodels
            or self.ports
            or self.replaced_elements
            or self.deletions
            or self.model_definitions
            or self.external_model_definitions
        ):
            packages.add(Package.COMP_V1)

        # `fbc:strict` is an attribute of the fbc plugin of the model, so a
        # model which says anything about strictness engages fbc, `False`
        # included: that is a claim of its own, and a model which makes
        # neither claim leaves `strict` at `None`. A model definition is not
        # counted, since libsbml cannot write `fbc:strict` on one at all and
        # the package would be declared for an attribute nobody gets, see
        # `ModelDefinition` and `_fill_sbml`.
        if self.strict is not None and not isinstance(self, ModelDefinition):
            packages.add(Package.FBC_V3)

        for sbase, in_model in _iter_sbases_with_model(self):
            if Package.COMP_V1 not in packages and (
                # a port which cannot be written is not comp content
                (
                    getattr(sbase, "port", None) not in (None, False)
                    and sbase._port_loss(in_model, level, version) is None
                )
                or bool(getattr(sbase, "replacedBy", None))
            ):
                packages.add(Package.COMP_V1)
            if getattr(sbase, "uncertainties", None):
                packages.add(Package.DISTRIB_V1)
            if (
                # the key-value pairs of fbc version 3, which any element can
                # carry, and the three fbc lists of a model
                getattr(sbase, "keyValuePairs", None)
                or isinstance(sbase, (GeneProduct, Objective, UserDefinedConstraint))
                # the fbc attributes of a species and of a reaction
                or (
                    isinstance(sbase, Species)
                    and (sbase.charge is not None or sbase.chemicalFormula is not None)
                )
                or (
                    isinstance(sbase, Reaction)
                    and (
                        sbase.lowerFluxBound
                        or sbase.upperFluxBound
                        or sbase.geneProductAssociation
                    )
                )
            ):
                packages.add(Package.FBC_V3)

        return packages

    @staticmethod
    def merge_models(models: Iterable[Model]) -> Model:
        """Merge information from multiple models into a single model.

        The lists of the models are concatenated, the creators and the unit
        definitions are collected and deduplicated, and every other attribute
        is taken from the last model which sets it.

        Args:
            models: the models to merge; a single Model is returned unchanged

        Returns:
            the merged model

        Raises:
            ValueError: if no models are provided
        """
        if isinstance(models, Model):
            return models
        models = list(models)
        if not models:
            raise ValueError("No models are provided.")
        model = Model("template")
        # units are collected over all models and deduplicated by their id, so
        # that two models which define the same unit do not write it twice
        udefs: dict[str, UnitDefinition] = {}
        creators: dict[Creator, Any] = {}  # using a dict to keep order of insertion
        for m2 in models:
            for key, value in m2.__dict__.items():
                kind = m2._keys.get(key, None)
                # lists of higher modules are extended
                if kind in [list, tuple]:
                    # create new list
                    if not hasattr(model, key) or getattr(model, key) is None:
                        setattr(model, key, [])
                    # now add elements by copy
                    if getattr(model, key):
                        if value:
                            getattr(model, key).extend(deepcopy(value))
                    else:
                        if value:
                            setattr(model, key, deepcopy(value))

                # units are collected and merged at the end; they are copied
                # like every other merged list, so that the merged model and
                # the model it was merged from do not share one object
                elif key == "units":
                    for udef in m2.units:
                        if udef.sid:
                            udefs[udef.sid] = deepcopy(udef)
                elif key == "creators":
                    if m2.creators:
                        for c in m2.creators:
                            creators[c] = None
                # !everything else is overwritten
                else:
                    setattr(model, key, value)

        model.units = list(udefs.values())
        model.creators = list(creators)

        return model


class ModelDefinition(Model):
    """A comp model definition: a complete model of its own inside a document.

    A `<comp:modelDefinition>` lives in the document next to its main model
    and is instantiated by the `Submodel`s which name it in their `modelRef`.
    In libsbml `ModelDefinition` subclasses `Model`, and so does this class:
    the same code writes every element of it, its unit definitions, its model
    units and its model history included. It is created on the comp plugin of
    the document rather than with `createModel`, which is the only thing that
    differs, see `_create_sbml`.

    What a model definition does not take, decided by what libsbml 5.21.2
    accepts on a `<comp:modelDefinition>` and writes for it:

    - `packages`: a package is declared on the `<sbml>` element, which is the
      document, and comp gives a model definition no place to declare one.
      Rejected. The document declares what the content of its model
      definitions needs, see `Model._required_packages`.
    - `model_definitions` and `external_model_definitions`: both are children
      of the `<sbml>` element as well, and the `CompModelPlugin` of a model
      definition has neither `createModelDefinition` nor
      `createExternalModelDefinition`, so comp does not nest them at all.
      Rejected.
    - `strict`: the fbc model plugin does attach to a model definition and
      `setStrict` succeeds on it, but libsbml then writes `fbc:strict` twice
      on the `<comp:modelDefinition>` element and the document it writes
      cannot be read back, by libsbml or any other XML parser ("Duplicate XML
      attribute"). The attribute is therefore not written and a model
      definition which sets it is reported. A model definition with fbc
      content consequently carries the libsbml error 2020209 ("Strict
      attribute required on <model>"): a document which validates with one
      error is usable, an unreadable one is not.

    Everything else a `Model` holds is written into it: the comp constructs
    of a model definition (`submodels`, `ports`, `replaced_elements`,
    `deletions`), the fbc ones (`gene_products`, `objectives`,
    `user_defined_constraints`, the charge and the chemical formula of a
    species, the flux bounds and the gene product association of a reaction,
    key-value pairs), the distrib `uncertainties` of any of its elements and
    a `layouts` list, all through the plugins libsbml attaches to a model
    definition as it does to the model of a document.

    A model definition is a model *in* a document, not the model *of* it: it
    is written by putting it in the `model_definitions` of a `Model` and
    writing that model. Handing one to `create_model`, to `Document` or to
    `get_sbml` is refused, since the document it would write has a
    `<comp:modelDefinition>` and no `<model>` at all.
    """

    _unsupported_fields: ClassVar[dict[str, str]] = {
        "packages": (
            "the packages of a document are declared on its <sbml> element, "
            "which is written from the packages of its model; the document "
            "declares what the content of a model definition needs"
        ),
        "model_definitions": (
            "comp does not nest model definitions, a <comp:modelDefinition> "
            "is a child of the <sbml> element; use the model definitions of "
            "the model of the document"
        ),
        "external_model_definitions": (
            "a <comp:externalModelDefinition> is a child of the <sbml> "
            "element; use the external model definitions of the model of the "
            "document"
        ),
    }

    def _create_sbml(self, doc: libsbml.SBMLDocument) -> libsbml.ModelDefinition:
        """Create the libsbml.ModelDefinition on the document and fill it.

        Args:
            doc: the libsbml.SBMLDocument the model definition is created on

        Returns:
            the created and filled libsbml.ModelDefinition

        Raises:
            ValueError: if a field a model definition does not support is set,
                or if the document does not declare the comp package
        """
        # checked before anything is created, so that a model definition
        # which is rejected leaves no empty `<comp:modelDefinition>` behind
        self._check_fields()
        doc_comp: libsbml.CompSBMLDocumentPlugin = _comp_plugin(
            doc, f"The model definition '{self.sid}'"
        )
        model_definition: libsbml.ModelDefinition = doc_comp.createModelDefinition()
        self._fill_sbml(model_definition)
        return model_definition


def _model_field_kind(annotation: object) -> type | None:
    """Classify a resolved `Model` field annotation as list-valued or scalar.

    `merge_models` concatenates a `list`-valued field of the merged models
    and overwrites every other field with the value of the last model that
    sets it. An annotation is list-valued when it is, once `| None` /
    `Optional[...]` is stripped, the bare `list`, a
    subscripted `list[X]`, or a subscripted `Sequence[X]`. `Model.annotations`
    is declared `AnnotationsType` (`Sequence[AnnotationType]`, see its
    definition in `sbmlutils.factory._core`), not `list[...]`, because it accepts any
    sequence but `Sbase.__init__` always stores it as a list, so `Sequence` is
    classified the same as `list` here.

    Args:
        annotation: a fully resolved field annotation, as returned by
            `typing.get_type_hints`, not the raw annotation string
            `from __future__ import annotations` leaves in `__annotations__`

    Returns:
        `list` for a list-valued annotation, `None` for a scalar one

    Raises:
        TypeError: if `annotation` is a shape this function does not
            recognize (a union of more than one non-`None` member, or a
            generic other than `list`/`Sequence`), so a field with an
            annotation shape nobody has taught this function about fails
            loudly at import instead of silently being classified as scalar
    """
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        members = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(members) != 1:
            raise TypeError(
                f"Cannot classify Model field annotation {annotation!r}: a "
                f"union must have exactly one non-None member."
            )
        return _model_field_kind(members[0])
    if annotation is list or origin is list or origin is Sequence:
        return list
    if origin is None:
        # a plain, non-generic annotation (str, bool, Any, or a class): scalar
        return None
    raise TypeError(
        f"Cannot classify Model field annotation {annotation!r}: unsupported "
        f"generic origin {origin!r}."
    )


def _derive_model_keys() -> dict[str, Any]:
    """Derive `Model._keys` from `Model`'s own field annotations.

    Called once, as a module-level statement after the `Model` class body,
    rather than during it: `from __future__ import annotations` turns every
    annotation in this module into a string, and `typing.get_type_hints`
    resolves each of `Model`'s forward references (`Species`, `Reaction`, ...)
    by looking them up in the namespace of this module, which imports the
    elements at its top. One of those forward references is
    `ModelDefinition`, which subclasses `Model` and is therefore defined
    between the class body and this call, so they cannot be resolved while
    `Model`'s own class body is still executing. A type alias the fields use
    is resolved in the same namespace, which is why the aliases of
    `sbmlutils.factory._core` are values rather than strings.

    Every field `Model` declares in its own class body (not one inherited
    from `Sbase` or `FrozenClass`) is classified by `_model_field_kind`;
    `ClassVar`s and private names (`_keys` itself, `_supported_packages`) are
    not fields and are excluded.

    Two fields are `list`-typed on `Model` but forced to `None` here, because
    `merge_models` merges them itself in a dedicated branch, deduplicated,
    rather than through its generic list-extend branch:

    - `units`, deduplicated by unit id: marking it `list` would run the
      generic branch instead, which writes duplicate unit ids into the merged
      model.
    - `creators`, deduplicated by equality: marking it `list` would also run
      the generic branch instead, and `merge_models` then unconditionally
      overwrites `model.creators` with the (never populated) dedup dict after
      its main loop, discarding the generic branch's result and leaving the
      merged model with no creators at all.

    Returns:
        the field name -> merge kind mapping `merge_models` reads through
        `Model._keys`

    Raises:
        TypeError: if a field annotation's shape is not recognized by
            `_model_field_kind`
    """
    own_annotations = inspect.get_annotations(Model)
    # `Layout` is imported for the type checker only, the layout package
    # imports this module; the element type of a list does not change the
    # kind of the field
    resolved = get_type_hints(Model, localns={"Layout": Any})
    keys: dict[str, Any] = {}
    for name in own_annotations:
        if name.startswith("_"):
            continue
        hint = resolved[name]
        if get_origin(hint) is ClassVar:
            continue
        keys[name] = _model_field_kind(hint)

    keys["units"] = None
    keys["creators"] = None
    return keys


Model._keys = _derive_model_keys()


class Document(Sbase):
    """The SBML document a model is written into.

    `keyValuePairs` are not offered. fbc version 3 gives a
    `<fbc:keyValuePair>` to every `SBase`, but libsbml 5.21.2 attaches an
    `FbcSBMLDocumentPlugin` to the `<sbml>` element, which has no
    key-value-pair accessor at all: writing the pairs of a document failed
    with an `AttributeError` on the plugin, and a `<listOfKeyValuePairs>`
    written into the XML of an `<sbml>` element by hand is read without an
    error and is invisible afterwards.
    """

    _hint_name: ClassVar[bool] = False
    _hint_sbo_term: ClassVar[bool] = False

    def __init__(
        self,
        model: Model,
        sid: str | None = None,
        name: str | None = None,
        sboTerm: str | None = None,
        metaId: str | None = None,
        annotations: OptionalAnnotationsType = None,
        notes: str | Notes | None = None,
        sbml_level: int = SBML_LEVEL,
        sbml_version: int = SBML_VERSION,
    ):
        """Document constructor.

        Args:
            model: the model of the document
            sid: the id of the document
            name: the name of the document
            sboTerm: the SBO term of the document
            metaId: the meta id of the document
            annotations: the annotations of the document
            notes: the notes of the document
            sbml_level: the SBML level to write
            sbml_version: the SBML version to write

        Raises:
            ValueError: if the model is a `ModelDefinition`, which is a model
                of the document but not the model of the document
        """
        if isinstance(model, ModelDefinition):
            raise ValueError(
                f"A ModelDefinition is not the model of a document: "
                f"'{model.sid}' cannot be written on its own, a "
                f"<comp:modelDefinition> lives next to the <model> of a "
                f"document. Put it in the `model_definitions` of a `Model` "
                f"and write that model."
            )
        self.model = model
        self.sid = sid
        self.name = name
        self.sboTerm = sboTerm
        self.metaId = metaId
        self.annotations: list[AnnotationType] = (
            list(annotations) if annotations else []
        )
        # `Document` does not call `Sbase.__init__` (it has no sboTerm
        # handling and sets its own fields), so the notes normalization
        # `Sbase.__init__` otherwise applies is done here explicitly
        self.notes = Sbase._process_notes(notes)
        self.keyValuePairs = None
        self.sbml_level = sbml_level
        self.sbml_version = sbml_version
        self.doc: libsbml.SBMLDocument | None = None

        sbmlutils_notes = Sbase._process_notes(
            """
        Created with [https://github.com/matthiaskoenig/sbmlutils](https://github.com/matthiaskoenig/sbmlutils).
        [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5525390.svg)](https://doi.org/10.5281/zenodo.5525390)
        """
        )
        if sbmlutils_notes is None:
            raise RuntimeError("The attribution of the document has no content.")

        if self.notes is None:
            self.notes = sbmlutils_notes
        else:
            # both are already xhtml, appending the attribution as it is
            # would nest a body inside the notes; its content goes into their
            # body instead, which keeps an `<html>` root with its head
            self.notes = _append_to_xhtml_body(
                self.notes, _xhtml_body_content(sbmlutils_notes)
            )

    def create_sbml(self) -> libsbml.SBMLDocument:
        """Create the libsbml.SBMLDocument of the model.

        This writes a whole document, so a loss which one decision fixes for
        every element at once is reported once rather than once per element:
        an annotation resource which cannot be canonicalized, see
        `annotator.collect_resource_losses`, an attribute the document has no
        place for, see `collect_attribute_losses`, and content its fbc version
        cannot carry, see `collect_content_losses`.

        Returns:
            the created libsbml.SBMLDocument
        """
        with (
            annotator.collect_resource_losses(),
            collect_attribute_losses(),
            collect_content_losses(),
        ):
            return self._create_sbml()

    def _create_sbml(self) -> libsbml.SBMLDocument:
        """Create the libsbml.SBMLDocument and all its objects.

        Returns:
            the created libsbml.SBMLDocument
        """
        logger.info("Create SBML for model '%s'", self.model.sid)

        # the packages actually needed to write this model: whatever the
        # content of the model engages without the definition asking for it,
        # and whatever the content of a model definition of the document
        # needs, which is a model of its own but has no place to declare a
        # package, both read off by `Model._required_packages`. This must be
        # decided before the namespace is built, since libsbml cannot enable
        # a package on the document after it exists.
        packages = list(self.model.packages)
        required: set[Package] = self.model._required_packages(
            self.sbml_level, self.sbml_version
        )
        for model_definition in self.model.model_definitions:
            required |= model_definition._required_packages(
                self.sbml_level, self.sbml_version
            )

        if Package.COMP_V1 in required and Package.COMP_V1 not in packages:
            packages.append(Package.COMP_V1)
        if Package.DISTRIB_V1 in required and Package.DISTRIB_V1 not in packages:
            packages.append(Package.DISTRIB_V1)
        if Package.FBC_V3 in required and not (
            Package.FBC_V2 in packages or Package.FBC_V3 in packages
        ):
            # the content only says that it needs fbc, so the version is the
            # one `Package.FBC` normalizes to; a document which already
            # declares a version of fbc keeps it
            packages.append(Package.FBC_V3)
        # in the canonical order, so that a model which engages a package
        # through its content declares it where a model which asks for it
        # declares it, see `packages_in_canonical_order`
        packages = packages_in_canonical_order(packages)

        # create core model
        sbmlns = libsbml.SBMLNamespaces(self.sbml_level, self.sbml_version)

        # add all the package; a package namespace can only be added to an
        # SBML L3 document, libsbml answers with
        # `LIBSBML_INVALID_ATTRIBUTE_VALUE` below it and the document is
        # written without the package
        declared: list[Package] = []
        for package in packages:
            name, package_version = _PACKAGE_NAMESPACES[package]
            if check(
                sbmlns.addPackageNamespace(name, package_version),
                f"Declare the package '{package.value}' on an "
                f"SBML L{self.sbml_level}V{self.sbml_version} document",
            ):
                declared.append(package)
        packages = declared

        self.doc = libsbml.SBMLDocument(sbmlns)
        self._set_fields(self.doc, None)

        # create model
        sbml_model: libsbml.Model = self.model.create_sbml(self.doc)

        if Package.COMP_V1 in packages:
            check(
                self.doc.setPackageRequired("comp", True),
                "Set comp:required on the document",
            )
        if (Package.FBC_V2 in packages) or (Package.FBC_V3 in packages):
            check(
                self.doc.setPackageRequired("fbc", False),
                "Set fbc:required on the document",
            )
            fbc_plugin: libsbml.FbcModelPlugin = sbml_model.getPlugin("fbc")
            # `Model.strict` is `None` for a model which never set it, which
            # keeps today's default of writing `fbc:strict="false"`, see the
            # field's docstring in `Model`
            strict = self.model.strict if self.model.strict is not None else False
            check(
                fbc_plugin.setStrict(strict),
                f"Set fbc:strict on model '{self.model.sid}'",
            )
        if Package.DISTRIB_V1 in packages:
            check(
                self.doc.setPackageRequired("distrib", True),
                "Set distrib:required on the document",
            )

        return self.doc

    def get_sbml(self) -> str:
        """Return SBML string of the model.

        :return: SBML string
        """
        if self.doc is None:
            self.create_sbml()
        return str(libsbml.writeSBMLToString(self.doc))

    def get_json(self) -> str:
        """Get JSON representation."""
        o = xmltodict.parse(self.get_sbml())
        return json.dumps(o, indent=2)


@dataclass
class FactoryResult:
    """Data structure for model creation."""

    model: Model
    sbml_path: Path
    antimony_path: Path | None = None
    markdown_path: Path | None = None


def create_model(
    model: Model | Iterable[Model],
    filepath: Path,
    sbml_level: int = SBML_LEVEL,
    sbml_version: int = SBML_VERSION,
    validate: bool = True,
    validation_options: ValidationOptions | None = None,
    show_sbml: bool = False,
    annotations: Path | None = None,
    create_antimony: bool = False,
    create_markdown: bool = False,
) -> FactoryResult:
    """Create SBML model from models.

    This is the entry point for creating models. If multiple models are provided
    these are merged in the process of model creation. See `merge_models` for more
    details.

    Additional model annotations can be provided via a file.

    The created SBML can be serialized to additional formats for inspection, which
    are written next to the SBML file: the antimony serialization of the model
    (`create_antimony`, `*.ant`) and the markdown overview of the ODE system
    (`create_markdown`, `*.md`, see `sbmlutils.converters.odefac`).

    :param model: Model or iterable of Model instances which are merged in single model
    :param filepath: Path to write the SBML model to
    :param sbml_level: set SBML level for model generation
    :param sbml_version: set SBML version for model generation
    :param validate: boolean flag to validate the SBML file
    :param validation_options: options for model validation
    :param show_sbml: boolean flag to log the created SBML at INFO level on the `sbmlutils.factory.model` logger, nothing is shown unless logging is enabled, see `sbmlutils.log.enable_rich_logging`
    :param annotations: Path to annotations file
    :param create_antimony: write the antimony serialization to `*.ant`
    :param create_markdown: write the markdown overview of the ODE system to `*.md`

    :return: FactoryResult

    :raises ValueError: if `model` is neither a `Model` nor an iterable of them
    :raises OSError: if the SBML could not be written to `filepath`, see
        `write_sbml`. The parent directory is created if it does not exist.
        Validation does not raise: a document which does not validate is
        written and returned all the same.
    """
    filepath = Path(filepath)
    if validation_options is None:
        validation_options = ValidationOptions()

    # merge models (a Model is iterable itself, so it is checked first)
    m: Model
    if isinstance(model, Model):
        m = model
    elif isinstance(model, Iterable):
        m = Model.merge_models(model)
    else:
        raise ValueError(f"Unsupported `model` type: {type(model)}")

    # create and write SBML; creating the document and annotating it from a
    # file both write annotation resources, and one call writes one document,
    # so both report into one collector, see `collect_resource_losses`. The
    # attributes the document has no place for and the content its fbc
    # version cannot carry are collected the same way, see
    # `collect_attribute_losses` and `collect_content_losses`
    with (
        annotator.collect_resource_losses(),
        collect_attribute_losses(),
        collect_content_losses(),
    ):
        doc: libsbml.SBMLDocument = Document(
            model=m,
            sbml_level=sbml_level,
            sbml_version=sbml_version,
        ).create_sbml()

        write_sbml(
            doc=doc,
            filepath=filepath,
            validate=validate,
            validation_options=validation_options,
        )

        # annotation of model (overwrites file)
        if annotations is not None:
            annotator.annotate_sbml(
                source=filepath, annotations_path=annotations, filepath=filepath
            )

    # additional serializations (from the final file, including the annotations)
    antimony_path: Path | None = None
    if create_antimony:
        antimony_path = filepath.with_suffix(".ant")
        antimony_path.write_text(sbml_to_antimony(filepath), encoding="utf-8")
        logger.info("Antimony written to '%s'", antimony_path)

    markdown_path: Path | None = None
    if create_markdown:
        markdown_path = filepath.with_suffix(".md")
        SBML2ODE.from_file(filepath).to_markdown(md_file=markdown_path)
        logger.info("Markdown written to '%s'", markdown_path)

    # log created sbml
    if show_sbml:
        logger.info("Created SBML:\n%s", filepath.read_text(encoding="utf-8"))

    return FactoryResult(
        sbml_path=filepath,
        model=m,
        antimony_path=antimony_path,
        markdown_path=markdown_path,
    )
