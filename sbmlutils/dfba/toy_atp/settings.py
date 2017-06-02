"""
Settings for toy model.
"""
from __future__ import print_function, division
import os

# output directory
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

model_id = 'toy_atp'

# model files
fba_file = '{}_fba.xml'.format(model_id)
bounds_file = '{}_bounds.xml'.format(model_id)
update_file = '{}_update.xml'.format(model_id)
top_file = '{}_top.xml'.format(model_id)
flattened_file = '{}_flattened.xml'.format(model_id)
