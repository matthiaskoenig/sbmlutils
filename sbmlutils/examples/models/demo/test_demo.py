from __future__ import print_function

import unittest

import roadrunner
from sbmlutils import validation

from sbmlutils.examples.testfiles import demo_sbml


class GalactoseTestCase(unittest.TestCase):
    """
    Unit tests on the galactose model to check the model behavior.
    """

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
