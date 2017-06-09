# -*- coding=utf-8 -*-
"""
Hepatic glucose model (Koenig 2012).

Definition of units is done by defining the main_units of the model in
addition with the definition of the individual units of the model.

"""
from __future__ import print_function, division, absolute_import

from sbmlutils import factory as mc

from libsbml import UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE
from libsbml import XMLNode
from sbmlutils.modelcreator import templates

from . import Reactions

##############################################################
creators = templates.creators
mid = 'Hepatic_glucose'
version = 3
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Koenig Human Glucose Metabolism</h1>
    <h2>Description</h2>
    <p>
        This is a metabolism model of Human glucose metabolism in <a href="http://sbml.org">SBML</a> format.
    </p>
    <p>This model is described in the article:</p>
    <div class="bibo:title">
        <a href="http://identifiers.org/pubmed/22761565" title="Access to this publication">Quantifying the
        contribution of the liver to glucose homeostasis: a detailed kinetic model of human hepatic glucose metabolism.
        </a>
    </div>
    <div class="bibo:authorList">König M., Bulik S., Holzhütter HG.</div>
    <div class="bibo:Journal">PLoS Comput Biol. 2012;8(6)</div>
    <p>Abstract:</p>
    <div class="bibo:abstract">
    <p>Despite the crucial role of the liver in glucose homeostasis, a detailed mathematical model of human
         hepatic glucose metabolism is lacking so far. Here we present a detailed kinetic model of glycolysis,
         gluconeogenesis and glycogen metabolism in human hepatocytes integrated with the hormonal control of
         these pathways by insulin, glucagon and epinephrine. Model simulations are in good agreement with experimental
         data on (i) the quantitative contributions of glycolysis, gluconeogenesis, and glycogen metabolism to hepatic
         glucose production and hepatic glucose utilization under varying physiological states. (ii) the time courses
         of postprandial glycogen storage as well as glycogen depletion in overnight fasting and short term fasting
         (iii) the switch from net hepatic glucose production under hypoglycemia to net hepatic glucose utilization
         under hyperglycemia essential for glucose homeostasis (iv) hormone perturbations of hepatic glucose
         metabolism. Response analysis reveals an extra high capacity of the liver to counteract changes of
         plasma glucose level below 5 mM (hypoglycemia) and above 7.5 mM (hyperglycemia). Our model may serve as
         an important module of a whole-body model of human glucose metabolism and as a valuable tool for
         understanding the role of the liver in glucose homeostasis under normal conditions and in diseases
         like diabetes or glycogen storage diseases.</p>
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
    mc.Compartment(sid='pm', spatialDimensions=2, unit='m2', constant=True, value='1.0 m2', name='plasma membrane'),
    mc.Compartment(sid='mm', spatialDimensions=2, unit='m2', constant=True, value='1.0 m2',
                   name='mitochondrial membrane'),
])

