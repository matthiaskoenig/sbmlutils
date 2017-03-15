"""
Unit tests for fbc.
"""
from __future__ import print_function
import cobra
import libsbml

import sbmlutils.fbc as fbc
from sbmlutils.tests import data


def test_mass_balance():

    doc = libsbml.readSBMLFromFile(data.DEMO_SBML)

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
