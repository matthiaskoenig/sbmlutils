"""Test the demo model."""
import roadrunner

from sbmlutils.io.sbml import validate_sbml
from sbmlutils.test import DEMO_SBML


def test_check_sbml() -> None:
    vresults = validate_sbml(DEMO_SBML, units_consistency=True)
    assert vresults.is_perfect()


def test_roadrunner_selections() -> None:
    rr = roadrunner.RoadRunner(str(DEMO_SBML))
    assert len(rr.selections) > 1


def test_fixed_step_simulation() -> None:
    rr = roadrunner.RoadRunner(str(DEMO_SBML))
    tend = 10.0
    steps = 100
    s = rr.simulate(start=0, end=tend, steps=steps)

    # test end point reached
    assert s[-1, 0] == 10
    # test correct number of steps
    assert len(s["time"]) == steps + 1
