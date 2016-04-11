"""
Check the charge and formula balance of the model.

Run some simple FBA simulations.
"""

from __future__ import print_function, division
from sbmlutils import fbc
from sbmlutils.examples import testfiles

if __name__ == "__main__":
    path = testfiles.glucose_sbml
    print(path)
    fbc.check_balance(path)
    model = fbc.load_cobra_model(path)
