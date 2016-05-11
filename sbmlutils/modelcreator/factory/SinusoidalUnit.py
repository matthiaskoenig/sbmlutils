"""
Model factory for the creation of the sinusoidal metabolic models.
Cellular models are integrated into the sinusoidal structure.
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
    'Pa': [(UNIT_KIND_PASCAL, 1.0)],
    'Pa_s': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0)],
    'Pa_s_per_m4': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                     (UNIT_KIND_METRE, -4.0)],
    'Pa_s_per_m3': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                     (UNIT_KIND_METRE, -3.0)],
    'Pa_s_per_m2': [(UNIT_KIND_PASCAL, 1.0), (UNIT_KIND_SECOND, 1.0),
                     (UNIT_KIND_METRE, -2.0)],
    'm6_per_Pa2_s2': [(UNIT_KIND_PASCAL, -2.0), (UNIT_KIND_SECOND, -2.0),
                     (UNIT_KIND_METRE, 6.0)],
    
}

##########################################################################
# Parameters
##########################################################################
pars.extend([
            # id, value, unit, constant
            ('L',           500E-6,   'm',      True),
            ('y_sin',       4.4E-6,   'm',      True),
            ('y_end',     0.165E-6,   'm',      True),
            ('y_dis',       2.3E-6,   'm',      True),
            ('y_cell',     9.40E-6,   'm',      True),
            
            ('N_fen',        10E12,   'per_m2', True),
            ('r_fen',      53.5E-9,   'm',      True),
            
            ('rho_liv',     1.25E3,    'kg_per_m3', True), 
            ('f_tissue',     0.8, '-', True),
            ('f_cyto',       0.4, '-', True),
            
            ('Pa',       1333.22, 'Pa', True), # 1mmHg = 133.322
            ('Pb',       266.64,  'Pa', True), 
            ('nu_f',     10.0, '-', True),
            ('nu_plasma', 0.0018, 'Pa_s', True),
])
names['Nc'] = 'number of cells in sinusoidal unit'
names['Nf'] = 'external compartments per cell'
names['L'] = 'sinusoidal length'
names['y_sin'] = 'sinusoidal radius'
names['y_end'] = 'endothelial cell thickness'
names['y_dis'] = 'width space of Disse'
names['y_cell'] = 'width hepatocyte'
names['flow_sin'] = 'sinusoidal flow velocity'
names['N_fen'] = 'fenestrations per area'
names['r_fen'] = 'fenestration radius'

names['rho_liv'] = 'liver density'
names['f_tissue'] = 'parenchymal fraction of liver'
names['f_cyto'] = 'cytosolic fraction of hepatocyte'

names['Pa'] = 'pressure periportal'
names['Pb'] = 'pressure perivenious'
names['Pa_per_mmHg'] = 'conversion factor between Pa and mmHg'
names['nu_f'] = 'viscosity factor for sinusoidal resistance'
names['nu_plasma'] = 'plasma viscosity'

names['Nc'] = 'hepatocytes in sinusoid'
names['scale_f'] = 'metabolic scaling factor'
names['REF_P'] = 'reference protein amount'
names['deficiency'] = 'type of galactosemia'
names['gal_challenge'] = 'galactose challenge periportal'

##########################################################################
# AssignmentRules
##########################################################################
rules.extend([
            # id, assignment, unit
            ('x_cell', 'L/Nc', 'm'),
            ('x_sin',  "x_cell/Nf", "m"),
            ("A_sin", "pi*y_sin^2",  "m2"),
            ("A_dis", "pi*(y_sin+y_end+y_dis)^2 - pi*(y_sin+y_end)^2",  "m2"),
            ("A_sindis", "2 dimensionless *pi*y_sin*x_sin",  "m2"),
            ("A_sinunit", "pi*(y_sin+y_end+y_dis+y_cell)^2",  "m2"),
            ("Vol_sin", "A_sin*x_sin",  "m3"),
            ("Vol_dis", "A_dis*x_sin",  "m3"),
            ("Vol_cell", "pi*x_cell*( (y_sin+y_end+y_dis+y_cell)^2-(y_sin+y_end+y_dis)^2 )", "m3"),
            ("Vol_cyto", "f_cyto*Vol_cell",  "m3"),
            ("Vol_pp", "Vol_sin", "m3"),
            ("Vol_pv", "Vol_sin", "m3"),
            ("Vol_sinunit", "L*pi*(y_sin+y_end+y_dis+y_cell)^2", "m3"),
            ("f_sin",  "Vol_sin/(A_sinunit*x_sin)", '-'),
            ("f_dis", "Vol_dis/(A_sinunit*x_sin)", '-'),
            ("f_cell", "Vol_cell/(A_sinunit*x_sin)", '-'),
            ('flow_sin',    'PP_Q/A_sin',   'm_per_s'),
            ("Q_sinunit", "PP_Q", "m3_per_s"),
            ("f_fen", "N_fen*pi*(r_fen)^2", '-'),
            # ("m_liv", "rho_liv * Vol_liv", "kg"),
            # ("q_liv" , "Q_liv/m_liv", "m3_per_skg"),
            ("P0", "0.5 dimensionless * (Pa+Pb)", 'Pa'),
            ("nu", "nu_f * nu_plasma", 'Pa_s'),
            ("W", "8 dimensionless * nu/(pi*y_sin^4)", 'Pa_s_per_m4'),
            ("w", "4 dimensionless *nu*y_end/(pi^2* r_fen^4*y_sin*N_fen)", 'Pa_s_per_m2'),
            ("lambda", "sqrt(w/W)", 'm'),
])

names['x_cell'] = 'length cell compartment'
names['x_sin'] = 'length sinusoidal compartment'
names['A_sin'] = 'cross section sinusoid'
names['A_dis'] = 'cross section space of Disse'
names['A_sindis'] = 'exchange area between sinusoid and Disse'
names['A_sinunit'] = 'cross section sinusoidal unit'
names['Vol_sin'] = 'volume sinusoidal compartment'
names['Vol_dis'] = 'volume Disse compartment'
names['Vol_cell'] = 'volume cell compartment'
names['Vol_pp'] = 'volume periportal'
names['Vol_pv'] = 'volume perivenious'
names['Vol_sinunit'] = 'total volume sinusoidal unit'
names['f_sin'] = 'sinusoidal fraction of volume'
names['f_dis'] = 'Disse fraction of volume'
names['f_cell'] = 'cell fraction of volume'
names['Q_sinunit'] = 'volume flow sinusoid'
names['f_cyto'] = 'cytosolic fraction of cell volume'
names['f_fen'] = 'fenestration porosity'
names['P0'] = 'resulting oncotic pressure P0 = Poc-Pot'
names['nu'] = 'hepatic viscosity'
names['W'] = 'specific hydraulic resistance capillary'
names['w'] = 'specific hydraulic resistance of all pores'
    

##########################################################################
# InitialAssignments
##########################################################################
assignments.extend([])
