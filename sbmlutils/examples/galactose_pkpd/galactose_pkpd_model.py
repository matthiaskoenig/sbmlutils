# -*- coding=utf-8 -*-
"""
PKPD model for methacetin-based liver function tests.
"""
try:
    from libsbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE
except ImportError:
    from tesbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE

from sbmlutils.modelcreator import templates
import sbmlutils.factory as mc
from sbmlutils.modelcreator.processes import ReactionTemplate

########################################################################################################################

mid = 'galactose'
version = "v32"
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>PBPK model for galactose based dynamical liver function tests (GEC).</h1>
    <h2>Description</h2>
    <p>
        This model is a physiological-base pharmacokinetic model (PBPK) for the
        absorption, distribution, metabolism and elimination of galactose 
        encoded in <a href="http://sbml.org">SBML</a> format.<br /> 
        The model is applied to the analysis of galactose based liver function tests.
    </p>
    """ + templates.terms_of_use + """
    </body>
    """)
creators = templates.creators

########################################################################################################################

COMPARTMENTS = {
    "ve": "venous blood",
    "gu": "gut",
    "ki": "kidney",
    "li": "liver",
    "lu": "lung",
    "sp": "spleen",
    "re": "rest",
    'ar': "arterial blood",
}

SUBSTANCES = {
    # --------------
    # Galactose
    # --------------
    "gal": {
        "name": "galactose",
        # partition coefficients [-]
        "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0, "Kpbo": 1.0, "Kpre": 1.0,
        # Molecular weight
        "Mr": 180.16,  # [g/mole] CHEBI:4139
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 2.5, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,  # < 5% of dose {Krumbiegel1985a}
    },
}

########################################################################################################################
# Hepatic Metabolism
########################################################################################################################
SPECIES = []
REACTIONS = [

    # TODO: add the full galactose metabolism (better to use a comp approach here !)
    # ReactionTemplate(
    #     rid="CYP1A2MET",
    #     name="CYP1A2_MET (CYP1A2) [metc13 -> apap + co2c13]",
    #     equation="Ali_metc13 -> Ali_apap + 1.0 Ali_co2c13",
    #     compartment='Vli',
    #     pars=[
    #         mc.Parameter('CYP1A2MET_CL', 1.5, 'mulitre_per_min_mg',
    #                      name='HLM apparent clearance by hepatic microsomes [mul/min/mg]'),
    #         mc.Parameter('CYP1A2MET_Km_met', 0.02, 'mM'),
    #     ],
    #     rules=[
    #         mc.AssignmentRule('CYP1A2MET_CLliv',
    #                           '(CYP1A2MET_CL/fumic_metc13) * MPPGL * Vli * F_PAR * 60 min_per_h / 1000 mulitre_per_g',
    #                           'litre_per_h', name='liver clearance [l/hr]'),
    #     ],
    #     formula=("CYP1A2MET_CLliv*1.0 mmole_per_litre * (Cli_free_metc13/(Cli_free_metc13 + CYP1A2MET_Km_met))", 'mmole_per_h'),
    # ),
]

#########################################################################
# Units
##########################################################################
main_units = {
    'time': 'h',
    'extent': 'mmole',
    'substance': 'mmole',
    'length': 'm',
    'area': 'm2',
    'volume': UNIT_KIND_LITRE,
}

# units (kind, exponent, scale=0, multiplier=1.0)
units = [
    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)]),
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0, 0, 1)]),
    mc.Unit('kg', [(UNIT_KIND_GRAM, 1.0, 3, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('per_min', [(UNIT_KIND_SECOND, -1.0, 0, 60)]),
    mc.Unit('cm', [(UNIT_KIND_METRE, 1.0, -2, 1.0)]),
    mc.Unit('mg', [(UNIT_KIND_GRAM, 1.0, -3, 1.0)]),
    mc.Unit('mmole', [(UNIT_KIND_MOLE, 1.0, -3, 1)]),
    mc.Unit('ml', [(UNIT_KIND_LITRE, 1.0, -3, 1.0)]),

    mc.Unit('mg_per_litre', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
    mc.Unit('mg_per_g', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                     (UNIT_KIND_GRAM, -1.0, 0, 1.0)]),
    mc.Unit('mg_per_h', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                 (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmole_per_h', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                         (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmole_per_litre', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
    mc.Unit('litre_per_h', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                     (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('litre_per_kg', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                     (UNIT_KIND_GRAM, -1.0, 3, 1.0)]),
    mc.Unit('mulitre_per_min_mg', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                           (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_GRAM, -1.0, -3, 1.0)]),

    mc.Unit('g_per_mole', [(UNIT_KIND_GRAM, 1.0, 0, 1.0),
                           (UNIT_KIND_MOLE, -1.0, 0, 1.0)]),
    mc.Unit('m2_per_kg', [(UNIT_KIND_METRE, 2.0, 0, 1.0),
                           (UNIT_KIND_GRAM, -1.0, 3, 1.0)]),

    mc.Unit('mug_per_hkg', [(UNIT_KIND_GRAM, 1.0, -6, 1.0),
                           (UNIT_KIND_MOLE, -1.0, 0, 3600), (UNIT_KIND_GRAM, -1.0, 3, 1.0)]),


    mc.Unit('mg_per_min', [(UNIT_KIND_GRAM, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 60)]),
    mc.Unit('mmole_per_min', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 60)]),
    mc.Unit('mmole_per_minkg', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_GRAM, -1.0, 3, 1)]),
    mc.Unit('mmole_per_hm2', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_METRE, -2.0, 0, 1)]),

    mc.Unit('ml_per_s', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                         (UNIT_KIND_SECOND, -1.0, 0, 1)]),
    mc.Unit('ml_per_skg', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                           (UNIT_KIND_SECOND, -1.0, 0, 1), (UNIT_KIND_GRAM, -1.0, 3, 1)]),

    mc.Unit('min_per_h', [(UNIT_KIND_SECOND, 1.0, 0, 60),
                  (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('s_per_min', [(UNIT_KIND_SECOND, 1.0, 0, 60),
                          (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('s_per_h', [(UNIT_KIND_SECOND, 1.0, 0, 1.0),
                        (UNIT_KIND_SECOND, -1.0, 0, 3600)]),

    mc.Unit('mulitre_per_g', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                      (UNIT_KIND_GRAM, -1.0, 0, 1)]),

    mc.Unit('ml_per_litre', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                     (UNIT_KIND_LITRE, -1.0, 0, 1)]),
]

##############################################################
# Functions
##############################################################
functions = [
    # mc.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='min'),
    # mc.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='max'),
]

##############################################################
# Compartments
##############################################################
compartments = [
    mc.Compartment('Vre', value=1, unit=UNIT_KIND_LITRE, constant=False, name='rest of body'),
    mc.Compartment('Vgu', value=1, unit=UNIT_KIND_LITRE, constant=False, name='gut'),
    mc.Compartment('Vki', value=1, unit=UNIT_KIND_LITRE, constant=False, name='kidney'),
    mc.Compartment('Vli', value=1, unit=UNIT_KIND_LITRE, constant=False, name='liver'),
    mc.Compartment('Vlu', value=1, unit=UNIT_KIND_LITRE, constant=False, name='lung'),
    mc.Compartment('Vsp', value=1, unit=UNIT_KIND_LITRE, constant=False, name='spleen'),

    mc.Compartment('Vve', value=1, unit=UNIT_KIND_LITRE, constant=False, name='venous blood'),
    mc.Compartment('Var', value=1, unit=UNIT_KIND_LITRE, constant=False, name='arterial blood'),
    mc.Compartment('Vpl', value=1, unit=UNIT_KIND_LITRE, constant=False, name='plasma'),
    mc.Compartment('Vplas_ven', value=1, unit=UNIT_KIND_LITRE, constant=False, name='venous plasma'),
    mc.Compartment('Vplas_art', value=1, unit=UNIT_KIND_LITRE, constant=False, name='arterial plasma'),

    mc.Compartment('Vurine', value=1, unit=UNIT_KIND_LITRE, constant=True, name='urine'),
]

##############################################################
# Species
##############################################################
species = SPECIES
for s_id, s_dict in SUBSTANCES.items():
    for c_id, c_name in COMPARTMENTS.items():
        species.append(
            mc.Species('A{}_{}'.format(c_id, s_id), 0,
                       compartment="V{}".format(c_id),
                       unit='mmole',
                       name="{} ({})".format(s_dict['name'], c_name),
                       hasOnlySubstanceUnits=True)
        )
    species.append(
        mc.Species('Aurine_{}'.format(s_id), 0,
               compartment="Vurine",
               unit='mmole',
               name="{} (urine)".format(s_dict['name']),
               hasOnlySubstanceUnits=True),
    )

##############################################################
# Parameters
##############################################################
parameters = [
    # whole body data
    mc.Parameter('BW', 75, 'kg', constant=True, name='body weight [kg]'),
    mc.Parameter('HEIGHT', 170, 'cm', constant=True, name='height [cm]'),
    mc.Parameter('HR', 70, 'per_min', constant=True, name='heart rate [1/min]'),
    mc.Parameter('HRrest', 70, 'per_min', constant=True, name='heart rate [1/min]'),

    mc.Parameter('BSA', 0, 'm2', constant=False, name='body surface area [m^2]'),
    mc.Parameter('COBW', 1.548, 'ml_per_skg', constant=True, name='cardiac output per bodyweight [ml/s/kg]'),
    mc.Parameter('CO', 108.33, 'ml_per_s', constant=False, name='cardiac output [ml/s]'),
    mc.Parameter('QC', 108.33*1000*60*60, 'litre_per_h', constant=False, name='cardiac output [L/hr]'),
    mc.Parameter('COHRI', 150, 'ml', constant=True, name="increase of cardiac output per heartbeat [ml/min*min]"),

    # fractional tissue volumes
    mc.Parameter('FVre', 0, 'litre_per_kg', constant=False, name='rest of body fractional tissue volume'),
    mc.Parameter('FVgu', 0.0171, 'litre_per_kg', constant=True, name='gut fractional tissue volume'),
    mc.Parameter('FVki', 0.0044, 'litre_per_kg', constant=True, name='kidney fractional tissue volume'),
    mc.Parameter('FVli', 0.0210, 'litre_per_kg', constant=True, name='liver fractional tissue volume'),
    mc.Parameter('FVlu', 0.0076, 'litre_per_kg', constant=True, name='lung fractional tissue volume'),
    mc.Parameter('FVsp', 0.0026, 'litre_per_kg', constant=True, name='spleen fractional tissue volume'),
    mc.Parameter('FVve', 0.0514, 'litre_per_kg', constant=True, name='venous fractional tissue volume'),
    mc.Parameter('FVar', 0.0257, 'litre_per_kg', constant=True, name='arterial fractional tissue volume'),
    mc.Parameter('FVpl', 0.0424, 'litre_per_kg', constant=True, name='plasma fractional tissue volume'),

    # fractional tissue blood flows
    mc.Parameter('FQre', 0, '-', constant=False, name='rest of body fractional tissue blood flow'),
    mc.Parameter('FQgu', 0.146, '-', constant=True, name='gut fractional tissue blood flow'),
    mc.Parameter('FQki', 0.190, '-', constant=True, name='kidney fractional tissue blood flow'),
    mc.Parameter('FQh',  0.215, '-', constant=True, name='hepatic (venous side) fractional tissue blood flow'),
    mc.Parameter('FQlu', 1, '-', constant=True, name='lung fractional tissue blood flow'),
    mc.Parameter('FQsp', 0.017, '-', constant=True, name='spleen fractional tissue blood flow'),

    # liver data
    mc.Parameter('F_PAR', 0.85, '-', constant=True, name='parenchymal liver fraction'),
    mc.Parameter('MPPGL', 45, 'mg_per_g', constant=True, name='mg microsomal protein per g liver parenchym'),
]

# species specific parameters
for s_id, s_dict in SUBSTANCES.items():

    parameters.extend([
        # molecular weights
        mc.Parameter('Mr_{}'.format(s_id), s_dict["Mr"], 'g_per_mole', constant=True,
                     name='Molecular weight {} [g/mole]'.format(s_id)),

        # dosing
        mc.Parameter('IVDOSE_{}'.format(s_id), s_dict["IVDOSE"], 'mg', constant=True,
                     name='IV bolus dose {} [mg]'.format(s_id)),
        mc.Parameter('PODOSE_{}'.format(s_id), s_dict["PODOSE"], 'mg', constant=True,
                     name='oral bolus dose {} [mg]'.format(s_id)),

        # absorption
        mc.Parameter('Ka_{}'.format(s_id), s_dict["Ka"], 'per_h', constant=True,
                     name='Ka [1/hr] absorption {}'.format(s_id)),
        mc.Parameter('F_{}'.format(s_id), s_dict["F"], '-', constant=True,
                     name='fraction absorbed {}'.format(s_id)),

        # injection kinetics (IV)
        # bolus parameters
        mc.Parameter('ti_{}'.format(s_id), 10, 's', constant=True,
                     name='injection time {} [s]'.format(s_id)),
        mc.Parameter('Ki_{}'.format(s_id), 1, 'per_h', constant=False,
                     name='Ki [1/hr] injection {}'.format(s_id)),
        # continuous infusion
        mc.Parameter('Ri_{}'.format(s_id), 0, 'mg_per_min', constant=True,
                     name='Ri [mg/min] rate of injection {}'.format(s_id)),
        mc.Parameter('cum_dose_{}'.format(s_id), 0, 'mg', constant=False,
                     name='Cumulative dose due to infusion {}'.format(s_id)),

        # in vitro binding data
        mc.Parameter('fup_{}'.format(s_id), s_dict["fup"], '-', constant=True,
                     name='fraction unbound in plasma {}'.format(s_id)),
        mc.Parameter('BP_{}'.format(s_id), s_dict["BP"], '-', constant=True,
                     name='blood to plasma ratio {}'.format(s_id)),
        mc.Parameter('fumic_{}'.format(s_id), s_dict["fumic"], '-', constant=True,
                     name='fraction unbound in microsomes {}'.format(s_id)),

        # renal clearance
        mc.Parameter('CLrenal_{}'.format(s_id), s_dict["CLrenal"], 'litre_per_h',
                     constant=True, name='renal clearance {} [L/hr]'.format(s_id)),
    ])

    for c_id, c_name in COMPARTMENTS.items():

        # tissue to plasma partition coefficients
        if c_id not in ['ve', 'ar']:
            parameters.append(
                mc.Parameter('Kp{}_{}'.format(c_id, s_id),
                             value=s_dict['Kp{}'.format(c_id)],
                             unit='-',
                             constant=True,
                             name='{} plasma partition coefficient'.format(c_name))
            )


##############################################################
# Assignments
##############################################################
assignments = []

##############################################################
# AssignmentRules
##############################################################
rules = [
    # Rest body volume
    mc.AssignmentRule('FVre', '1.0 litre_per_kg - (FVgu + FVki + FVli + FVlu + FVsp + FVve + FVar + FVpl)', 'litre_per_kg'),
    # Rest body perfusion
    mc.AssignmentRule('FQre', '1.0 dimensionless - (FQgu + FQki + FQh + FQsp)', 'dimensionless'),

    # Body surface area (Haycock1978)
    mc.AssignmentRule('BSA', '0.024265 m2 * power(BW/1 kg, 0.5378) * power(HEIGHT/1 cm, 0.3964)', 'm2'),

    # cardiac output (depending on heart rate and bodyweight)
    mc.AssignmentRule('CO', 'BW*COBW + (HR-HRrest)*COHRI / 60 s_per_min', 'ml_per_s'),
    # cardiac output (depending on bodyweight)
    mc.AssignmentRule('QC', 'CO/1000 ml_per_litre * 3600 s_per_h', 'litre_per_h'),

    # volumes
    mc.AssignmentRule('Vgu', 'BW*FVgu', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vki', 'BW*FVki', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vli', 'BW*FVli', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vlu', 'BW*FVlu', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vsp', 'BW*FVsp', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vve', 'BW*FVve', UNIT_KIND_LITRE),
    mc.AssignmentRule('Var', 'BW*FVar', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vpl', 'BW*FVpl', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vre', 'BW*FVre', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vplas_ven', 'Vpl*Vve/(Vve + Var)', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vplas_art', 'Vpl*Var/(Vve + Var)', UNIT_KIND_LITRE),

    # blood flows
    mc.AssignmentRule('Qgu', 'QC*FQgu', 'litre_per_h', name='gut blood flow'),
    mc.AssignmentRule('Qki', 'QC*FQki', 'litre_per_h', name='kidney blood flow'),
    mc.AssignmentRule('Qh', 'QC*FQh', 'litre_per_h', name='hepatic (venous side) blood flow'),
    mc.AssignmentRule('Qha', 'Qh - Qgu - Qsp', 'litre_per_h', name='hepatic artery blood flow'),
    mc.AssignmentRule('Qlu', 'QC*FQlu', 'litre_per_h', name='lung blood flow'),
    mc.AssignmentRule('Qsp', 'QC*FQsp', 'litre_per_h', name='spleen blood flow'),
    mc.AssignmentRule('Qre', 'QC*FQre', 'litre_per_h', name='rest of body blood flow'),
]

for s_id, s_dict in SUBSTANCES.items():
    s_name = s_dict['name']

    # total substance
    rules.append(
        mc.AssignmentRule('Xbody_{}'.format(s_id),
                      'Xar_{0} + Xgu_{0} + Xki_{0} + Xli_{0} + Xlu_{0} + Xsp_{0} + Xre_{0} + Xve_{0}'.format(s_id),
                      'mg')
    )

    # free concentrations & clearance
    rules.extend([
        mc.AssignmentRule('Cpl_ve_{}'.format(s_id),
                          'Cve_{}/BP_{}'.format(s_id, s_id), 'mM',
                          name='{} venous plasma concentration'.format(s_name)),
        mc.AssignmentRule('Cli_free_{}'.format(s_id),
                          'Cli_{}*fup_{}'.format(s_id, s_id), 'mM',
                          name='{} free liver concentration'.format(s_name)),
        mc.AssignmentRule('Cki_free_{}'.format(s_id),
                          'Cki_{}*fup_{}'.format(s_id, s_id), 'mM',
                          name='{} free kidney concentration'.format(s_name)),
    ])

    # injection
    rules.extend([
        mc.AssignmentRule('Ki_{}'.format(s_id),
                          '1.386 dimensionless/ti_{} * 3600 s_per_h'.format(s_id, s_id, s_id), 'mg_per_h'),  # 2*ln2
    ])

    # concentration rules
    for c_id, c_name in COMPARTMENTS.items():
        rules.extend([
            mc.AssignmentRule('C{}_{}'.format(c_id, s_id),
                              'A{}_{}/V{}'.format(c_id, s_id, c_id),
                              'mM', name='{} concentration ({})'.format(s_name, c_name)),

            mc.AssignmentRule('X{}_{}'.format(c_id, s_id),
                              'A{}_{}*Mr_{}'.format(c_id, s_id, s_id),
                              'mg', name='{} amount ({})'.format(s_name, c_name)),

            mc.AssignmentRule('M{}_{}'.format(c_id, s_id),
                              'A{}_{}/V{}*Mr_{}'.format(c_id, s_id, c_id, s_id),
                              'mg_per_litre', name='{} amount ({})'.format(s_name, c_name))
        ])

    c_id, c_name = ("urine", "urine")
    rules.append(
        mc.AssignmentRule('X{}_{}'.format(c_id, s_id),
                          'A{}_{}*Mr_{}'.format(c_id, s_id, s_id),
                          'mg', name='{} amount ({})'.format(s_name, c_name)),
    )

##############################################################
# Reactions
##############################################################
reactions = REACTIONS

for s_id, s_dict in SUBSTANCES.items():
    s_name = s_dict['name']
    reactions.extend([
        # Injection venous (I.V. dose)
        ReactionTemplate(rid="Injection_{}".format(s_id),
                         name="injection {}".format(s_name),
                         formula=("Ki_{}*IVDOSE_{}/Mr_{}".format(s_id, s_id, s_id, s_id), 'mmole_per_h'),
                         equation="-> Ave_{}".format(s_id),
                         compartment='Vve'),
        ReactionTemplate(rid="Infusion_{}".format(s_id),
                         name="infusion {}".format(s_name),
                         formula=("Ri_{}/Mr_{}*60 min_per_h".format(s_id, s_id), 'mmole_per_h'),
                         equation="-> Ave_{}".format(s_id),
                         compartment='Vve'),

        # Absorption gut (oral dose)
        ReactionTemplate(rid="Absorption_{}".format(s_id),
                         name="absorption {}".format(s_name),
                         formula=("Ka_{}*PODOSE_{}/Mr_{}*F_{}".format(s_id, s_id, s_id, s_id), 'mmole_per_h'),
                         equation="-> Agu_{}".format(s_id),
                         compartment='Vgu'),

        # Clearance kidney
        ReactionTemplate(rid="RenalClearance_{}".format(s_id),
                         name="clearance {} (kidney)".format(s_name),
                         formula=("CLrenal_{}*Cki_free_{}".format(s_id, s_id), 'mmole_per_h'),
                         equation='Aki_{} -> Aurine_{}'.format(s_id, s_id), compartment='Vki'),

        # lung
        ReactionTemplate(rid="Flow_ve_lu_{}".format(s_id),
                         name="inflow lung {}".format(s_name),
                         formula=("Qlu*Cve_{}".format(s_id), 'mmole_per_h'),
                         equation='Ave_{} -> Alu_{}'.format(s_id, s_id)),
        ReactionTemplate(rid="Flow_lu_ar_{}".format(s_id),
                         name="outflow lung {}".format(s_name),
                         formula=("Qlu*(Clu_{}/Kplu_{}*BP_{})".format(s_id, s_id, s_id), 'mmole_per_h'),
                         equation='Alu_{} -> Aar_{}'.format(s_id, s_id)),

        # rest
        ReactionTemplate(rid="Flow_ar_re_{}".format(s_id),
                         name="inflow rest {}".format(s_name),
                         formula=("Qre*Car_{}".format(s_id), 'mmole_per_h'),
                         equation='Aar_{} -> Are_{}'.format(s_id, s_id)),
        ReactionTemplate(rid="Flow_re_ve_{}".format(s_id),
                         name="outflow lung {}".format(s_name),
                         formula=("Qre*(Cre_{}/Kpre_{}*BP_{})".format(s_id, s_id, s_id), 'mmole_per_h'),
                         equation='Are_{} -> Ave_{}'.format(s_id, s_id)),

        # gut
        ReactionTemplate(rid="Flow_ar_gu_{}".format(s_id),
                         name="inflow gut {}".format(s_name),
                         formula=("Qgu*Car_{}".format(s_id), 'mmole_per_h'),
                         equation='Aar_{} -> Agu_{}'.format(s_id, s_id)),
        ReactionTemplate(rid="Flow_gu_li_{}".format(s_id),
                         name="outflow gut {}".format(s_name),
                         formula=("Qgu*(Cgu_{}/Kpgu_{}*BP_{})".format(s_id, s_id, s_id), 'mmole_per_h'),
                         equation='Agu_{} -> Ali_{}'.format(s_id, s_id)),

        # kidney
        ReactionTemplate(rid="Flow_ar_ki_{}".format(s_id),
                         name="inflow kidney {}".format(s_name),
                         formula=("Qki*Car_{}".format(s_id), 'mmole_per_h'),
                         equation='Aar_{} -> Aki_{}'.format(s_id, s_id)),
        ReactionTemplate(rid="Flow_ki_ve_{}".format(s_id),
                         name="outflow kidney {}".format(s_name),
                         formula=("Qki*(Cki_{}/Kpki_{}*BP_{})".format(s_id, s_id, s_id), 'mmole_per_h'),
                         equation='Aki_{} -> Ave_{}'.format(s_id, s_id)),

        # spleen
        ReactionTemplate(rid="Flow_ar_sp_{}".format(s_id),
                         name="inflow spleen {}".format(s_name),
                         formula=("Qsp*Car_{}".format(s_id), 'mmole_per_h'),
                         equation='Aar_{} -> Asp_{}'.format(s_id, s_id)),
        ReactionTemplate(rid="Flow_sp_li_{}".format(s_id),
                         name="outflow spleen {}".format(s_name),
                         formula=("Qsp*(Csp_{}/Kpsp_{}*BP_{})".format(s_id, s_id, s_id), 'mmole_per_h'),
                         equation='Asp_{} -> Ali_{}'.format(s_id, s_id)),

        # liver
        ReactionTemplate(rid="Flow_ar_li_{}".format(s_id),
                         name="inflow liver {}".format(s_name),
                         formula=("Qha*Car_{}".format(s_id), 'mmole_per_h'),
                         equation='Aar_{} -> Ali_{}'.format(s_id, s_id)),
        ReactionTemplate(rid="Flow_li_ve_{}".format(s_id),
                         name="outflow liver {}".format(s_name),
                         formula=("Qh*(Cli_{}/Kpli_{}*BP_{})".format(s_id, s_id, s_id), 'mmole_per_h'),
                         equation='Ali_{} -> Ave_{}'.format(s_id, s_id)),

    ])

##############################################################
# RateRules
##############################################################
rate_rules = []

for s_id, s_dict in SUBSTANCES.items():
    rate_rules.extend([
        # absorption of dose
        mc.RateRule('PODOSE_{}'.format(s_id), '-Absorption_{}*Mr_{}'.format(s_id, s_id), 'mg_per_h'),
        # injection of dose
        mc.RateRule('IVDOSE_{}'.format(s_id), '-Injection_{}*Mr_{}'.format(s_id, s_id), 'mg_per_h'),
    ])
