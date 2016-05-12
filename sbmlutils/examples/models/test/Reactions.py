"""
Reactions and transporters of test model.
"""
from sbmlutils.modelcreator.processes.ReactionTemplate import ReactionTemplate

#############################################################################################
#    REACTIONS
#############################################################################################

GLUT2_GAL = ReactionTemplate(
    rid='e__GLUT2_GAL',
    name='galactose transport [e__]',
    equation='e__gal <-> c__gal []',
    # C6H1206 (0) <-> C6H1206 (0)
    localization='pm',
    compartments=['cyto__', 'ext__'],
    pars=[
            ('GLUT2_Vmax',    1E-13,   'mole_per_s'),
            ('GLUT2_k_gal', 1.0, 'mM'),
            ('GLUT2_keq', 1.0, '-'),
    ],
    formula=('GLUT2_Vmax/GLUT2_k_gal * (e__gal - c__gal/GLUT2_keq)/(1 dimensionless + c__gal/GLUT2_k_gal + e__gal/GLUT2_k_gal) ', 'mole_per_s')
)

