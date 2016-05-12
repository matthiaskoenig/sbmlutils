"""
Reactions and transporters of demo metabolism.
"""
from sbmlutils.modelcreator.processes.ReactionTemplate import ReactionTemplate

#############################################################################################
#    REACTIONS
#############################################################################################
bA = ReactionTemplate(
    rid='bA',
    name='bA (A import)',
    equation='e__A => c__A []',
    localization='m',
    compartments=['c, e'],
    pars=[],
    rules=[],
    formula=('scale_f*(Vmax_bA/Km_A)*(e__A - c__A)/ (1 dimensionless + e__A/Km_A + c__A/Km_A)', 'mole_per_s')
)


bB = ReactionTemplate(
    rid='bB',
    name='bB (B export)',
    equation='c__B => e__B []',
    localization='m',
    compartments=['c, e'],
    pars=[],
    rules=[],
    formula=('(scale_f*(Vmax_bB/Km_B)*(c__B - e__B))/(1 dimensionless + e__B/Km_B + c__B/Km_B)', 'mole_per_s')
)

bC = ReactionTemplate(
    rid='bC',
    name='bC (C export)',
    equation='c__C => e__C []',
    localization='m',
    compartments=['c, e'],
    pars=[],
    rules=[],
    formula=('(scale_f*(Vmax_bC/Km_C)*(c__C - e__C))/(1 dimensionless + e__C/Km_C + c__C/Km_C)', 'mole_per_s')
)

v1 = ReactionTemplate(
    rid='v1',
    name='v1 (A -> B)',
    equation='c__A -> c__B []',
    localization='c',
    compartments=['c'],
    formula=('(scale_f*Vmax_v1)/Km_A*(c__A - 1 dimensionless/Keq_v1*c__B)', 'mole_per_s')
)

v2 = ReactionTemplate(
    rid='v2',
    name='v2 (A -> C)',
    equation='c__A -> c__C []',
    localization='c',
    compartments=['c'],
    formula=('(scale_f*Vmax_v2)/Km_A*c__A', 'mole_per_s')
)

v3 = ReactionTemplate(
    rid='v3',
    name='v3 (C -> A)',
    equation='c__C -> c__A []',
    localization='c',
    compartments=['c'],
    formula=('(scale_f*Vmax_v3)/Km_A*c__C', 'mole_per_s')
)

v4 = ReactionTemplate(
    rid='v4',
    name='v4 (C -> B)',
    equation='c__C -> c__B []',
    localization='c',
    compartments=['c'],
    formula=('(scale_f*Vmax_v4)/Km_A*(c__C - 1 dimensionless/Keq_v4*c__B)', 'mole_per_s')
)
