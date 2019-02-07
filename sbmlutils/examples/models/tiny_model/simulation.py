"""
Check the charge and formula balance of the model.
Run some simple FBA simulations.
"""
from __future__ import print_function, division

import os

import model
import cobra
import libsbml
from sbmlutils import fbc
import roadrunner
import pandas as pd


# SBML file
tiny_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'results',
                         '{}_{}.xml'.format(model.mid, model.version))


r = roadrunner.RoadRunner(tiny_sbml)
print(r)
s = r.simulate(0, 100, steps=100)
df = pd.DataFrame(s, columns=s.colnames)
print(df.head(10))
# r.plot()
