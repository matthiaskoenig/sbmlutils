"""
Definition of constants.
"""

from __future__ import absolute_import, print_function
import os


OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

MODEL_ID = 'diauxic'

FBA_LOCATION = '{}_fba.xml'.format(MODEL_ID)
BOUNDS_LOCATION = '{}_bounds.xml'.format(MODEL_ID)
UPDATE_LOCATION = '{}_update.xml'.format(MODEL_ID)
TOP_LOCATION = '{}_top.xml'.format(MODEL_ID)
FLATTENED_LOCATION = '{}_flattened.xml'.format(MODEL_ID)

# annotations
ANNOTATIONS_LOCATION = 'annotations.xlsx'

# SED-ML
SEDML_LOCATION = 'dfba_simulation.xml'.format(MODEL_ID)

# Combine archive
OMEX_LOCATION = '{}.omex'.format(MODEL_ID)

# ExternalModelDefinitions removed
top_noemd_file = '{}_top_noemd.xml'.format(MODEL_ID)
flattened_noemd_file = '{}_flattened_noemd.xml'.format(MODEL_ID)
