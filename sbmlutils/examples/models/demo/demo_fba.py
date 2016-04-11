"""
Check the charge and formula balance of the model.
Run some simple FBA simulations.
"""
from __future__ import print_function, division
import os
import cobra
import libsbml
from sbmlutils import fbc

curdir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    path = os.path.join(curdir, 'Koenig_demo_10.xml')
    doc = libsbml.readSBMLFromFile(path)

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
