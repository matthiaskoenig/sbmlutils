"""
Check the charge and formula balance of the model.
"""
from __future__ import print_function, division

import os
from sbmlutils import fbc

import Cell

glucose_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'results',
                            '{}_{}.xml'.format(Cell.mid, Cell.version))

if __name__ == "__main__":
    fbc.check_balance(glucose_sbml)
    model = fbc.load_cobra_model(glucose_sbml)
