"""
Database of information reused in sinusoidal models.

These are mainly the transport properties.
Necessary to have a database of all the values used in modelling and their sources.
"""
from __future__ import print_function

from sbmlutils.factory import Parameter

# -------------------------------------------------------------------------
# Diffusion Parameters
# -------------------------------------------------------------------------
# diffusion constants [m^2/s]
diffusion = {
    'h2o': Parameter('Dh2o', 2300E-12, 'm2_per_s', name='diffusion constant water M*'),
    'h2oM': Parameter('Dh2oM', 2300E-12, 'm2_per_s', name='diffusion constant water M'),
    'gal': Parameter('Dgal', 910E-12, 'm2_per_s', name='diffusion constant galactose'),
    'galM': Parameter('DgalM', 910E-12, 'm2_per_s', name='diffusion constant galactose M*'),
    'suc': Parameter('Dsuc', 720E-12, 'm2_per_s', name='diffusion constant sucrose'),
    'alb': Parameter('Dalb', 90E-12, 'm2_per_s', name='diffusion constant albumin'),
    'rbcM': Parameter('DrbcM', 0.0E-12, 'm2_per_s', name='diffusion constant rbc M*'),

    'S': Parameter('DS', 910E-12, 'm2_per_s', name='diffusion constant S'),
    'P': Parameter('DP', 720E-12, 'm2_per_s', name='diffusion constant P'),

}

# effective radius [m]
radius = {
    'h2o': Parameter('r_h2oM', 0.15E-9, 'm', name='effective radius water M*'),
    'gal': Parameter('r_gal', 0.36E-9, 'm', name='effective radius galactose'),
    'galM': Parameter('r_galM', 0.36E-9, 'm', name='effective radius galactose M*'),
    'suc': Parameter('r_suc', 0.44E-9, 'm', name='effective radius sucrose'),
    'alb': Parameter('r_alb', 3.64E-9, 'm', name='effective radius albumin'),
    'rbcM': Parameter('r_rbcM', 3000E-9, 'm', name='effective radius RBC M*'),

    'S': Parameter('r_S', 0.36E-9, 'm', name='effective radius S'),
    'P': Parameter('r_P', 0.44E-9, 'm', name='effective radius P'),
}
