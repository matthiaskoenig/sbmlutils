"""
Settings for toy model.
"""
from __future__ import print_function, division
import os

# output directory
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

# model files
fba_file = 'toy_fba.xml'
bounds_file = 'toy_bounds.xml'
update_file = 'toy_update.xml'
top_file = 'toy_top.xml'
flattened_file = 'toy_flattened.xml'
