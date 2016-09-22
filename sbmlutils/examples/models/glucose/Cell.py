# -*- coding=utf-8 -*-
"""
Hepatic glucose model (Koenig 2012).

Definition of units is done by defining the main_units of the model in
addition with the definition of the individual units of the model.

"""
from libsbml import UNIT_KIND_KILOGRAM, UNIT_KIND_MOLE, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE
from libsbml import XMLNode
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator import modelcreator as mc

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
        <a href="http://identifiers.org/pubmed/22761565" title="Access to this publication">Quantifying the contribution of the liver to glucose homeostasis: a detailed kinetic model of human hepatic glucose metabolism.</a>
    </div>
    <div class="bibo:authorList">König M., Bulik S., Holzhütter HG.</div>
    <div class="bibo:Journal">PLoS Comput Biol. 2012;8(6)</div>
    <p>Abstract:</p>
    <div class="bibo:abstract">
    <p>Despite the crucial role of the liver in glucose homeostasis, a detailed mathematical model of human
         hepatic glucose metabolism is lacking so far. Here we present a detailed kinetic model of glycolysis,
         gluconeogenesis and glycogen metabolism in human hepatocytes integrated with the hormonal control of
         these pathways by insulin, glucagon and epinephrine. Model simulations are in good agreement with experimental
         data on (i) the quantitative contributions of glycolysis, gluconeogenesis, and glycogen metabolism to hepatic glucose
         production and hepatic glucose utilization under varying physiological states. (ii) the time courses of
         postprandial glycogen storage as well as glycogen depletion in overnight fasting and short term fasting
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
    mc.Compartment(sid='pm', spatialDimension=2, unit='m2', constant=True, value='1.0 m2', name='plasma membrane'),
    mc.Compartment(sid='mm', spatialDimension=2, unit='m2', constant=True, value='1.0 m2', name='mitochondrial membrane'),
])

