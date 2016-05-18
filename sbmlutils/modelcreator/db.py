"""
Database of information reused in sinusoidal models.

These are mainly the transport properties.
Necessary to have a database of all the values used in modelling and their sources.
"""

# -------------------------------------------------------------------------
# Diffusion Parameters
# -------------------------------------------------------------------------
# diffusion constants [m^2/s]
diffusion = {
    'h2o': ('Dh2o', 2300E-12, 'm2_per_s', 'diffusion constant water M*'),
    'h2oM': ('Dh2oM', 2300E-12, 'm2_per_s', 'diffusion constant water M'),
    'gal': ('Dgal', 910E-12, 'm2_per_s', 'diffusion constant galactose'),
    'galM': ('DgalM', 910E-12, 'm2_per_s', 'True', 'diffusion constant galactose M*'),

    'suc': ('Dsuc', 720E-12, 'm2_per_s', 'True', 'diffusion constant sucrose'),
    'alb': ('Dalb', 90E-12, 'm2_per_s', 'True', 'diffusion constant albumin'),
    'rbcM': ('DrbcM', 0.0E-12, 'm2_per_s', 'True', 'diffusion constant rbc M*'),
}

# effective radius [m]
radius = {
    'h2o': ('r_h2oM', 0.15E-9, 'm', 'effective radius water M*'),
    'gal': ('r_gal', 0.36E-9, 'm', 'effective radius galactose'),
    'galM': ('r_galM', 0.36E-9, 'm', 'effective radius galactose M*'),
    'suc': ('r_suc', 0.44E-9, 'm', 'effective radius sucrose'),
    'alb': ('r_alb', 3.64E-9, 'm', 'effective radius albumin'),
    'rbcM': ('r_rbcM', 3000E-9, 'm', 'effective radius RBC M*'),
}
