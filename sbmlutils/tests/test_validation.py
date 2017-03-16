from __future__ import print_function, division

import unittest

from sbmlutils.validation import check_sbml
from sbmlutils.tests import data

##################################################################################
# These files are validated. All of them are valid and have no warnings or errors.
# dictionary of filenames, with setting for ucheck
SBML_FILES = [
    {'path': data.DFBA_EMD_SBML, 'ucheck': True, 'N': 0},
    {'path': data.DEMO_SBML, 'ucheck': True, 'N': 0},
    {'path': data.GALACTOSE_SINGLECELL_SBML, 'ucheck': True, 'N': 0},
    {'path': data.BASIC_SBML, 'ucheck': True, 'N': 0},
    {'path': data.VDP_SBML, 'ucheck': False, 'N': 10},
]


##################################################################################

class TestValidation(unittest.TestCase):
    """ Unittests for the validation module."""

    def validate_file(self, sbmlpath, ucheck=True, Nall=0):
        """ Validate given SBML file.

        Helper function called by the other tests.

        :param sbmlpath:
        :param ucheck:
        :return:
        """
        Nall, Nerr, Nwarn = check_sbml(sbmlpath, ucheck=ucheck)
        self.assertIsNotNone(Nall)
        # There is an SBOfix for model framework in the develop version,
        # with the wheel steel 3 warnings
        # FIXME: update to 0 with next libsbml wheel release
        self.assertTrue(Nall in [0, 3])

    def test_files(self):
        """ Test all files provided in SBML_FILES

        :return:
        """
        for d in SBML_FILES:
            self.validate_file(sbmlpath=d['path'], ucheck=d['ucheck'], Nall=d['N'])


if __name__ == '__main__':
    unittest.main()
