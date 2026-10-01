# ruff: noqa: I001
"""Create SBML models from a python definition.

A model definition is a `Model` which holds the elements of this package,
`create_model` writes it as an SBML file and validates it. A model definition
imports the names of `__all__` with a star import:

```python
from sbmlutils.factory import *
```

The package re-exports the classes and functions of its modules, which are
split along the SBML packages:

- `sbmlutils.factory._core`: `Sbase`, the base of every element, and the
  helpers the elements share
- `sbmlutils.factory.units`: units and unit definitions
- `sbmlutils.factory.core_elements`: the elements of SBML core
- `sbmlutils.factory.distrib`: the uncertainties of the distrib package
- `sbmlutils.factory.fbc`: the elements of the fbc package
- `sbmlutils.factory.comp`: the elements of the comp package
- `sbmlutils.factory.model`: `Model`, `ModelDefinition`, `Document` and
  `create_model`
"""

# Every name is re-exported explicitly (`X as X`), most of them are not in
# `__all__`. The imports follow the order of the modules and of the definitions
# in them, which is the order of the API reference, and are therefore not
# sorted. The API reference renders a re-exported class or function only when
# `docs/api/factory.md` lists it in `members`, which a test keeps complete.
import importlib as _importlib
import warnings as _warnings
from typing import TYPE_CHECKING as _TYPE_CHECKING
from typing import Any as _Any

from pymetadata.core.creator import Creator as Creator
from numpy import nan as NaN
from sbmlutils.reaction_equation import (
    EquationPart as EquationPart,
    ReactionEquation as ReactionEquation,
)
from sbmlutils.validation import ValidationOptions as ValidationOptions
from sbmlutils.factory._core import (
    SBML_LEVEL as SBML_LEVEL,
    SBML_VERSION as SBML_VERSION,
    PORT_SUFFIX as PORT_SUFFIX,
    PORT_UNIT_SUFFIX as PORT_UNIT_SUFFIX,
    create_objects as create_objects,
    ast_node_from_formula as ast_node_from_formula,
    collect_attribute_losses as collect_attribute_losses,
    collect_content_losses as collect_content_losses,
    AnnotationType as AnnotationType,
    AnnotationsType as AnnotationsType,
    OptionalAnnotationsType as OptionalAnnotationsType,
    set_notes as set_notes,
    Sbase as Sbase,
    KeyValuePair as KeyValuePair,
    Value as Value,
)
from sbmlutils.factory.units import (
    ureg as ureg,
    Q_ as Q_,
    UnitType as UnitType,
    ModelUnits as ModelUnits,
    Unit as Unit,
    UnitDefinition as UnitDefinition,
    Units as Units,
    ValueWithUnit as ValueWithUnit,
)
from sbmlutils.factory.core_elements import (
    Function as Function,
    Parameter as Parameter,
    LocalParameter as LocalParameter,
    Compartment as Compartment,
    Species as Species,
    InitialAssignment as InitialAssignment,
    RuleWithVariable as RuleWithVariable,
    AssignmentRule as AssignmentRule,
    RateRule as RateRule,
    AlgebraicRule as AlgebraicRule,
    Formula as Formula,
    KineticLaw as KineticLaw,
    Reaction as Reaction,
    EventAssignment as EventAssignment,
    Trigger as Trigger,
    Priority as Priority,
    Delay as Delay,
    Event as Event,
    Constraint as Constraint,
)
from sbmlutils.factory.distrib import (
    UncertParameter as UncertParameter,
    UncertSpan as UncertSpan,
    Uncertainty as Uncertainty,
)
from sbmlutils.factory.fbc import (
    PREFIX_EXCHANGE_REACTION as PREFIX_EXCHANGE_REACTION,
    ExchangeReaction as ExchangeReaction,
    GeneProduct as GeneProduct,
    UserDefinedConstraintComponent as UserDefinedConstraintComponent,
    UserDefinedConstraint as UserDefinedConstraint,
    FluxObjective as FluxObjective,
    Objective as Objective,
)
from sbmlutils.factory.comp import (
    ExternalModelDefinition as ExternalModelDefinition,
    Submodel as Submodel,
    SbaseRef as SbaseRef,
    ReplacedElement as ReplacedElement,
    ReplacedBy as ReplacedBy,
    Deletion as Deletion,
    PortType as PortType,
    Port as Port,
)
from sbmlutils.factory import _core, units
from sbmlutils.factory.model import (
    set_model_history as set_model_history,
    date_now as date_now,
    Package as Package,
    packages_in_canonical_order as packages_in_canonical_order,
    ModelDict as ModelDict,
    Model as Model,
    ModelDefinition as ModelDefinition,
    Document as Document,
    FactoryResult as FactoryResult,
    create_model as create_model,
)

