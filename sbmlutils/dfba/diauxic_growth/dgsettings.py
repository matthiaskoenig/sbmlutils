"""
Settings for diauxic growth model.
"""
from __future__ import print_function, division
import os

# directory to write files to
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

# FBA submodel
fba_file = 'diauxic_fba.xml'
# ODE submodels
bounds_file = 'diauxic_bounds.xml'
update_file = 'diauxic_update.xml'
ode_file = 'diauxic_ode.xml'

# top level
comp_file = 'diauxic_comp.xml'
# flattened top level
flattened_file = 'diauxic_flattened.xml'
