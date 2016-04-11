from __future__ import print_function, division

import unittest
import tempfile
from multiscale.sbmlutils.validation import validate_sbml, check_sbml
from multiscale.examples.testdata import demo_sbml, galactose_singlecell_sbml, test_sbml, vdp_sbml


class TestValidation(unittest.TestCase):

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

        print(sbml_str)

        # validate_sbml(f.name, ucheck=False)
        Nerrors = check_sbml(f.name)
        self.assertEqual(Nerrors, 36)

        self.validate_file(f.name, ucheck=False)


    def test_check_vdp(self):
        Nerrors = check_sbml(vdp_sbml)
        self.assertEqual(Nerrors, 10)


    def validate_file(self, sbml_file, ucheck=True):
        results = validate_sbml(sbml_file, ucheck=ucheck)
        self.assertEqual(0, results["numCCErr"])
        self.assertEqual(0, results["numCCWarn"])

    def test_validate_demo(self):
        self.validate_file(demo_sbml)

    def test_validate_galactose(self):
        self.validate_file(galactose_singlecell_sbml)

    def test_validate_test(self):
        self.validate_file(test_sbml)

    def test_validate_vdp(self):
        self.validate_file(vdp_sbml, ucheck=False)

if __name__ == '__main__':
    unittest.main()
