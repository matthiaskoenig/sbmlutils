"""
Test the demo network.
"""

from __future__ import print_function, absolute_import

import roadrunner
from sbmlutils import validation
import sbmlutils.tests.data as data


def test_check_sbml():
    Nall, Nerr, Nwarn = validation.check_sbml(data.DEMO_SBML, ucheck=True)
    assert Nall == 0


def test_roadrunner_selections():
    rr = roadrunner.RoadRunner(data.DEMO_SBML)
    assert len(rr.selections) > 1


def test_fixed_step_simulation():
    rr = roadrunner.RoadRunner(data.DEMO_SBML)
    tend = 10.0
    steps = 100
    s = rr.simulate(start=0, end=tend, steps=steps)

    # test end point reached
    assert s[-1, 0] == 10
    # test correct number of steps
    assert len(s['time']) == steps+1
