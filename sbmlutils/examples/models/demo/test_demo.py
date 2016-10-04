"""
Test the demo network.
"""

from __future__ import print_function

import os
import unittest
import roadrunner
from sbmlutils import validation


from Cell import mid, version
demo_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'results',
                         '{}_{}.xml'.format(mid, version))


class DemoTestCase(unittest.TestCase):

    def test_validate_sbml(self):
        vres = validation.validate_sbml(demo_sbml, ucheck=True)
        self.assertEqual(vres["numCCErr"], 0)
        self.assertEqual(vres["numCCWarn"], 0)

    def test_roadrunner_selections(self):
        rr = roadrunner.RoadRunner(demo_sbml)
        print(rr.selections)
        self.assertTrue(len(rr.selections) > 1)

    def test_fixed_step_simulation(self):
        rr = roadrunner.RoadRunner(demo_sbml)
        tend = 10.0
        steps = 100
        s = rr.simulate(start=0, end=tend, steps=steps)

        # test end point reached
        self.assertEqual(s[-1, 0], 10)
        # test correct number of steps
        self.assertEqual(len(s['time']), steps+1)


if __name__ == '__main__':
    unittest.main()
