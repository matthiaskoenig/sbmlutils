# -*- coding=utf-8 -*-
try:
    from libsbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE
except ImportError:
    from tesbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE

from sbmlutils.modelcreator import templates
import sbmlutils.factory as mc
import sbmlutils.comp as mcomp
from sbmlutils.factory import PORT_SUFFIX
from sbmlutils.modelcreator.processes import ReactionTemplate

PORT_SUFFIX = "_port"

########################################################################################################################
# Hepatic Metabolism
########################################################################################################################
mid = 'glucose_liver'
version = 3
########################################################################################################################
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Liver glucose model</h1>
    <h2>Description</h2>
    <p>
        Hepatic metabolism of glucose encoded in <a href="http://sbml.org">SBML</a> format.<br /> 
    </p>
    """ + templates.terms_of_use + """
    </body>
    """)

creators = templates.creators
main_units = {
    'time': 'h',
    'extent': 'mmole',
    'substance': 'mmole',
    'length': 'm',
    'area': 'm2',
    'volume': UNIT_KIND_LITRE,
}
ports = []

#########################################################################
# Units
##########################################################################
# units (kind, exponent, scale=0, multiplier=1.0)
units = [
    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)]),
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0, 0, 1)]),
    mc.Unit('kg', [(UNIT_KIND_GRAM, 1.0, 3, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('per_min', [(UNIT_KIND_SECOND, -1.0, 0, 60)]),
    mc.Unit('mg', [(UNIT_KIND_GRAM, 1.0, -3, 1.0)]),
    mc.Unit('ml', [(UNIT_KIND_LITRE, 1.0, -3, 1.0)]),
    mc.Unit('mmole', [(UNIT_KIND_MOLE, 1.0, -3, 1)]),


    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                                (UNIT_KIND_LITRE, -1.0, 0, 1)]),
    mc.Unit('mmole_per_h', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                                (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('g_per_mole', [(UNIT_KIND_GRAM, 1.0, 0, 1.0),
                           (UNIT_KIND_MOLE, -1.0, 0, 1)]),
    mc.Unit('mg_per_litre', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                             (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),

    mc.Unit('mg_per_g', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                         (UNIT_KIND_GRAM, -1.0, 0, 1.0)]),
    mc.Unit('mmole_per_hl', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                             (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
]

for unit in units:
    ports.append(
        mcomp.Port(sid="{}{}".format(unit.sid, PORT_SUFFIX), unitRef=unit.sid)
    )

##############################################################
# Functions
##############################################################
functions = []

##############################################################
# Compartments
##############################################################
compartments = [
    mc.Compartment('Vli', value=1.47, unit=UNIT_KIND_LITRE, constant=False, name='liver', port=True),
    mc.Compartment('Vext', value=1.0, unit=UNIT_KIND_LITRE, constant=False, name='liver blood', port=True),
]

##############################################################
# Species
##############################################################
species = [
    mc.Species('Aext_glc', compartment="Vext", initialConcentration=5.0, unit='mmole',
               name="glucose", hasOnlySubstanceUnits=True, port=True),
    mc.Species('Aext_lac', compartment="Vext", initialConcentration=0.8, unit='mmole',
               name="lactate", hasOnlySubstanceUnits=True, port=True),
    mc.Species('Ali_glc', compartment="Vli", initialConcentration=5.0, unit='mmole',
               name="glucose", hasOnlySubstanceUnits=True),
    mc.Species('Ali_lac', compartment="Vli", initialConcentration=0.8, unit='mmole',
               name="lactate", hasOnlySubstanceUnits=True),
]

##############################################################
# Parameters
##############################################################
parameters = []


##############################################################
# Assignments
##############################################################
assignments = []

##############################################################
# AssignmentRules
##############################################################
rules = []
# add concentrations
for s in species:

    rules.append(
        mc.AssignmentRule(f'C{s.sid[1:]}', f'{s.sid}/{s.compartment}',
                          'mM', name=f'{s.name} concentration ({s.compartment})'),
    )

##############################################################
# Reactions
##############################################################
reactions = [

    ReactionTemplate(
        rid="GLCIM",
        name="GLCIM (glc_ext <-> glc)",
        equation="Aext_glc <-> Ali_glc",
        compartment='Vli',
        pars=[
            mc.Parameter('GLCIM_Vmax', 1E3, 'mmole_per_hl',
                         name='Glucose utilization brain'),
            mc.Parameter('GLCIM_Km', 0.1, 'mM'),
        ],
        rules=[],

        formula=(
        "GLCIM_Vmax/GLCIM_Km * Vli * (Cext_glc-Cli_glc)/(1 dimensionless + Cext_glc/GLCIM_Km + Cli_glc/GLCIM_Km)",
        'mmole_per_h'),
    ),

    ReactionTemplate(
        rid="LACIM",
        name="LACIM (lac_ext <-> lac)",
        equation="Aext_lac <-> Ali_lac",
        compartment='Vli',
        pars=[
            mc.Parameter('LACIM_Vmax', 1E3, 'mmole_per_hl',
                         name='Glucose utilization brain'),
            mc.Parameter('LACIM_Km', 0.1, 'mM'),
        ],
        rules=[],

        formula=(
            "LACIM_Vmax/LACIM_Km * Vli * (Cext_lac-Cli_lac)/(1 dimensionless + Cext_lac/LACIM_Km + Cli_lac/LACIM_Km)",
            'mmole_per_h'),
    ),


    ReactionTemplate(
        rid="LAC2GLC",
        name="LAC2GLC (2 lac -> glu)",
        equation="2 Ali_lac -> Ali_glc",
        compartment='Vli',
        pars=[
            mc.Parameter('LAC2GLC_Vmax', 200, 'mmole_per_hl',
                         name='Gluconeogenesis [mmole_per_h]'),
            mc.Parameter('LAC2GLC_Km', 0.05, 'mM'),
        ],
        rules=[],

        formula=("LAC2GLC_Vmax * Vli * (5.0 mM - Cext_glc)/Cext_glc*(Cli_lac/(Cli_lac + LAC2GLC_Km))", 'mmole_per_h'),
    ),
]

##############################################################
# RateRules
##############################################################
rate_rules = []
