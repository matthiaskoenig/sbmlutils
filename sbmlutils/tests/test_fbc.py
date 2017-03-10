"""
Unit tests for fbc.
"""

import unittest

import libsbml
import cobra
import sbmlutils.fbc as fbc
from sbmlutils.tests import resources


class FBCTestCase(unittest.TestCase):
    def test_mass_balance(self):

        doc = libsbml.readSBMLFromFile(resources.DEMO_SBML)

        # add defaults
        fbc.add_default_flux_bounds(doc)

        import tempfile
        f = tempfile.NamedTemporaryFile('w', suffix='xml')
        libsbml.writeSBMLToFile(doc, f.name)
        f.flush()
        model = cobra.io.read_sbml_model(f.name)

        # mass/charge balance
        for r in model.reactions:
            mb = r.check_mass_balance()
            print(r.id, mb)


if __name__ == '__main__':
    unittest.main()
