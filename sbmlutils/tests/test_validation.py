from __future__ import print_function, division

import tempfile
import unittest
from sbmlutils.validation import check_sbml

from sbmlutils.examples.testfiles import demo_sbml, galactose_singlecell_sbml, basic_sbml, vdp_sbml

##################################################################################
# These files are validated. All of them are valid and have no warnings or errors.
# dictionary of filenames, with setting for ucheck
SBML_FILES = {
    demo_sbml: True,
    galactose_singlecell_sbml: True,
    basic_sbml: True,
    vdp_sbml: False
}
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

    def test_check_vdp(self):
        Nerrors = check_sbml(vdp_sbml)
        self.assertEqual(Nerrors, 10)

    def validate_file(self, sbmlpath, ucheck=True):
        """ Validate given SBML file.

        Helper function called by the other tests.

        :param sbmlpath:
        :param ucheck:
        :return:
        """
        Nerrors = check_sbml(sbmlpath, ucheck=ucheck)
        self.assertIsNone(Nerrors)
        self.assertEqual(0, Nerrors)

    def test_files(self):
        """ Test all files provided in SBML_FILES

        :return:
        """
        for sbmlpath, ucheck in SBML_FILES.iteritems():
            self.validate_file(sbmlpath=sbmlpath, ucheck=ucheck)


if __name__ == '__main__':
    unittest.main()