##############################################################
# Species
##############################################################
species.update({
    # id : ('compartment', 'value', 'unit', 'boundaryCondition')
    'atp': ('cyto', 2.8000, 'mM', True),
    'adp': ('cyto', 0.8000, 'mM', True),
    'amp': ('cyto', 0.1600, 'mM', True),
    'utp': ('cyto', 0.2700, 'mM', False),
    'udp': ('cyto', 0.0900, 'mM', False),
    'gtp': ('cyto', 0.2900, 'mM', False),
    'gdp': ('cyto', 0.1000, 'mM', False),
    'nad': ('cyto', 1.2200, 'mM', True),
    'nadh': ('cyto', 0.56E-3, 'mM', True),
    'phos': ('cyto', 5.0000, 'mM', True),
    'pp': ('cyto', 0.0080, 'mM', False),
    'co2': ('cyto', 5.0000, 'mM', True),
    'h2o': ('cyto', 0.0, 'mM', True),
    'h': ('cyto', 0.0, 'mM', True),
    
    'glc1p': ('cyto', 0.0120, 'mM', False),
    'udpglc': ('cyto', 0.3800, 'mM', False),
    'glyglc': ('cyto', 250.0000, 'mM', False),
    'glc': ('cyto', 5.0000, 'mM', False),
    'glc6p': ('cyto', 0.1200, 'mM', False),
    'fru6p': ('cyto', 0.0500, 'mM', False),
    'fru16bp': ('cyto', 0.0200, 'mM', False),
    'fru26bp': ('cyto', 0.0040, 'mM', False),
    'grap': ('cyto', 0.1000, 'mM', False),
    'dhap': ('cyto', 0.0300, 'mM', False),
    'bpg13': ('cyto', 0.3000, 'mM', False),
    'pg3': ('cyto', 0.2700, 'mM', False),
    'pg2': ('cyto', 0.0300, 'mM', False),
    'pep': ('cyto', 0.1500, 'mM', False),
    'pyr': ('cyto', 0.1000, 'mM', False),
    'oaa': ('cyto', 0.0100, 'mM', False),
    'lac': ('cyto', 0.5000, 'mM', False),

    'glc_ext': ('ext', 3.0000, 'mM', True),
    'lac_ext': ('ext', 1.2000, 'mM', True),

    'co2_mito': ('mito', 5.0000, 'mM', True),
    'phos_mito': ('mito', 5.0000, 'mM', True),
    'oaa_mito': ('mito', 0.0100, 'mM', False),
    'pep_mito': ('mito', 0.1500, 'mM', False),
    'acoa_mito': ('mito', 0.0400, 'mM', True),
    'pyr_mito': ('mito', 0.1000, 'mM', False),
    'cit_mito': ('mito', 0.3200, 'mM', True),

    'atp_mito': ('mito', 2.8000, 'mM', True),
    'adp_mito': ('mito', 0.8000, 'mM', True),
    'gtp_mito': ('mito', 0.2900, 'mM', False),
    'gdp_mito': ('mito', 0.1000, 'mM', False),
    'coa_mito': ('mito', 0.0550, 'mM', True),
    'nadh_mito': ('mito', 0.2400, 'mM', True),
    'nad_mito': ('mito', 0.9800, 'mM', True),
    'h2o_mito': ('mito', 0.0, 'mM', True),
    'h_mito': ('mito', 0.0, 'mM', True),
})
names.update({
    'atp': 'ATP',
    'adp': 'ADP',
    'amp': 'AMP',
    'utp': 'UTP',
    'udp': 'UDP',
    'gtp': 'GTP',
    'gdp': 'GDP',
    'nad': 'NAD+',
    'nadh': 'NADH',
    'phos': 'phosphate',
    'pp': 'pyrophosphate',
    'co2': 'CO2',
    'h2o': 'H2O',
    'h': 'H+',

    'glc1p': 'glucose-1 phosphate',
    'udpglc': 'UDP-glucose',
    'glyglc': 'glycogen',
    'glc': 'glucose',
    'glc6p': 'glucose-6 phosphate',
    'fru6p': 'fructose-6 phosphate',
    'fru16bp': 'fructose-1,6 bisphosphate',
    'fru26bp': 'fructose-2,6 bisphosphate',
    'grap': 'glyceraldehyde 3-phosphate',
    'dhap': 'dihydroxyacetone phosphate',
    'bpg13': '1,3-bisphospho-glycerate',
    'pg3': '3-phosphoglycerate',
    'pg2': '2-phosphoglycerate',
    'pep': 'phosphoenolpyruvate',
    'pyr': 'pyruvate',
    'oaa': 'oxaloacetate',
    'lac': 'lactate',

    'glc_ext': 'glucose',
    'lac_ext': 'lactate',

    'co2_mito': 'CO2',
    'phos_mito': 'phosphate',
    'oaa_mito': ' oxaloacetate',
    'pep_mito': 'phosphoenolpyruvate',
    'acoa_mito': 'acetyl-coenzyme A',
    'pyr_mito': 'pyruvate',
    'cit_mito': 'citrate',

    'atp_mito': 'ATP',
    'adp_mito': 'ADP',
    'gtp_mito': 'GTP',
    'gdp_mito': 'GDP',
    'coa_mito': 'coenzyme A',
    'nadh_mito': 'NADH',
    'nad_mito': 'NAD+',
    'h2o_mito': 'H20',
    'h_mito': 'H+',
})

##############################################################
# Parameters
##############################################################
parameters.update({
    # id: ('value', 'unit', 'constant')
    'V_cyto': (1.0E-3, 'm3', True),
    'f_ext': (10.0, 'dimensionless', True),
    'f_mito': (0.2, 'dimensionless', True),
    'Vliver': (1.5E-3, 'm3', True),
    'fliver': (0.583333333333334, 'dimensionless', True),
    'bodyweight': (70, 'kg', True),
    'sec_per_min': (60, 's_per_min', True),

    # hormonal regulation
    'x_ins1': (818.9, 'pM', True),
    'x_ins2': (0, 'pM', True),
    'x_ins3': (8.6, 'mM', True),
    'x_ins4': (4.2, 'dimensionless', True),

    'x_glu1': (190, 'pM', True),
    'x_glu2': (37.9, 'pM', True),
    'x_glu3': (3.01, 'mM', True),
    'x_glu4': (6.40, 'dimensionless', True),

    'x_epi1': (6090, 'pM', True),
    'x_epi2': (100, 'pM', True),
    'x_epi3': (3.10, 'mM', True),
    'x_epi4': (8.40, 'dimensionless', True),

    'K_val': (0.1, 'dimensionless', True),
    'epi_f': (0.8, 'dimensionless', True),

})
names.update({
    'V_cyto': 'cytosolic volume',
    'f_ext': 'external volume factor',
    'f_mito': 'mitochondrial volume factor',
    'Vliver': 'liver volume',
    'fliver': 'parenchymal fraction liver',
    'bodyweight': 'bodyweight',
    'sec_per_min': 'conversion',
})

