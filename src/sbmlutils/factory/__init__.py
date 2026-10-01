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
