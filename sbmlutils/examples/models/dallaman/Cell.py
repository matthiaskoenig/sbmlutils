# -*- coding=utf-8 -*-
"""
DallaMan2006

"""
from libsbml import UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE
from libsbml import XMLNode
from sbmlutils.modelcreator import templates
from sbmlutils import factory as mc

##############################################################
creators = templates.creators
mid = 'Hepatic_glucose'
version = 3
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>DallaMan2006 - Glucose Insulin System</h1>
    <h2>Description</h2>
    <p>
        This is a A simulation model of the glucose-insulin system in the postprandial state in <a href="http://sbml.org">SBML</a> format.
    </p>
    <p>This model is described in the article:</p>
    <div class="bibo:title">
        <a href="http://identifiers.org/pubmed/17926672" title="Access to this publication">Meal simulation model of the glucose-insulin system.</a>
    </div>
    <div class="bibo:authorList">Dalla Man C, Rizza RA, Cobelli C.</div>
    <div class="bibo:Journal">IEEE Trans Biomed Eng. 2007 Oct;54(10):1740-9.</div>
    <p>Abstract:</p>
    <div class="bibo:abstract">
    <p>Asimulation model of the glucose-insulin system in the
postprandial state can be useful in several circumstances, including
testing of glucose sensors, insulin infusion algorithms and decision
support systems for diabetes. Here, we present a new simulation
model in normal humans that describes the physiological events
that occur after a meal, by employing the quantitative knowledge
that has become available in recent years. Model parameters were
set to fit the mean data of a large normal subject database that underwent
a triple tracer meal protocol which provided quasi-modelindependent
estimates of major glucose and insulin fluxes, e.g., meal
rate of appearance, endogenous glucose production, utilization of
glucose, insulin secretion.</p>
    </div>
    """ + templates.terms_of_use + """
    </body>
    """)

main_units = {
    'time': 's',
    'extent': UNIT_KIND_MOLE,
    'substance': UNIT_KIND_MOLE,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}
units = list()
functions = list()
compartments = list()
species = list()
parameters = list()
names = list()
assignments = list()
rules = list()
reactions = list()

#########################################################################
# Units
##########################################################################
units.extend([
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0)]),
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    mc.Unit('per_s', [(UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('min', [(UNIT_KIND_SECOND, 1.0, 0, 60)]),
    mc.Unit('s_per_min', [(UNIT_KIND_SECOND, 1.0),
                          (UNIT_KIND_SECOND, -1.0, 0, 60)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0),
                   (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('per_mM', [(UNIT_KIND_METRE, 3.0),
                       (UNIT_KIND_MOLE, -1.0)]),
    mc.Unit('mM2', [(UNIT_KIND_MOLE, 2.0),
                    (UNIT_KIND_METRE, -6.0)]),
    mc.Unit('mole_per_s', [(UNIT_KIND_MOLE, 1.0),
                           (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('pmol', [(UNIT_KIND_MOLE, 1.0, -12, 1.0)]),
    mc.Unit('pM', [(UNIT_KIND_MOLE, 1.0, -12, 1.0),
                   (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('mumol_per_min_kg', [(UNIT_KIND_MOLE, 1.0, -6, 1.0),
                                 (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_KILOGRAM, -1.0)]),
    mc.Unit('s_per_min_kg', [(UNIT_KIND_SECOND, 1.0),
                             (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_KILOGRAM, -1.0)]),
])

##############################################################
# Functions
##############################################################
functions.extend([
    mc.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='minimum of arguments'),
    mc.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='maximum of arguments'),
])

##############################################################
# Compartments
##############################################################
compartments.extend([
    mc.Compartment(sid='ext', unit='m3', constant=False, value='V_ext', name='blood'),
    mc.Compartment(sid='cyto', unit='m3', constant=False, value='V_cyto', name='cytosol'),
    mc.Compartment(sid='mito', unit='m3', constant=False, value='V_mito', name='mitochondrion'),
    mc.Compartment(sid='pm', spatialDimension=2, unit='m2', constant=True, value='1.0 m2', name='plasma membrane'),
    mc.Compartment(sid='mm', spatialDimension=2, unit='m2', constant=True, value='1.0 m2',
                   name='mitochondrial membrane'),
])

##############################################################
# Species
##############################################################
species.extend([
    mc.Species('atp', compartment='cyto', value=2.8000, unit='mM', boundaryCondition=True, name='ATP'),
])

##############################################################
# Parameters
##############################################################
parameters.extend([

    mc.Parameter('BW', 78, 'kg', constant=True, name='bodyweight'),
    mc.Parameter('D', 78000, '?', constant=True),

    # Glucose Kinetics
    mc.Parameter('V_G', 1.88, 'dl_per_kg', constant=True, name='V_G glucose kinetics'),
    mc.Parameter('k_1', 0.065, 'per_min', constant=true, name='k_1 glucose kinetics'),
    mc.Parameter('k_2', 0.079, 'per_min', constant=True, name='k_2 glucose kinetics'),
    mc.Parameter('G_b', 95, '?', constant=True),

    # Insulin kinetics
    mc.Parameter('V_I', 0.05, 'l_per_kg', constant=True),
    mc.Parameter('m_1', 0.190, 'per_min', constant=True),
    mc.Parameter('m_2', 0.484, 'per_min', constant=True),
    mc.Parameter('m_4', 0.194, 'per_min', constant=True),
    mc.Parameter('m_5', 0.0304, 'minkg_pmol', constant=True),
    mc.Parameter('m_6', 0.6471, '-', constant=True),
    mc.Parameter('HE_b', 0.60, '-', constant=True),
    I_b = 25
    S_b = 1.8
# Rate of appearance
k_max = 0.055800000000000002
k_min = 0.0080000000000000002
k_abs = 0.057000000000000002
k_gri = 0.055800000000000002
f = 0.90000000000000002
b = 0.81999999999999995
d = 0.01
# Endogenous production
k_p1 = 2.7000000000000002
k_p2 = 0.0020999999999999999
k_p3 = 0.0089999999999999993
k_p4 = 0.061800000000000001
k_i = 0.0079000000000000008
# Utilization
U_ii = 1
V_m0 = 2.5
V_mX = 0.047
K_m0 = 225.59
V_f0 = 2.5
V_fX = 0.047
K_f0 = 225.59
p_2U = 0.033099999999999997
part = 0.20000000000000001
# Secretion
K = 2.2999999999999998
alpha = 0.050000000000000003
beta = 0.11
gamma = 0.5
# renal excretion
k_e1 = 0.00050000000000000001
k_e2 = 339



])

##############################################################
# Assignments
##############################################################
assignments.extend([
    mc.InitialAssignment('V_ext', 'f_ext * V_cyto', 'm3', name='external volume'),
    mc.InitialAssignment('V_mito', 'f_mito * V_cyto', 'm3', name='mitochondrial volume'),
    mc.InitialAssignment('conversion_factor', 'fliver*Vliver/V_cyto*sec_per_min * 1E3 dimensionless/bodyweight',
                         's_per_min_kg'),

    # scaling factors
    mc.InitialAssignment('scale', '1 dimensionless /60 dimensionless', 'dimensionless', name='scaling factor rates'),
    mc.InitialAssignment('f_gly', 'scale', 'dimensionless', name='scaling factor glycolysis'),
    mc.InitialAssignment('f_glyglc', 'scale', 'dimensionless', name='scaling factor glycogen metabolism'),
])

##############################################################
# Rules
##############################################################
rules.extend([
    # hormonal regulation
    mc.AssignmentRule('ins', 'x_ins2 + (x_ins1-x_ins2) * glc_ext^x_ins4/(glc_ext^x_ins4 + x_ins3^x_ins4)', 'pM',
                      name='insulin'),
    mc.AssignmentRule('ins_norm', 'max(0.0 pM, ins-x_ins2)', 'pM', name='insulin normalized'),
    mc.AssignmentRule('glu',
                      'x_glu2 + (x_glu1-x_glu2)*(1 dimensionless - glc_ext^x_glu4/(glc_ext^x_glu4 + x_glu3^x_glu4))',
                      'pM', name='glucagon'),
    mc.AssignmentRule('glu_norm', 'max(0.0 pM, glu-x_glu2)', 'pM', name='glucagon normalized'),
    mc.AssignmentRule('epi',
                      'x_epi2 + (x_epi1-x_epi2) * (1 dimensionless - glc_ext^x_epi4/(glc_ext^x_epi4 + x_epi3^x_epi4))',
                      'pM', name='epinephrine'),
    mc.AssignmentRule('epi_norm', 'max(0.0 pM, epi-x_epi2)', 'pM', name='epinephrine normalized'),
    mc.AssignmentRule('K_ins', '(x_ins1-x_ins2) * K_val', 'pM'),
    mc.AssignmentRule('K_glu', '(x_glu1-x_glu2) * K_val', 'pM'),
    mc.AssignmentRule('K_epi', '(x_epi1-x_epi2) * K_val', 'pM'),
    mc.AssignmentRule('gamma',
                      '0.5 dimensionless * (1 dimensionless - ins_norm/(ins_norm+K_ins) + max(glu_norm/(glu_norm+K_glu), epi_f*epi_norm/(epi_norm+K_epi)))',
                      'dimensionless',
                      name='phosphorylation state'),

    # balance equations
    mc.AssignmentRule('nadh_tot', 'nadh + nad', 'mM', name='NADH balance'),
    mc.AssignmentRule('atp_tot', 'atp + adp + amp', 'mM', 'ATP balance'),
    mc.AssignmentRule('utp_tot', 'utp + udp + udpglc', 'mM', name='UTP balance'),
    mc.AssignmentRule('gtp_tot', 'gtp + gdp', 'mM', name='GTP balance'),
    mc.AssignmentRule('nadh_mito_tot', 'nadh_mito + nad_mito', 'mM', name='NADH mito balance'),
    mc.AssignmentRule('atp_mito_tot', 'atp_mito + adp_mito', 'mM', name='ATP mito balance'),
    mc.AssignmentRule('gtp_mito_tot', 'gtp_mito + gdp_mito', 'mM', name='GTP mito balance'),

    # whole liver output
    mc.AssignmentRule('HGP', 'GLUT2 * conversion_factor', 'mumol_per_min_kg',
                      name='hepatic glucose production/utilization'),
    mc.AssignmentRule('GNG', 'GPI * conversion_factor', 'mumol_per_min_kg', name='gluconeogenesis/glycolysis'),
    mc.AssignmentRule('GLY', '-G16PI * conversion_factor', 'mumol_per_min_kg',
                      name='glycogenolysis/glycogen synthesis'),
])

##############################################################
# Reactions
##############################################################