##############################################################
# Assignments
##############################################################
assignments.update({
    # id: ('value', 'unit')
    'V_ext': ('f_ext * V_cyto', 'm3'),
    'V_mito': ('f_mito * V_cyto', 'm3'),
    'conversion_factor': ('fliver*Vliver/V_cyto*sec_per_min * 1E3 dimensionless/bodyweight', 's_per_min_kg'),

    # scaling factors
    'scale': ('1 dimensionless /60 dimensionless', 'dimensionless'),
    'f_gly': ('scale', 'dimensionless'),
    'f_glyglc': ('scale', 'dimensionless'),
})
names.update({
    'V_mito': 'mitochondrial volume',
    'V_ext': 'external volume',
    'scale': 'scaling factor rates',
    'f_glc': 'scaling factor glycolysis',
    'f_glyglc': 'scaling factor glycogen metabolism',
})

##############################################################
# Rules
##############################################################
rules.update({
    # id: ('value', 'unit')

    # hormonal regulation
    'ins': ('x_ins2 + (x_ins1-x_ins2) * glc_ext^x_ins4/(glc_ext^x_ins4 + x_ins3^x_ins4)', 'pM'),
    'ins_norm': ('max(0.0 pM, ins-x_ins2)', 'pM'),
    'glu': ('x_glu2 + (x_glu1-x_glu2)*(1 dimensionless - glc_ext^x_glu4/(glc_ext^x_glu4 + x_glu3^x_glu4))', 'pM'),
    'glu_norm': ('max(0.0 pM, glu-x_glu2)', 'pM'),
    'epi': ('x_epi2 + (x_epi1-x_epi2) * (1 dimensionless - glc_ext^x_epi4/(glc_ext^x_epi4 + x_epi3^x_epi4))', 'pM'),
    'epi_norm': ('max(0.0 pM, epi-x_epi2)', 'pM'),
    'K_ins': ('(x_ins1-x_ins2) * K_val', 'pM'),
    'K_glu': ('(x_glu1-x_glu2) * K_val', 'pM'),
    'K_epi': ('(x_epi1-x_epi2) * K_val', 'pM'),
    'gamma': ('0.5 dimensionless * (1 dimensionless - ins_norm/(ins_norm+K_ins) + max(glu_norm/(glu_norm+K_glu), epi_f*epi_norm/(epi_norm+K_epi)))', 'dimensionless'),

    # balance rules
    'nadh_tot': ('nadh + nad', 'mM'),
    'atp_tot': ('atp + adp + amp', 'mM'),
    'utp_tot': ('utp + udp + udpglc', 'mM'),
    'gtp_tot': ('gtp + gdp', 'mM'),
    'nadh_mito_tot': ('nadh_mito + nad_mito', 'mM'),
    'atp_mito_tot': ('atp_mito + adp_mito', 'mM'),
    'gtp_mito_tot': ('gtp_mito + gdp_mito', 'mM'),

    # whole liver output
    'HGP': ('GLUT2 * conversion_factor', 'mumol_per_min_kg'),
    'GNG': ('GPI * conversion_factor', 'mumol_per_min_kg'),
    'GLY': ('-G16PI * conversion_factor', 'mumol_per_min_kg'),
})
names.update({
    'ins': 'insulin',
    'epi': 'epinephrine',
    'glu': 'glucagon',
    'gamma': 'phosphorylation state',

    'nadh_tot': 'NADH balance',
    'atp_tot': 'ATP balance',
    'utp_tot': 'UTP balance',
    'gtp_tot': 'GTP balance',
    'nadh_mito_tot': 'NADH mito balance',
    'atp_mito_tot': 'ATP mito balance',
    'gtp_mito_tot': 'GTP mito balance',

    'HGP': 'hepatic glucose production/utilization',
    'GNG': 'gluconeogenesis/glycolysis',
    'GLY': 'glycogenolysis/glycogen synthesis',
})


##############################################################
# Reactions
##############################################################
import Reactions
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
