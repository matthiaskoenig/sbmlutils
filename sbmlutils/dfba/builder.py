"""
Building DFBA models by providing.

FBA SBML models in combination with the variable species.


"""
from __future__ import print_function, division
import logging
import warnings

#################################################
# Logging
#################################################
logging.basicConfig(format='%(message)s', level=logging.DEBUG)

#################################################
# Builder constants
#################################################

LOWER_BOUND_DEFAULT = -1000
UPPER_BOUND_DEFAULT = 1000
LOWER_BOUND_PREFIX = 'lb'
UPPER_BOUND_PREFIX = 'ub'