##############################################################
# Species
##############################################################
species.extend([
    mc.Species('atp', compartment='cyto', value=2.8000, unit='mM', boundaryCondition=True, name='ATP'),
    mc.Species('adp', compartment='cyto', value=0.8000, unit='mM', boundaryCondition=True, name='ADP'),
    mc.Species('amp', compartment='cyto', value=0.1600, unit='mM', boundaryCondition=True, name='AMP'),
    mc.Species('utp', compartment='cyto', value=0.2700, unit='mM', boundaryCondition=False, name='UTP'),
    mc.Species('udp', compartment='cyto', value=0.0900, unit='mM', boundaryCondition=False, name='UDP'),
    mc.Species('gtp', compartment='cyto', value=0.2900, unit='mM', boundaryCondition=False, name='GTP'),
    mc.Species('gdp', compartment='cyto', value=0.1000, unit='mM', boundaryCondition=False, name='GDP'),
    mc.Species('nad', compartment='cyto', value=1.2200, unit='mM', boundaryCondition=True, name='NAD+'),
    mc.Species('nadh', compartment='cyto', value=0.56E-3, unit='mM', boundaryCondition=True, name='NADH'),
    mc.Species('phos', compartment='cyto', value=5.0000, unit='mM', boundaryCondition=True, name='phosphate'),
    mc.Species('pp', compartment='cyto', value=0.0080, unit='mM', boundaryCondition=False, name='pyrophosphate'),
    mc.Species('co2', compartment='cyto', value=5.0000, unit='mM', boundaryCondition=True, name='CO2'),
    mc.Species('h2o', compartment='cyto', value=0.0, unit='mM', boundaryCondition=True, name='H2O'),
    mc.Species('h', compartment='cyto', value=0.0, unit='mM', boundaryCondition=True, name='H+'),

    mc.Species('glc1p', compartment='cyto', value=0.0120, unit='mM', boundaryCondition=False,
               name='glucose-1 phosphate'),
    mc.Species('udpglc', compartment='cyto', value=0.3800, unit='mM', boundaryCondition=False, name='UDP-glucose'),
    mc.Species('glyglc', compartment='cyto', value=250.0000, unit='mM', boundaryCondition=False, name='glycogen'),
    mc.Species('glc', compartment='cyto', value=5.0000, unit='mM', boundaryCondition=False, name='glucose'),
    mc.Species('glc6p', compartment='cyto', value=0.1200, unit='mM', boundaryCondition=False,
               name='glucose-6 phosphate'),
    mc.Species('fru6p', compartment='cyto', value=0.0500, unit='mM', boundaryCondition=False,
               name='fructose-6 phosphate'),
    mc.Species('fru16bp', compartment='cyto', value=0.0200, unit='mM', boundaryCondition=False,
               name='fructose-16 bisphosphate'),
    mc.Species('fru26bp', compartment='cyto', value=0.0040, unit='mM', boundaryCondition=False,
               name='fructose-26 bisphosphate'),
    mc.Species('grap', compartment='cyto', value=0.1000, unit='mM', boundaryCondition=False,
               name='glyceraldehyde 3-phosphate'),
    mc.Species('dhap', compartment='cyto', value=0.0300, unit='mM', boundaryCondition=False,
               name='dihydroxyacetone phosphate'),
    mc.Species('bpg13', compartment='cyto', value=0.3000, unit='mM', boundaryCondition=False,
               name='13-bisphospho-glycerate'),
    mc.Species('pg3', compartment='cyto', value=0.2700, unit='mM', boundaryCondition=False, name='3-phosphoglycerate'),
    mc.Species('pg2', compartment='cyto', value=0.0300, unit='mM', boundaryCondition=False, name='2-phosphoglycerate'),
    mc.Species('pep', compartment='cyto', value=0.1500, unit='mM', boundaryCondition=False, name='phosphoenolpyruvate'),
    mc.Species('pyr', compartment='cyto', value=0.1000, unit='mM', boundaryCondition=False, name='pyruvate'),
    mc.Species('oaa', compartment='cyto', value=0.0100, unit='mM', boundaryCondition=False, name='oxaloacetate'),
    mc.Species('lac', compartment='cyto', value=0.5000, unit='mM', boundaryCondition=False, name='lactate'),

    mc.Species('glc_ext', compartment='ext', value=3.0000, unit='mM', boundaryCondition=True, name='glucose'),
    mc.Species('lac_ext', compartment='ext', value=1.2000, unit='mM', boundaryCondition=True, name='lactate'),

    mc.Species('co2_mito', compartment='mito', value=5.0000, unit='mM', boundaryCondition=True, name='CO2'),
    mc.Species('phos_mito', compartment='mito', value=5.0000, unit='mM', boundaryCondition=True, name='phosphate'),
    mc.Species('oaa_mito', compartment='mito', value=0.0100, unit='mM', boundaryCondition=False, name=' oxaloacetate'),
    mc.Species('pep_mito', compartment='mito', value=0.1500, unit='mM', boundaryCondition=False,
               name='phosphoenolpyruvate'),
    mc.Species('acoa_mito', compartment='mito', value=0.0400, unit='mM', boundaryCondition=True,
               name='acetyl-coenzyme A'),
    mc.Species('pyr_mito', compartment='mito', value=0.1000, unit='mM', boundaryCondition=False, name='pyruvate'),
    mc.Species('cit_mito', compartment='mito', value=0.3200, unit='mM', boundaryCondition=True, name='citrate'),

    mc.Species('atp_mito', compartment='mito', value=2.8000, unit='mM', boundaryCondition=True, name='ATP'),
    mc.Species('adp_mito', compartment='mito', value=0.8000, unit='mM', boundaryCondition=True, name='ADP'),
    mc.Species('gtp_mito', compartment='mito', value=0.2900, unit='mM', boundaryCondition=False, name='GTP'),
    mc.Species('gdp_mito', compartment='mito', value=0.1000, unit='mM', boundaryCondition=False, name='GDP'),
    mc.Species('coa_mito', compartment='mito', value=0.0550, unit='mM', boundaryCondition=True, name='coenzyme A'),
    mc.Species('nadh_mito', compartment='mito', value=0.2400, unit='mM', boundaryCondition=True, name='NADH'),
    mc.Species('nad_mito', compartment='mito', value=0.9800, unit='mM', boundaryCondition=True, name='NAD+'),
    mc.Species('h2o_mito', compartment='mito', value=0.0, unit='mM', boundaryCondition=True, name='H20'),
    mc.Species('h_mito', compartment='mito', value=0.0, unit='mM', boundaryCondition=True, name='H+'),
])

