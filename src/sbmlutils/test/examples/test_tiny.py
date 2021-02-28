import pytest

from sbmlutils.examples.tiny_model import simulation


@pytest.mark.skip
def test_tiny_simulation() -> None:
    simulation.tiny_simulation()
