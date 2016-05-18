"""
Test naming.
"""

import unittest
from naming import *


class TestNaming(unittest.TestCase):
    """ Unit tests for naming. """

    def test_pp_id(self):
        self.assertEqual('PP', getPPId())
        self.assertEqual('PP__test', getPPSpeciesId('test'))
        self.assertTrue(isPPSpeciesId('PP__test'))
        self.assertFalse(isPPSpeciesId('PP_test'))

    def test_pv_id(self):
        self.assertEqual('PV', getPVId())
        self.assertEqual('PV__test', getPVSpeciesId('test'))
        self.assertTrue(isPVSpeciesId('PV__test'))
        self.assertFalse(isPVSpeciesId('PV_test'))

    def test_sinusoid_id(self):
        self.assertEqual(getSinusoidId(21), 'S21')
        self.assertEqual(getSinusoidId(2), 'S02')
        self.assertTrue(isSinusoidSpeciesId('S31__test'))
        self.assertFalse(isSinusoidSpeciesId('S1__test'))
    
    def test_disse_id(self):
        self.assertEqual(getDisseId(21), 'D21')
        self.assertEqual(getDisseId(2), 'D02')
        self.assertTrue(isDisseSpeciesId('D31__test'))
        self.assertFalse(isDisseSpeciesId('D1__test'))

    def test_hepatocyte_id(self):
        self.assertEqual(getHepatocyteId(21), 'H21')
        self.assertEqual(getHepatocyteId(2), 'H02')
        self.assertTrue(isHepatocyteSpeciesId('H31__test'))
        self.assertFalse(isHepatocyteSpeciesId('H1__test'))

    def test_cytosol_id(self):
        self.assertEqual(getCytosolId(21), 'C21')
        self.assertEqual(getCytosolId(2), 'C02')
        self.assertTrue(isCytosolSpeciesId('C31__test'))
        self.assertFalse(isCytosolSpeciesId('C1__test'))

    def test_localized_species_id(self):
        self.assertEqual(getPPSpeciesId('s1'), 'PP__s1')
        self.assertEqual(getPVSpeciesId('s1'), 'PV__s1')
        self.assertEqual(getSinusoidSpeciesId('s1', 3), 'S03__s1')
        self.assertEqual(getDisseSpeciesId('s1', 3), 'D03__s1')
        self.assertEqual(getHepatocyteSpeciesId('s1', 3), 'H03__s1')

if __name__ == "__main__":
    unittest.main()