##############################################################
# Parameters
##############################################################
parameters.extend([
    mc.Parameter('V_cyto', 1.0E-3, 'm3', True, name='cytosolic volume'),
    mc.Parameter('f_ext', 10.0, 'dimensionless', True, name='external volume factor'),
    mc.Parameter('f_mito', 0.2, 'dimensionless', True, name='mitochondrial volume factor'),
    mc.Parameter('Vliver', 1.5E-3, 'm3', True, name='liver volume'),
    mc.Parameter('fliver', 0.583333333333334, 'dimensionless', True, name='parenchymal fraction liver'),
    mc.Parameter('bodyweight', 70, 'kg', True, name='bodyweight'),
    mc.Parameter('sec_per_min', 60, 's_per_min', True, name='time conversion'),

    # hormonal regulation
    mc.Parameter('x_ins1', 818.9, 'pM', True),
    mc.Parameter('x_ins2', 0, 'pM', True),
    mc.Parameter('x_ins3', 8.6, 'mM', True),
    mc.Parameter('x_ins4', 4.2, 'dimensionless', True),

    mc.Parameter('x_glu1', 190, 'pM', True),
    mc.Parameter('x_glu2', 37.9, 'pM', True),
    mc.Parameter('x_glu3', 3.01, 'mM', True),
    mc.Parameter('x_glu4', 6.40, 'dimensionless', True),

    mc.Parameter('x_epi1', 6090, 'pM', True),
    mc.Parameter('x_epi2', 100, 'pM', True),
    mc.Parameter('x_epi3', 3.10, 'mM', True),
    mc.Parameter('x_epi4', 8.40, 'dimensionless', True),

    mc.Parameter('K_val', 0.1, 'dimensionless', True),
    mc.Parameter('epi_f', 0.8, 'dimensionless', True),
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
                      '0.5 dimensionless * (1 dimensionless -ins_norm/(ins_norm+K_ins) + '
                      'max(glu_norm/(glu_norm+K_glu), epi_f*epi_norm/(epi_norm+K_epi)))',
                      'dimensionless', name='phosphorylation state'),

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
reactions.extend([
    Reactions.GLUT2,
    Reactions.GK,
    Reactions.G6PASE,
    Reactions.GPI,
    Reactions.G16PI,
    Reactions.UPGASE,
    Reactions.PPASE,
    Reactions.GS,
    Reactions.GP,
    Reactions.NDKGTP,
    Reactions.NDKUTP,
    Reactions.AK,
    Reactions.PFK2,
    Reactions.FBP2,
    Reactions.PFK1,
    Reactions.FBP1,
    Reactions.ALD,
    Reactions.TPI,
    Reactions.GAPDH,
    Reactions.PGK,
    Reactions.PGM,
    Reactions.EN,
    Reactions.PK,
    Reactions.PEPCK,
    Reactions.PEPCKM,
    Reactions.PC,
    Reactions.LDH,
    Reactions.LACT,
    Reactions.PYRTM,
    Reactions.PEPTM,
    Reactions.PDH,
    Reactions.CS,
    Reactions.NDKGTPM,
    Reactions.OAAFLX,
    Reactions.ACOAFLX,
    Reactions.CITFLX,
])
