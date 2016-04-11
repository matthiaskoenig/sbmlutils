"""
Check the charge and formula balance of the model.
Run some simple FBA simulations.
"""

from __future__ import print_function, division
import os
from sbmlutils import fbc
from sbmlutils.examples import testfiles


if __name__ == "__main__":
    sbml_path = testfiles.galactose_singlecell_sbml

    fbc.check_balance(sbml_path)
    model = fbc.load_cobra_model(sbml_path)







