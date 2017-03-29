"""
Reactions and transporters of test model.
"""
from sbmlutils import factory as mc

from sbmlutils.modelcreator.processes import ReactionTemplate

#############################################################################################
#    REACTIONS
#############################################################################################

GLUT2_GAL = ReactionTemplate(
    rid='e__GLUT2_GAL',
    name='galactose transport [e__]',
    equation='e__gal <-> c__gal []',
    # C6H1206 (0) <-> C6H1206 (0)
    compartment='pm',
    pars=[
            mc.Parameter(sid='GLUT2_Vmax', value=1E-13, unit='mole_per_s'),
            mc.Parameter('GLUT2_k_gal', 1.0, 'mM'),
            mc.Parameter('GLUT2_keq', 1.0, '-'),
    ],
    formula=('GLUT2_Vmax/GLUT2_k_gal * (e__gal - c__gal/GLUT2_keq)/'
             '(1 dimensionless + c__gal/GLUT2_k_gal + e__gal/GLUT2_k_gal) ', 'mole_per_s')
)
