import pytest

from sbmlutils.factory import *


def test_model_existing_attribute() -> None:
    m = Model("tests")
    m.reactions = []


def test_model_new_attribute() -> None:
    m = Model("tests")
    with pytest.raises(AttributeError) as _:
        m.reaction = []
