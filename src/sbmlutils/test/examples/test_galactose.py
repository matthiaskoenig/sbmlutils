import roadrunner

from sbmlutils.io.sbml import validate_sbml
from sbmlutils.test import GALACTOSE_SINGLECELL_SBML


def test_validate_sbml() -> None:
    vresults = validate_sbml(GALACTOSE_SINGLECELL_SBML, units_consistency=True)
    assert vresults.is_valid()


def test_roadrunner_selections() -> None:
    rr = roadrunner.RoadRunner(str(GALACTOSE_SINGLECELL_SBML))
    assert len(rr.timeCourseSelections) == 27


def test_fixed_step_simulation() -> None:
    rr = roadrunner.RoadRunner(str(GALACTOSE_SINGLECELL_SBML))

    tend = 10.0
    steps = 100
    s = rr.simulate(start=0, end=tend, steps=steps)

    # test end point reached
    assert s[-1, 0] == 10
    # test correct number of steps
    assert len(s["time"]) == steps + 1