# FIXME: make complete import of all DISTRIB constants
__all__ = [
    "PORT_SUFFIX",
    "PORT_UNIT_SUFFIX",
    "SBML_LEVEL",
    "SBML_VERSION",
    "AlgebraicRule",
    "AssignmentRule",
    "Compartment",
    "Constraint",
    "Creator",
    "Delay",
    "Deletion",
    "Document",
    "Event",
    "EventAssignment",
    "ExchangeReaction",
    "ExternalModelDefinition",
    "FactoryResult",
    "FluxObjective",
    "Formula",
    "Function",
    "GeneProduct",
    "InitialAssignment",
    "KeyValuePair",
    "KineticLaw",
    "LocalParameter",
    "Model",
    "ModelDefinition",
    "ModelDict",
    "ModelUnits",
    "NaN",
    "Objective",
    "Package",
    "Parameter",
    "Port",
    "PortType",
    "Priority",
    "RateRule",
    "Reaction",
    "ReactionEquation",
    "ReplacedBy",
    "ReplacedElement",
    "SbaseRef",
    "Species",
    "Submodel",
    "Trigger",
    "UncertParameter",
    "UncertSpan",
    "Uncertainty",
    "Unit",
    "UnitDefinition",
    "UnitType",
    "Units",
    "UserDefinedConstraint",
    "UserDefinedConstraintComponent",
    "ValidationOptions",
    "create_model",
]

# `_core` and `units` import `Uncertainty` for the type checker only, since
# `distrib` builds on them; it is bound into them here, after `distrib` was
# imported, so that `typing.get_type_hints` resolves their annotations. The
# layout package builds on this package and binds `Layout` into
# `sbmlutils.factory.model` the same way once it defined it, it is imported
# here so that this happens whenever the package is imported.
_core.Uncertainty = Uncertainty
units.Uncertainty = Uncertainty
_importlib.import_module("sbmlutils.layout.layout")

#: the names the module `sbmlutils.factory` only imported, before it was split
#: into a package, mapped to the module they come from and the name in it
#: (`None` for a module)
_DEPRECATED_NAMES: dict[str, tuple[str, str | None]] = {
    "AbstractContextManager": ("contextlib", "AbstractContextManager"),
    "Annotation": ("sbmlutils.metadata.annotator", "Annotation"),
    "Any": ("typing", "Any"),
    "BQB": ("sbmlutils.metadata", "BQB"),
    "BQM": ("sbmlutils.metadata", "BQM"),
    "ClassVar": ("typing", "ClassVar"),
    "ContextVar": ("contextvars", "ContextVar"),
    "FrozenClass": ("sbmlutils.utils", "FrozenClass"),
    "Iterable": ("collections.abc", "Iterable"),
    "Iterator": ("collections.abc", "Iterator"),
    "Literal": ("typing", "Literal"),
    "Notes": ("sbmlutils.notes", "Notes"),
    "NotesFormat": ("sbmlutils.notes", "NotesFormat"),
    "Path": ("pathlib", "Path"),
    "SBML2ODE": ("sbmlutils.converters.odefac", "SBML2ODE"),
    "SBO": ("sbmlutils.metadata", "SBO"),
    "ScopedLossCollector": ("sbmlutils.validation", "ScopedLossCollector"),
    "Sequence": ("collections.abc", "Sequence"),
    "StrEnum": ("enum", "StrEnum"),
    "TypeAlias": ("typing", "TypeAlias"),
    "TypedDict": ("typing", "TypedDict"),
    "UndefinedUnitError": ("pint", "UndefinedUnitError"),
    "Union": ("typing", "Union"),
    "UnionType": ("types", "UnionType"),
    "UnitRegistry": ("pint", "UnitRegistry"),
    "annotator": ("sbmlutils.metadata", "annotator"),
    "check": ("sbmlutils.validation", "check"),
    "contextmanager": ("contextlib", "contextmanager"),
    "create_metaid": ("sbmlutils.utils", "create_metaid"),
    "dataclass": ("dataclasses", "dataclass"),
    "datetime": ("datetime", None),
    "deepcopy": ("copy", "deepcopy"),
    "detect_format": ("sbmlutils.notes", "detect_format"),
    "get_args": ("typing", "get_args"),
    "get_origin": ("typing", "get_origin"),
    "get_type_hints": ("typing", "get_type_hints"),
    "inspect": ("inspect", None),
    "json": ("json", None),
    "libsbml": ("libsbml", None),
    "logging": ("logging", None),
    "namedtuple": ("collections", "namedtuple"),
    "np": ("numpy", None),
    "numbers": ("numbers", None),
    "re": ("re", None),
    "sbml_to_antimony": ("sbmlutils.io", "sbml_to_antimony"),
    "write_sbml": ("sbmlutils.io", "write_sbml"),
    "xmltodict": ("xmltodict", None),
}


# The module `__getattr__` is defined for the runtime only: the type checker
# would otherwise type every unknown attribute of the package as `Any` instead
# of reporting it, and the deprecated names are not part of its API.
if not _TYPE_CHECKING:

    def __getattr__(name: str) -> _Any:
        """Resolve a name the module `sbmlutils.factory` only imported.

        Code imported such names from the module, e.g. `sbml_to_antimony`, which
        the package does not re-export. They still resolve, with a
        `DeprecationWarning` which names the import to use instead.

        Args:
            name: the name of the attribute

        Returns:
            the object the module had under the name

        Raises:
            AttributeError: if the module never had the name
        """
        if name not in _DEPRECATED_NAMES:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        module_name, attribute = _DEPRECATED_NAMES[name]
        if attribute is not None:
            instead = f"from {module_name} import {attribute}"
        elif module_name != name:
            instead = f"import {module_name} as {name}"
        else:
            instead = f"import {module_name}"
        _warnings.warn(
            f"`sbmlutils.factory.{name}` is deprecated and will be removed, "
            f"use `{instead}`",
            DeprecationWarning,
            stacklevel=2,
        )
        module = _importlib.import_module(module_name)
        return module if attribute is None else getattr(module, attribute)
