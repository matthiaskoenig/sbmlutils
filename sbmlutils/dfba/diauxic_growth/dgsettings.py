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

ode_update_file = 'diauxic_ode_update.xml'
ode_model_file = 'diauxic_ode_model.xml'
# top level
top_level_file = 'diauxic_top_level.xml'
# flattened top level
flattened_file = 'diauxic_flattened.xml'
