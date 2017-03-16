
from __future__ import print_function

import roadrunner
from sbmlutils import validation
from sbmlutils.tests import data


def test_validate_sbml():
    Nall, Nerr, Nwarn = validation.check_sbml(data.GALACTOSE_SINGLECELL_SBML, ucheck=True)
    assert Nerr == 0


def test_roadrunner_selections():
    rr = roadrunner.RoadRunner(data.GALACTOSE_SINGLECELL_SBML)
    assert len(rr.timeCourseSelections) == 27


def test_fixed_step_simulation():
    rr = roadrunner.RoadRunner(data.GALACTOSE_SINGLECELL_SBML)

    tend = 10.0
    steps = 100
    s = rr.simulate(start=0, end=tend, steps=steps)

    # test end point reached
    assert s[-1, 0] == 10
    # test correct number of steps
    assert len(s['time']) == steps+1
