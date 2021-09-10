import pytest

from sbmlutils.factory import *


def test_model_existing_attribute() -> None:
    m = Model("test")
    m.reactions = []


def test_model_new_attribute() -> None:
    m = Model("test")
    with pytest.raises(AttributeError) as _:
        m.reaction = []
