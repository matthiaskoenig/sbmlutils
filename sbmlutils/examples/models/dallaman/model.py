# -*- coding=utf-8 -*-
"""
DallaMan2006
"""
# TODO: encode units for model
# TODO: T2DM simulations (in current version not working)

from sbmlutils import factory as mc

from libsbml import UNIT_KIND_GRAM
from libsbml import UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE
from libsbml import XMLNode
from sbmlutils.modelcreator import templates

##############################################################
creators = templates.creators
mid = 'DallaMan2006'
version = 2
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>DallaMan2006 - Glucose Insulin System</h1>
    <h2>Description</h2>
    <p>
        This is a A simulation model of the glucose-insulin system in the postprandial state in
        <a href="http://sbml.org">SBML</a> format.
    </p>
    <p>This model is described in the article:</p>
    <div class="bibo:title">
        <a href="http://identifiers.org/pubmed/17926672" title="Access to this publication">Meal simulation model of
        the glucose-insulin system.</a>
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
    'time': 'min',
    'extent': UNIT_KIND_MOLE,  # change to mg
    'substance': UNIT_KIND_MOLE,  # change to mg
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}

#########################################################################
# Units
##########################################################################
units = [
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    mc.Unit('min', [(UNIT_KIND_SECOND, 1.0, 0, 60)]),
    mc.Unit('per_min', [(UNIT_KIND_SECOND, -1.0, 0, 60)]),

    mc.Unit('l_per_kg', [(UNIT_KIND_LITRE, 1.0),
                         (UNIT_KIND_KILOGRAM, -1.0)]),
    mc.Unit('dl_per_kg', [(UNIT_KIND_LITRE, 1.0, -1, 1.0),
                          (UNIT_KIND_KILOGRAM, -1.0)]),
    mc.Unit('mg_per_kg', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                          (UNIT_KIND_KILOGRAM, -1.0)]),
    mc.Unit('mg_per_dl', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                          (UNIT_KIND_LITRE, -1.0, -1, 1.0)]),
    mc.Unit('pmol_per_kg', [(UNIT_KIND_MOLE, 1.0, -9, 1.0),
                            (UNIT_KIND_KILOGRAM, -1.0)]),
    mc.Unit('pmol_per_l', [(UNIT_KIND_MOLE, 1.0, -9, 1.0),
                           (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('pmol_per_kgmin', [(UNIT_KIND_MOLE, 1.0, -9, 1.0),
                               (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_SECOND, -1.0, 0, 60)]),
    mc.Unit('minkg_per_pmol', [(UNIT_KIND_SECOND, 1.0, 0, 60), (UNIT_KIND_KILOGRAM, 1.0),
                               (UNIT_KIND_MOLE, -1.0, -9, 1.0)]),
    mc.Unit('mg_per_kgmin', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                             (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_SECOND, -1.0, 0, 60)]),
    mc.Unit('mgl_per_kgminpmol', [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_LITRE, 1.0),
                                  (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_SECOND, -1.0, 0, 60),
                                  (UNIT_KIND_MOLE, -1.0, -9, 1.0)]),
    mc.Unit('mg_per_minpmol', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                               (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_MOLE, -1.0, -9, 1.0)]),

    mc.Unit('pmolmg_per_kgdl', [(UNIT_KIND_MOLE, 1.0, -9, 1.0), (UNIT_KIND_GRAM, 1.0, -3, 1.0),
                                (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_LITRE, -1.0, -1, 1.0)]),
    mc.Unit('pmolmg_per_kgmindl', [(UNIT_KIND_MOLE, 1.0, -9, 1.0), (UNIT_KIND_GRAM, 1.0, -3, 1.0),
                                   (UNIT_KIND_KILOGRAM, -1.0), (UNIT_KIND_LITRE, -1.0, -1, 1.0),
                                   (UNIT_KIND_SECOND, -1.0, 0, 60)]),
]

##############################################################
# Functions
##############################################################
functions = []

##############################################################
# Compartments
##############################################################
compartments = []

##############################################################
# Species
##############################################################
species = []

