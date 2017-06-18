"""
Settings for diauxic growth model.
"""
from __future__ import print_function, division
import os

# directory to write files to
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

model_id = 'diauxic'

fba_file = '{}_fba.xml'.format(model_id)
bounds_file = '{}_bounds.xml'.format(model_id)
update_file = '{}_update.xml'.format(model_id)
top_file = '{}_top.xml'.format(model_id)
flattened_file = '{}_flattened.xml'.format(model_id)

# annotations
annotations_file = 'annotations.xlsx'

# ExternalModelDefinitions removed
top_noemd_file = '{}_top_noemd.xml'.format(model_id)
flattened_noemd_file = '{}_flattened_noemd.xml'.format(model_id)
