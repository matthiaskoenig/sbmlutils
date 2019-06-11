# -*- coding=utf-8 -*-
"""
Distrib example.
"""

from sbmlutils.units import *
from sbmlutils.factory import *
from sbmlutils.modelcreator import templates

# -----------------------------------------------------------------------------
mid = 'distrib_ex1'
version = 1
creators = templates.creators
notes = Notes([
    """
    <h1>sbmlutils {}</h1>
    <h2>Description</h2>
    <p>Example creating distrib model with distribution elements.</p>
    """,
    templates.terms_of_use
])

# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------

model_units = ModelUnits(time=UNIT_h, extent=UNIT_KIND_MOLE, substance=UNIT_KIND_MOLE,
                         length=UNIT_m, area=UNIT_m2, volume=UNIT_KIND_LITRE)
units = [
    UNIT_h, UNIT_m, UNIT_m2,
]

# -----------------------------------------------------------------------------
# InitialAssignments
# -----------------------------------------------------------------------------
assignments = [
    InitialAssignment('p_normal_1', 'normal(0, 1)'),
    InitialAssignment('p_normal_2', 'normal(0, 1, 0, 10)'),
    InitialAssignment('p_uniform', 'uniform(5, 10)'),
    InitialAssignment('p_bernoulli', 'bernoulli(0.4)'),
    InitialAssignment('p_binomial_1', 'binomial(100, 0.3)'),
    InitialAssignment('p_binomial_2', 'binomial(100, 0.3, 0, 2)'),
    InitialAssignment('p_cauchy_1', 'cauchy(0, 1)'),
    InitialAssignment('p_cauchy_2', 'cauchy(0, 1, 0, 5)'),
    InitialAssignment('p_chisquare_1', 'chisquare(10)'),
    InitialAssignment('p_chisquare_2', 'chisquare(10, 0, 10)'),
    InitialAssignment('p_exponential_1', 'exponential(1.0)'),
    InitialAssignment('p_exponential_2', 'exponential(1.0, 0, 10)'),
    InitialAssignment('p_gamma_1', 'gamma(0, 1)'),
    InitialAssignment('p_gamma_2', 'gamma(0, 1, 0, 10)'),
    InitialAssignment('p_laplace_1', 'laplace(0, 1)'),
    InitialAssignment('p_laplace_2', 'laplace(0, 1, 0, 10)'),
    InitialAssignment('p_lognormal_1', 'lognormal(0, 1)'),
    InitialAssignment('p_lognormal_2', 'lognormal(0, 1, 0, 10)'),
    InitialAssignment('p_poisson_1', 'poisson(0.5)'),
    InitialAssignment('p_poisson_2', 'poisson(0.5, 0, 10)'),
    InitialAssignment('p_raleigh_1', 'rayleigh(0.5)'),
    InitialAssignment('p_raleigh_2', 'rayleigh(0.5, 0, 10)'),
]
