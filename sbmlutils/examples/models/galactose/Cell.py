# -*- coding=utf-8 -*-
"""
Galactose model for inclusion into sinusoidal unit.
The metabolic models are specified in a generic format which is than
included in the tissue scale model.

Generic generation of the species depending on the compartment they
are localized in.
e__x : extracellular compartment (Disse)
h__x : hepatocyte compartment (total internal cell volume)
c__x : cytosolic compartment (fraction of hepatocyte which is cytosol)


TODO: how to handle the versions and names of the multiple submodels ?
TODO: add the model description & history to the model

"""
from libsbml import XMLNode
from sbmlutils.modelcreator import templates

##############################################################
mid = 'galactose'
version = 30
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Koenig Human Galactose Metabolism</h1>
    <h2>Description</h2>
    <p>This is a metabolism model of Human galactose metabolism in
    <a href="http://sbmlutils.org" target="_blank" title="Access the definition of the SBML file format.">SBML</a>&#160;format.
    </p>
    """ + templates.terms_of_use + """
    </body>
    """)
creators = templates.creators
units = dict()
compartments = dict()
species = dict()
parameters = dict()
names = dict()
assignments = dict()
rules = dict()
reactions = []

##############################################################
# Compartments
##############################################################
compartments.update({
    # id : ('spatialDimension', 'unit', 'constant', 'assignment')
    'e': (3, 'm3', False, 'Vol_e'),
    'h': (3, 'm3', False, 'Vol_h'),
    'c': (3, 'm3', False, 'Vol_c'),
    'm': (2, 'm2', False, 'A_m'),
})
names.update({
    'e': 'external',
    'h': 'hepatocyte',
    'c': 'cytosol',
    'm': 'plasma membrane',
})

##############################################################
# Species
##############################################################
species.update({
    # id : ('compartment', 'value', 'unit', 'boundaryCondition')
    'e__gal':       ('e', 0.00012, 'mM', False),
    'e__galM':      ('e', 0.0, 'mM', False),
    'e__h2oM':      ('e', 0.0, 'mM', False),
    'h__h2oM':      ('h', 0.0, 'mM', False),
    'c__gal':       ('c', 0.00012, 'mM', False),
    'c__galM':      ('c', 0.0, 'mM', False),
    'c__glc1p':     ('c', 0.012, 'mM', False),
    'c__glc1pM':    ('c', 0.0, 'mM', False),
    'c__glc6p':     ('c', 0.12, 'mM', False),
    'c__glc6pM':    ('c', 0.0, 'mM', False),
    'c__gal1p':     ('c', 0.001, 'mM', False),
    'c__gal1pM':    ('c', 0.0, 'mM', False),
    'c__udpglc':    ('c', 0.34, 'mM', False),
    'c__udpglcM':   ('c', 0.0, 'mM', False),
    'c__udpgal':    ('c', 0.11, 'mM', False),
    'c__udpgalM':   ('c', 0.0, 'mM', False),
    'c__galtol':    ('c', 0.001, 'mM', False),
    'c__galtolM':   ('c', 0.0, 'mM', False),
    
    'c__atp':       ('c', 2.7, 'mM', False),
    'c__adp':       ('c', 1.2, 'mM', False),
    'c__utp':       ('c', 0.27, 'mM', False),
    'c__udp':       ('c', 0.09, 'mM', False),
    'c__phos':      ('c', 5.0, 'mM', False),
    'c__ppi':       ('c', 0.008, 'mM', False),
    'c__nadp':      ('c', 0.1, 'mM', False),
    'c__nadph':     ('c', 0.1, 'mM', False),

    'c__acpt':      ('c', 0.0, 'mM', True),
    'c__acptgal':   ('c', 0.0, 'mM', True),
    'c__acptglc':   ('c', 0.0, 'mM', True),
    'c__acptgalM':   ('c', 0.0, 'mM', True),
    'c__acptglcM':   ('c', 0.0, 'mM', True),

    'c__h2o':       ('c', 0.0, 'mM', True),
    'c__hydron':    ('c', 0.0, 'mM', True),
    'c__co2':       ('c', 0.0, 'mM', True),
    'c__o2':        ('c', 0.0, 'mM', True),
    'c__h2':        ('c', 0.0, 'mM', True),
})
names.update({
    'rbcM': 'red blood cells M*',
    'suc': 'sucrose',
    'alb': 'albumin',
    'h2oM': 'water M*',
    'glc': 'D-glucose',
    'gal': 'D-galactose',
    'galM': 'D-galactose M*',
    'glc1p': 'D-glucose 1-phophate',
    'glc1pM': 'D-glucose 1-phophate M*',
    'glc6p': 'D-glucose 6-phosphate',
    'glc6pM': 'D-glucose 6-phosphate M*',
    'gal1p': 'D-galactose 1-phosphate',
    'gal1pM': 'D-galactose 1-phosphate M*',
    'udpglc': 'UDP-D-glucose',
    'udpglcM': 'UDP-D-glucose M*',
    'udpgal': 'UDP-D-galactose',
    'udpgalM': 'UDP-D-galactose M*',
    'galtol': 'D-galactitol',
    'galtolM': 'D-galactitol M*',
    'atp': 'ATP',
    'adp': 'ADP',
    'utp': 'UTP',
    'udp': 'UDP',
    'phos': 'phosphate',
    'ppi': 'pyrophosphate',
    'nadp': 'NADP',
    'nadph': 'NADPH',

    'acpt': 'Acceptor (glc/gal)',
    'acptglc': 'Acceptor-glucose',
    'acptgal': 'Acceptor-galactose',
    'acptglcM': 'Acceptor-glucose M*',
    'acptgalM': 'Acceptor-galactose M*',

    'h2o': 'water',
    'hydron': 'H+',
    'co2': 'CO2',
    'o2': 'O2',
    'h2': 'H2'
})

##############################################################
# Parameters
##############################################################
parameters.update({
    # id: ('value', 'unit', 'constant')
    'scale_f':      (0.31, 'per_m3', True),
    'REF_P':        (1.0, 'mM', True),
    'deficiency':   (0, '-', True),
    'y_cell':       (9.40E-6, 'm', True),
    'x_cell':       (25E-6, 'm', True),
    'f_tissue':     (0.8, '-', True),
    'f_cyto':       (0.4, '-', True),
    'Nf':           (1, '-', True),
})
names.update({
    'scale_f': 'metabolic scaling factor',
    'REF_P': 'reference protein amount',
    'deficiency': 'type of galactosemia',
    'y_cell': 'width hepatocyte',
    'x_cell': 'length hepatocyte',
    'f_tissue': 'parenchymal fraction of liver',
    'f_cyto': 'cytosolic fraction of hepatocyte'
})

##############################################################
# Assignments
##############################################################
assignments.update({
    # id: ('value', 'unit')
    'Vol_h': ('x_cell*x_cell*y_cell', 'm3'),
    'Vol_e': ('Vol_h', 'm3'),
    'Vol_c': ('f_cyto*Vol_h', 'm3'),
    'A_m': ('x_cell*x_cell', 'm2'),
})
names.update({
    'Vol_h': 'volume hepatocyte',
    'Vol_c': 'volume cytosol',
    'Vol_e': 'volume external compartment',
    'A_m': 'area plasma membrane',
})

##############################################################
# Rules
##############################################################
rules.update({
    # id: ('value', 'unit')
    'c__scale': ('scale_f * Vol_h', '-'),
            
    'e__gal_tot': ('e__gal + e__galM', 'mM'),
    'c__gal_tot': ('c__gal + c__galM', 'mM'),
    'c__glc1p_tot': ('c__glc1p + c__glc1pM', 'mM'),
    'c__glc6p_tot': ('c__glc6p + c__glc6pM', 'mM'),
    'c__gal1p_tot': ('c__gal1p + c__gal1pM', 'mM'),
    'c__udpglc_tot': ('c__udpglc + c__udpglcM', 'mM'),
    'c__udpgal_tot': ('c__udpgal + c__udpgalM', 'mM'),
    'c__galtol_tot': ('c__galtol + c__galtolM', 'mM'),
            
    'c__nadp_bal': ('c__nadp + c__nadph', 'mM'),
    'c__adp_bal': ('c__atp + c__adp', 'mM'),
    'c__udp_bal': ('c__utp + c__udp + c__udpglc + c__udpgal + c__udpglcM + c__udpgalM', 'mM'),
    'c__phos_bal': ('3 dimensionless *c__atp + 2 dimensionless *c__adp + 3 dimensionless *c__utp + 2 dimensionless *c__udp' +
                    '+ c__phos + 2 dimensionless *c__ppi + c__glc1p + c__glc6p + c__gal1p + 2 dimensionless*c__udpglc + 2 dimensionless *c__udpgal' +
                    '+ c__glc1pM + c__glc6pM + c__gal1pM + 2 dimensionless*c__udpglcM + 2 dimensionless *c__udpgalM', 'mM'),
})
names.update({
    'nadp_bal': 'NADP balance',
    'adp_bal': 'ADP balance',
    'udp_bal': 'UDP balance',
    'phos_bal': 'Phosphate balance',
})


##############################################################
# Reactions
##############################################################
import Reactions
reactions.extend([
    Reactions.GALK,
    Reactions.GALKM,
    Reactions.IMP,
    Reactions.IMPM,
    Reactions.ATPS,
    Reactions.ALDR,
    Reactions.ALDRM,
    Reactions.NADPR,
    Reactions.GALT,
    Reactions.GALTM1,
    Reactions.GALTM2,
    Reactions.GALTM3,
    Reactions.GALE,
    Reactions.GALEM,
    Reactions.UGP,
    Reactions.UGPM,
    Reactions.UGALP,
    Reactions.UGALPM,
    Reactions.PPASE,
    Reactions.NDKU,
    Reactions.PGM1,
    Reactions.PGM1M,
    Reactions.GLY,
    Reactions.GLYM,
    Reactions.GTFGAL,
    Reactions.GTFGALM,
    Reactions.GTFGLC,
    Reactions.GTFGLCM,

    Reactions.H2OTM,
    Reactions.GLUT2_GAL,
    Reactions.GLUT2_GALM
])
