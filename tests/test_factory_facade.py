"""Test that `sbmlutils.factory` keeps its names since it is a package.

`sbmlutils.factory` was a single module. It is a package whose `__init__`
re-exports the names of its modules, so a model definition, which imports the
names with `from sbmlutils.factory import *`, and code which imports a name
from `sbmlutils.factory` see the same names as before the split. The names are
pinned here as the module had them.
"""

import importlib
import inspect
import re
import typing
import warnings
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

#: the names the module only imported, with the module they come from and the
#: name in it (`None` for a module); code which imports them from
#: `sbmlutils.factory` still gets them, with a `DeprecationWarning`
DEPRECATED_NAMES: dict[str, tuple[str, str | None]] = {
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


@pytest.mark.parametrize("name", sorted(DEPRECATED_NAMES))
def test_deprecated_name_resolves_with_a_warning(name: str) -> None:
    """Test that a name the module only imported resolves with a warning.

    The warning names the import to use instead.
    """
    module_name, attribute = DEPRECATED_NAMES[name]
    module = importlib.import_module(module_name)
    expected = module if attribute is None else getattr(module, attribute)
    if attribute is not None:
        instead = f"from {module_name} import {attribute}"
    elif module_name != name:
        instead = f"import {module_name} as {name}"
    else:
        instead = f"import {module_name}"

    with pytest.warns(DeprecationWarning, match=re.escape(f"use `{instead}`")):
        value = getattr(factory, name)

    assert value is expected


def test_deprecated_names_are_not_public_names() -> None:
    """Test that the deprecated names stay out of `dir()` and `__all__`."""
    assert not set(DEPRECATED_NAMES) & set(dir(factory))
    assert not set(DEPRECATED_NAMES) & set(factory.__all__)


def test_downstream_import_of_a_deprecated_name() -> None:
    """Test the import of a model package which imports `sbml_to_antimony`.

    The models of pkdb_models import it from `sbmlutils.factory` together with
    names of the package.
    """
    namespace: dict[str, object] = {}
    with pytest.warns(DeprecationWarning, match="sbml_to_antimony"):
        exec(  # noqa: S102
            "from sbmlutils.factory import AssignmentRule, create_model, "
            "sbml_to_antimony",
            namespace,
        )

    assert namespace["AssignmentRule"] is factory.AssignmentRule
    assert namespace["create_model"] is factory.create_model
    assert (
        namespace["sbml_to_antimony"]
        is importlib.import_module("sbmlutils.io").sbml_to_antimony
    )


def test_unknown_name_raises_attribute_error() -> None:
    """Test that a name the module never had is an `AttributeError`."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(AttributeError, match="no_such_name"):
            factory.no_such_name  # noqa: B018  # ty: ignore[unresolved-attribute]
        assert not hasattr(factory, "annotations")


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
