import pytest

from sbmlutils.examples.tiny_model import simulation


@pytest.mark.skip
def test_tiny_simulation():
    simulation.tiny_simulation()
