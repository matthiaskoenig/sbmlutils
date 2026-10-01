"""Test that `sbmlutils.factory` keeps its names since it is a package.

`sbmlutils.factory` was a single module. It is a package whose `__init__`
re-exports the names of its modules, so a model definition, which imports the
names with `from sbmlutils.factory import *`, and code which imports a name
from `sbmlutils.factory` see the same names as before the split. The names are
pinned here as the module had them.
"""

import inspect
import re
import typing
from pathlib import Path
from types import ModuleType

import pytest

from sbmlutils import factory

#: the names of `__all__`, which a star import gives a model definition
STAR_NAMES: frozenset[str] = frozenset(
    {
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
    }
)

#: the public names of the module besides `__all__`: what it defined and
#: `EquationPart`, which it imported and code imports from it
PUBLIC_NAMES: frozenset[str] = STAR_NAMES | frozenset(
    {
        "PREFIX_EXCHANGE_REACTION",
        "Q_",
        "ureg",
        "AnnotationType",
        "AnnotationsType",
        "OptionalAnnotationsType",
        "EquationPart",
        "RuleWithVariable",
        "Sbase",
        "Value",
        "ValueWithUnit",
        "ast_node_from_formula",
        "collect_attribute_losses",
        "collect_content_losses",
        "create_objects",
        "date_now",
        "packages_in_canonical_order",
        "set_model_history",
        "set_notes",
    }
)

API_PAGE: Path = Path(__file__).parent.parent / "docs" / "api" / "factory.md"


def test_star_import_gives_the_names_of_all() -> None:
    """Test that `from sbmlutils.factory import *` gives the pinned names."""
    namespace: dict[str, object] = {}
    exec("from sbmlutils.factory import *", namespace)  # noqa: S102
    namespace.pop("__builtins__")

    assert set(namespace) == STAR_NAMES
    assert set(factory.__all__) == STAR_NAMES
    for name, value in namespace.items():
        assert value is getattr(factory, name)


def test_package_has_the_public_names_of_the_module() -> None:
    """Test that the public names of the package are the pinned names.

    The modules of the package are attributes of it as well, they are not
    names a model definition uses.
    """
    names = {
        name
        for name in dir(factory)
        if not name.startswith("_")
        and not isinstance(getattr(factory, name), ModuleType)
    }
    assert names == PUBLIC_NAMES


def test_api_reference_lists_the_classes_and_functions() -> None:
    """Test that the API reference lists every class and function of the package.

    The API reference renders a re-exported class or function only if
    `docs/api/factory.md` lists it in `members`, so a class which is added to
    the package and not to the page would be missing from the reference.
    """
    members = re.findall(r"^\s+- (\w+)$", API_PAGE.read_text(), flags=re.MULTILINE)
    own = {
        name
        for name in PUBLIC_NAMES
        if (inspect.isclass(obj := getattr(factory, name)) or inspect.isfunction(obj))
        and obj.__module__.startswith("sbmlutils.factory.")
    }

    assert len(members) == len(set(members))
    assert set(members) == own | {"ReactionEquation", "ValidationOptions"}


def _hinted(obj: object) -> list[tuple[str, object]]:
    """Get a class with its own functions, or a function, to resolve hints of."""
    if inspect.isclass(obj):
        return [(obj.__qualname__, obj)] + [
            (f"{obj.__qualname__}.{name}", value)
            for name, value in vars(obj).items()
            if inspect.isfunction(value)
        ]
    if inspect.isfunction(obj):
        return [(obj.__qualname__, obj)]
    return []


@pytest.mark.parametrize(
    "name",
    sorted(
        name
        for name in PUBLIC_NAMES
        if getattr(getattr(factory, name), "__module__", "").startswith("sbmlutils.")
    ),
)
def test_type_hints_resolve(name: str) -> None:
    """Test that `typing.get_type_hints` resolves the annotations of a name.

    The modules import some names of their annotations for the type checker
    only, which must still resolve at runtime, for documentation tools and for
    code which inspects the signatures.
    """
    for _, obj in _hinted(getattr(factory, name)):
        typing.get_type_hints(obj)