##############################################################
# Parameters
##############################################################
parameters = [

    # state variables (initial values)
    mc.Parameter('Gp', 178, 'mg_per_kg', constant=False, name='glucose plasma'),
    mc.Parameter('Gt', 135, 'mg_per_kg', constant=False, name='glucose tissue'),
    mc.Parameter('Il', 4.5, 'pmol_per_kg', constant=False, name='insulin mass liver'),
    mc.Parameter('Ip', 1.25, 'pmol_per_kg', constant=False, name='insulin mass plasma'),
    mc.Parameter('Qsto1', 78000, '?', constant=False),
    mc.Parameter('Qsto2', 0, '?', constant=False),
    mc.Parameter('Qgut', 0, '?', constant=False),
    mc.Parameter('I1', 25, '?', constant=False),
    mc.Parameter('Id', 25, 'pmol_per_l', constant=False, name='delayed insulin'),
    mc.Parameter('INS', 0, '?', constant=False),
    mc.Parameter('Ipo', 3.6, 'pmol_per_kg', constant=False, name='insulin portal vein'),
    mc.Parameter('Y', 0, '?', constant=False),

    # bodyweight
    mc.Parameter('BW', 78, 'kg', constant=True, name='body weight'),
    mc.Parameter('D', 78000, '?', constant=True),

    # Glucose Kinetics
    mc.Parameter('V_G', 1.88, 'dl_per_kg', constant=True, name='V_G distribution volume glucose'),
    mc.Parameter('k_1', 0.065, 'per_min', constant=True, name='k_1 glucose kinetics'),
    mc.Parameter('k_2', 0.079, 'per_min', constant=True, name='k_2 glucose kinetics'),
    mc.Parameter('G_b', 95, '?', constant=True),

    # Insulin kinetics
    mc.Parameter('V_I', 0.05, 'l_per_kg', constant=True, name='V_I distribution volume insulin'),
    mc.Parameter('m_1', 0.190, 'per_min', constant=True),
    mc.Parameter('m_2', 0.484, 'per_min', constant=True),
    mc.Parameter('m_4', 0.194, 'per_min', constant=True),
    mc.Parameter('m_5', 0.0304, 'minkg_per_pmol', constant=True),
    mc.Parameter('m_6', 0.6471, '-', constant=True),
    mc.Parameter('HE_b', 0.60, '-', constant=True),
    mc.Parameter('I_b', 25, '?', constant=True),
    mc.Parameter('S_b', 1.8, '?', constant=True),

    # Rate of appearance
    mc.Parameter('k_max', 0.0558, 'per_min', constant=True),
    mc.Parameter('k_min', 0.0080, 'per_min', constant=True),
    mc.Parameter('k_abs', 0.057, 'per_min', constant=True),
    mc.Parameter('k_gri', 0.0558, 'per_min', constant=True),
    mc.Parameter('f', 0.90, '-', constant=True),
    # mc.Parameter('a', 0.00013, 'per_mg', constant=True),
    mc.Parameter('b', 0.82, '-', constant=True),
    # mc.Parameter('c', 0.00236, 'per_mg', constant=True),
    mc.Parameter('d', 0.010, '-', constant=True),

    # Endogenous production
    mc.Parameter('k_p1', 2.70, 'mg_per_kgmin', constant=True),
    mc.Parameter('k_p2', 0.0021, 'per_min', constant=True),
    mc.Parameter('k_p3', 0.009, 'mgl_per_kgminpmol', constant=True),
    mc.Parameter('k_p4', 0.0618, 'mg_per_minpmol', constant=True),
    mc.Parameter('k_i', 0.0079, 'per_min', constant=True),

    # Utilization
    mc.Parameter('U_ii', 1, 'mg_per_kgmin', constant=True, name="insulin independent glucose utilization"),  # F_cns
    mc.Parameter('V_m0', 2.50, 'mg_per_kgmin', constant=True),
    mc.Parameter('V_mX', 0.047, 'mgl_per_kgminpmol', constant=True),
    mc.Parameter('K_m0', 225.59, 'mg_per_kg', constant=True),
    mc.Parameter('V_f0', 2.5, 'mg_per_kgmin', constant=True),
    mc.Parameter('V_fX', 0.047, 'mgl_per_kgminpmol', constant=True),
    mc.Parameter('K_f0', 225.59, 'mg_per_kg', constant=True),
    mc.Parameter('p_2U', 0.0331, 'per_min', constant=True),
    mc.Parameter('part', 0.20, '?', constant=True),

    # Secretion
    mc.Parameter('K', 2.30, 'pmolmg_per_kgdl', constant=True),
    mc.Parameter('alpha', 0.050, 'per_min', constant=True),
    mc.Parameter('beta', 0.11, 'pmolmg_per_kgmindl', constant=True),
    mc.Parameter('gamma', 0.5, 'per_min', constant=True),

    # renal excretion
    mc.Parameter('k_e1', 0.0005, 'per_min', constant=True),
    mc.Parameter('k_e2', 339, 'mg_per_kg', constant=True),
]

