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
