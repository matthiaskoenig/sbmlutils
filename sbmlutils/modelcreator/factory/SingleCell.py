"""
Model factory for the creation of single cell model
Cellular models are integrated with the external structure.

A modular structure of processes for the single hepatocyte processes and transporters
exists which allows to reuse the created sinusoidal model for various simulations, like
clearance of a variety of substances.

Important features:
- important is a fast turnover between changes and simulations. 
  Currently this is quit cumbersome and necessary to write down the full network.
- single cell models as well as the full sinusoidal architecture have to be generated 
  at once.

"""

from libsbml import UNIT_KIND_SECOND, UNIT_KIND_MOLE,\
    UNIT_KIND_METRE,UNIT_KIND_KILOGRAM
from _libsbml import UNIT_KIND_PASCAL, UNIT_KIND_DIMENSIONLESS

#########################################################################

units = dict()
names = dict()
pars = []
external = []
assignments = []
rules = []

#########################################################################
# Main Units
##########################################################################
main_units = {
    'time': 's',
    'extent': UNIT_KIND_MOLE,
    'substance': UNIT_KIND_MOLE,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}
#########################################################################
# Units
##########################################################################
# units (kind, exponent, scale=0, multiplier=1.0)
# u_new = (multiplier  
units = {
    's': [(UNIT_KIND_SECOND, 1.0)],
    'kg': [(UNIT_KIND_KILOGRAM, 1.0)],
    'm': [(UNIT_KIND_METRE, 1.0)],
    'm2': [(UNIT_KIND_METRE, 2.0)],
    'm3': [(UNIT_KIND_METRE, 3.0)],
    'per_s': [(UNIT_KIND_SECOND, -1.0)],
    'mole_per_s': [(UNIT_KIND_MOLE, 1.0),
                       (UNIT_KIND_SECOND, -1.0)],
    'mole_per_s_per_mM': [(UNIT_KIND_METRE, 3.0),
                       (UNIT_KIND_SECOND, -1.0) ],
    'mole_per_s_per_mM2': [(UNIT_KIND_MOLE, -1.0), (UNIT_KIND_METRE, 6.0),
                       (UNIT_KIND_SECOND, -1.0) ],
    'm_per_s': [(UNIT_KIND_METRE, 1.0),
                    (UNIT_KIND_SECOND, -1.0)],
    'm2_per_s': [(UNIT_KIND_METRE, 2.0),
                    (UNIT_KIND_SECOND, -1.0)],
    'm3_per_s': [(UNIT_KIND_METRE, 3.0),
                    (UNIT_KIND_SECOND, -1.0)],
    'mM': [(UNIT_KIND_MOLE, 1.0, 0),
                    (UNIT_KIND_METRE, -3.0)],
    'mM_s': [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, 1.0),
                    (UNIT_KIND_METRE, -3.0)],
    'per_mM': [(UNIT_KIND_METRE, 3.0),
                    (UNIT_KIND_MOLE, -1.0)],
    'per_m2': [(UNIT_KIND_METRE, -2.0)],
    'per_m3': [(UNIT_KIND_METRE, -3.0)],
    'kg_per_m3': [(UNIT_KIND_KILOGRAM, 1.0),
                    (UNIT_KIND_METRE, -3.0)],
    'm3_per_skg': [(UNIT_KIND_METRE, 3.0),
                    (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_SECOND, -1.0)],
}

##########################################################################
# Parameters
##########################################################################
pars.extend([
            # id, value, unit, constant
            ('y_ext',      9.40E-6,   'm',      True),
            ('y_cell',     9.40E-6,   'm',      True),
            ('x_cell',      25.0E-6,   'm',      True),
            ('f_tissue',     0.8, '-', True),
            ('f_cyto',       0.4, '-', True),
])
names['y_ext'] = 'width external compartment'
names['y_cell'] = 'width hepatocyte'
names['f_tissue'] = 'parenchymal fraction of liver'
names['f_cyto'] = 'cytosolic fraction of hepatocyte'

names['scale_f'] = 'metabolic scaling factor'
names['REF_P'] = 'reference protein amount'
names['deficiency'] = 'type of galactosemia'
names['gal_challenge'] = 'galactose challenge periportal'

##########################################################################
# AssignmentRules
##########################################################################
rules.extend([
            # id, assignment, unit
            ("Vol_cell", "x_cell*x_cell*y_cell", "m3"),
            ("Vol_ext", "x_cell*x_cell*y_ext",  "m3"),
            ("Vol_cyto", "f_cyto*Vol_cell",  "m3"),
])

names['x_cell'] = 'length cell compartment'
names['Vol_cell'] = 'volume cell compartment'
names['Vol_ext'] = 'volume external compartment'

##########################################################################
# InitialAssignments
##########################################################################
assignments.extend([])
