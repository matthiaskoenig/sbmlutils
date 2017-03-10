from __future__ import print_function, division

import tempfile
import unittest
from sbmlutils.validation import check_sbml
from sbmlutils.tests import resources
sbml_path = resources.DFBA_EMD_SBML

##################################################################################
# These files are validated. All of them are valid and have no warnings or errors.
# dictionary of filenames, with setting for ucheck
SBML_FILES = [
    {'path': resources.DFBA_EMD_SBML, 'ucheck': True, 'N': 0},
    {'path': resources.DEMO_SBML, 'ucheck': True, 'N': 0},
    {'path': resources.GALACTOSE_SINGLECELL_SBML, 'ucheck': True, 'N': 0},
    {'path': resources.BASIC_SBML, 'ucheck': True, 'N': 0},
    {'path': resources.VDP_SBML, 'ucheck': False, 'N': 10},
]
##################################################################################

class TestValidation(unittest.TestCase):
    """ Unittests for the validation module."""

    def test_check_sbml(self):
        import tellurium as te

        sbml_str = te.antimonyToSBML('''
        model feedback()
           // Reactions:
           J0: $X0 -> S1; (VM1 * (X0 - S1/Keq1))/(1 + X0 + S1 +   S4^h);
           J1: S1 -> S2; (10 * S1 - 2 * S2) / (1 + S1 + S2);
           J2: S2 -> S3; (10 * S2 - 2 * S3) / (1 + S2 + S3);
           J3: S3 -> S4; (10 * S3 - 2 * S4) / (1 + S3 + S4);
           J4: S4 -> $X1; (V4 * S4) / (KS4 + S4);

          // Species initializations:
          S1 = 0; S2 = 0; S3 = 0;
          S4 = 0; X0 = 10; X1 = 0;

          // Variable initialization:
          VM1 = 10; Keq1 = 10; h = 10; V4 = 2.5; KS4 = 0.5;
        end''')

        f = tempfile.NamedTemporaryFile(suffix=".xml")
        f.write(sbml_str)
        f.flush()

        # validate_sbml(f.name, ucheck=False)
        Nerrors = check_sbml(f.name)
        self.assertEqual(Nerrors, 36)

        self.validate_file(f.name, ucheck=False)


    def validate_file(self, sbmlpath, ucheck=True, Nerrors=0):
        """ Validate given SBML file.

        Helper function called by the other tests.

        :param sbmlpath:
        :param ucheck:
        :return:
        """
        Nerrors = check_sbml(sbmlpath, ucheck=ucheck)
        self.assertIsNotNone(Nerrors)
        self.assertEqual(0, Nerrors)

    def test_files(self):
        """ Test all files provided in SBML_FILES

        :return:
        """
        for d in SBML_FILES:
            self.validate_file(sbmlpath=d['path'], ucheck=d['ucheck'], Nerrors=d['N'])


if __name__ == '__main__':
    unittest.main()