##############################################################
# Assignments
##############################################################
assignments = []

##############################################################
# Rules
##############################################################
rate_rules = [
    # rate rules d/dt
    mc.RateRule('Gp', 'EGP +Ra -U_ii -E -k_1*Gp +k_2*Gt', 'mg_per_kgmin'),
    mc.RateRule('Gt', '-U_id + k_1*Gp -k_2*Gt', 'mg_per_kgmin'),

    mc.RateRule('Il', '-(m_1+m_3)*Il + m_2*Ip + S', 'pmol_per_kg'),
    mc.RateRule('Ip', '-(m_2+m_4)*Ip + m_1*Il', 'pmol_per_kg'),

    mc.RateRule('Qsto1', '-k_gri*Qsto1', '?'),
    mc.RateRule('Qsto2', '(-k_empt*Qsto2)+k_gri*Qsto1', '?'),
    mc.RateRule('Qgut', '(-k_abs*Qgut)+k_empt*Qsto2', '?'),
    mc.RateRule('I1', '-k_i*(I1-I)', '?'),
    mc.RateRule('Id', '-k_i*(Id-I1)', '?'),
    mc.RateRule('INS', '(-p_2U*INS)+p_2U*(I-I_b)', '?'),
    mc.RateRule('Ipo', '(-gamma*Ipo)+S_po', '?'),
    mc.RateRule('Y', '-alpha*(Y-beta*(G-G_b))', '?'),
]

rules = [
    mc.AssignmentRule('aa', '5/2/(1-b)/D', '?'),
    mc.AssignmentRule('cc', '5/2/d/D', '?'),
    mc.AssignmentRule('EGP', 'k_p1-k_p2*Gp-k_p3*Id-k_p4*Ipo', 'mg_per_kgmin', name='EGP endogenous glucose production'),
    mc.AssignmentRule('V_mmax', '(1-part)*(V_m0+V_mX*INS)', '?'),
    mc.AssignmentRule('V_fmax', 'part*(V_f0+V_fX*INS)', '?'),
    mc.AssignmentRule('E', '0', 'mg_per_kgmin', 'renal excretion'),
    mc.AssignmentRule('S', 'gamma*Ipo', 'pmol_per_kgmin', name='S insulin secretion'),
    mc.AssignmentRule('I', 'Ip/V_I', 'pmol_per_l', name='I plasma insulin'),
    mc.AssignmentRule('G', 'Gp/V_G', 'mg_per_dl', name='G plasma Glucose'),
    mc.AssignmentRule('HE', '-m_5*S + m_6', '-', name="HE hepatic extraction insulin"),
    mc.AssignmentRule('m_3', 'HE*m_1/(1-HE)', 'per_min'),
    mc.AssignmentRule('Q_sto', 'Qsto1+Qsto2', '?'),
    mc.AssignmentRule('Ra', '1.32 dimensionless*f*k_abs*Qgut/BW', 'mg_per_kgmin', name='Ra glucose rate of appearance'),
    # % Ra', f*k_abs*Qgut/BW
    mc.AssignmentRule('k_empt', 'k_min+(k_max-k_min)/2*(tanh(aa*(Q_sto-b*D))-tanh(cc*(Q_sto-d*D))+2)', '?'),
    mc.AssignmentRule('U_idm', 'V_mmax*Gt/(K_m0+Gt)', 'mg_per_kgmin'),
    mc.AssignmentRule('U_idf', 'V_fmax*Gt/(K_f0+Gt)', 'mg_per_kgmin'),
    mc.AssignmentRule('U_id', 'U_idm+U_idf', 'mg_per_kgmin', name='insulin dependent glucose utilization'),
    mc.AssignmentRule('U', 'U_ii+U_id', 'mg_per_kgmin', name='U glucose uptake'),
    mc.AssignmentRule('S_po', 'Y+K*(EGP+Ra-E-U_ii-k_1*Gp+k_2*Gt)/V_G+S_b', '?'),
]

##############################################################
# Reactions
##############################################################
