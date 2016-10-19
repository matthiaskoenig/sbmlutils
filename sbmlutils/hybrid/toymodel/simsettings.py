"""
Settings for toy model.
"""
from __future__ import print_function, division
import os

# directory to write files to
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models')

# FBA submodel
fba_file = 'toy_fba.xml'
# ODE submodels
ode_bounds_file = 'toy_ode_bounds.xml'
ode_update_file = 'toy_ode_update.xml'
ode_model_file = 'toy_ode_model.xml'
# top level
top_level_file = 'toy_top_level.xml'
# flattened top level
flattened_file = 'flattened.xml'
