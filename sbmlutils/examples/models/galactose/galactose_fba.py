"""
Check the charge and formula balance of the model.
Run some simple FBA simulations.
"""
from __future__ import print_function, division
import os
import cobra
from multiscale.sbmlutils import fbc

curdir = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":

    path = os.path.join(curdir, 'galactose_30.xml')
    fbc.check_balance(path)

    model = fbc.load_cobra_model(path)







