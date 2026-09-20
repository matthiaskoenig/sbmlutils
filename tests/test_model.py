"""Test model functionality."""

import libsbml
import pytest

from sbmlutils.factory import *


def test_model_existing_attribute() -> None:
    """Test model access existing attribute."""
    m = Model("tests")
    m.reactions = []


def test_model_new_attribute() -> None:
    """Test setting new attribute."""
    m = Model("tests")
    with pytest.raises(AttributeError) as _:
        m.reaction = []


def test_model_is_deepcopyable() -> None:
    """Test that a Model can be deep copied.

    `Model` declared `BaseModel` as a base but never reached
    `BaseModel.__init__`, so `__pydantic_extra__` was never initialized and
    deepcopy raised AttributeError. A round trip wants to snapshot a parsed
    model before mutating it.
    """
    import copy

    model = Model("test", compartments=[Compartment("c", value=1.0)])
    clone = copy.deepcopy(model)

    assert clone.sid == "test"
    assert clone.compartments[0].sid == "c"
    assert clone.compartments[0] is not model.compartments[0]


def test_model_equality() -> None:
    """Test that `==` on a Model no longer raises.

    `Model` declared `BaseModel` as a base but never reached
    `BaseModel.__init__`, so pydantic's generated `__eq__` accessed
    uninitialized private pydantic attributes and raised AttributeError.
    Dropping `BaseModel` falls back to plain identity-based equality: a
    model equals itself, and two distinct instances (no value equality is
    implemented) are not equal, but neither comparison raises.
    """
    model_a = Model("test", compartments=[Compartment("c", value=1.0)])
    model_b = Model("test", compartments=[Compartment("c", value=1.0)])

    assert model_a == model_a
    assert model_a != model_b


def test_key_value_pair_writes_uri() -> None:
    """Test that a KeyValuePair with a uri writes it.

    `create_sbml` called `kvp.setValue(self.value)` a second time inside the
    `self.uri is not None` branch instead of `kvp.setUri(self.uri)`, so the
    uri was never written to the SBML KeyValuePair (and the value was set
    twice).
    """
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 3)
    doc = libsbml.SBMLDocument(sbmlns)
    model = doc.createModel()
    model.getPlugin("fbc").setStrict(False)
    parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setConstant(True)

    kvp = KeyValuePair(key="k1", value="v1", uri="http://example.org/kvp")
    kvp.create_sbml(parameter)

    kvp_sbml = parameter.getPlugin("fbc").getListOfKeyValuePairs().get(0)
    assert kvp_sbml.getValue() == "v1"
    assert kvp_sbml.getUri() == "http://example.org/kvp"


def _fbc_strict(model: Model) -> bool | None:
    """Get `fbc:strict` of the model created by `Document`, `None` if unset."""
    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()
    fbc: libsbml.FbcModelPlugin = doc.getModel().getPlugin("fbc")
    return fbc.getStrict() if fbc.isSetStrict() else None


def test_model_strict_true_writes_true() -> None:
    """Test that `Model(strict=True)` writes `fbc:strict="true"`."""
    model = Model("m", packages=[Package.FBC], strict=True)

    assert _fbc_strict(model) is True


def test_model_strict_false_writes_false() -> None:
    """Test that `Model(strict=False)` writes `fbc:strict="false"`."""
    model = Model("m", packages=[Package.FBC], strict=False)

    assert _fbc_strict(model) is False


def test_model_strict_none_writes_false() -> None:
    """Test that `Model(strict=None)` keeps today's default of `fbc:strict="false"` when fbc is declared."""
    model = Model("m", packages=[Package.FBC])

    assert model.strict is None
    assert _fbc_strict(model) is False


def test_model_without_fbc_writes_no_strict() -> None:
    """Test that a model which does not declare fbc writes no `fbc:strict` at all."""
    model = Model("m")

    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()

    assert doc.getPlugin("fbc") is None


@pytest.mark.parametrize("strict", [True, False])
def test_a_stated_strict_declares_fbc(strict: bool) -> None:
    """Test that a model which states `strict` declares fbc for it.

    `fbc:strict` is an attribute of the fbc plugin of the model, so a model
    which says anything about strictness needs the package. Without other fbc
    content the statement used to be dropped in silence: no fbc namespace, no
    `fbc:strict`, no report. A model which states neither leaves `strict`
    `None` and declares nothing.
    """
    model = Model("m", strict=strict)

    doc: libsbml.SBMLDocument = Document(model=model).create_sbml()

    assert doc.getPlugin("fbc") is not None
    assert _fbc_strict(model) is strict
