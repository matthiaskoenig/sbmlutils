"""
Definition of constants.
"""

from __future__ import absolute_import, print_function
import os


MODEL_ID = 'diauxic'
VERSION = 13
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

FBA_LOCATION = '{}_fba.xml'.format(MODEL_ID)
BOUNDS_LOCATION = '{}_bounds.xml'.format(MODEL_ID)
UPDATE_LOCATION = '{}_update.xml'.format(MODEL_ID)
TOP_LOCATION = '{}_top.xml'.format(MODEL_ID)
FLATTENED_LOCATION = '{}_flattened.xml'.format(MODEL_ID)

# SED-ML
SEDML_LOCATION = 'dfba_simulation.xml'.format(MODEL_ID)

# Combine archive
OMEX_LOCATION = '{}_v{}.omex'.format(MODEL_ID, VERSION)

# annotations
ANNOTATIONS_LOCATION = 'annotations.xlsx'

