"""Test model functionality."""
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
