from sbmlutils.examples.tiny_model import simulation
import pytest


@pytest.mark.skip
def test_tiny_simulation():
    simulation.tiny_simulation()
