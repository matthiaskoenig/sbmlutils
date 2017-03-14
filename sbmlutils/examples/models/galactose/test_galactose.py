from __future__ import print_function

import unittest

import roadrunner
from sbmlutils import validation

from sbmlutils.test import data


class GalactoseTestCase(unittest.TestCase):
    """
    Unit tests on the galactose model to check the model behavior.
    """

    def test_validate_sbml(self):
        Nall, Nerr, Nwarn = validation.check_sbml(data.GALACTOSE_SINGLECELL_SBML, ucheck=True)
        self.assertEqual(Nerr, 0)

    def test_roadrunner_selections(self):
        rr = roadrunner.RoadRunner(data.GALACTOSE_SINGLECELL_SBML)
        print(rr.selections)
        self.assertTrue(len(rr.selections) > 1)

    def test_fixed_step_simulation(self):
        rr = roadrunner.RoadRunner(data.GALACTOSE_SINGLECELL_SBML)

        tend = 10.0
        steps = 100
        s = rr.simulate(start=0, end=tend, steps=steps)

        # test end point reached
        self.assertEqual(s[-1, 0], 10)
        # test correct number of steps
        self.assertEqual(len(s['time']), steps+1)


if __name__ == '__main__':
    unittest.main()
