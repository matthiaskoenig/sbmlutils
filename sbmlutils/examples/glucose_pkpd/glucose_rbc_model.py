# -*- coding=utf-8 -*-
try:
    from libsbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE
except ImportError:
    from tesbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE

from sbmlutils.modelcreator import templates
import sbmlutils.factory as mc
import sbmlutils.comp as mcomp
from sbmlutils.modelcreator.processes import ReactionTemplate

PORT_SUFFIX = "_port"

########################################################################################################################
# RBC Metabolism
########################################################################################################################
mid = 'glucose_rbc'
version = 4
########################################################################################################################

notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Erythrocyte glucose model</h1>
    <h2>Description</h2>
    <p>
        Erythrocyte metabolism of glucose encoded in <a href="http://sbml.org">SBML</a> format.<br /> 
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
    mc.Unit('ml_per_l', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                         (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),

    mc.Unit('mmole_per_hml', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_LITRE, -1.0, -3, 1.0)]),
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
    mc.Compartment('Vpl', value=3.0, unit=UNIT_KIND_LITRE, constant=False, name='plasma', port=True),
    mc.Compartment('Vrbc', value=0.0, unit=UNIT_KIND_LITRE, constant=False, name='erythrocyte'),
]

##############################################################
# Species
##############################################################

# tissue metabolites
species = [
    mc.Species('glc_ext', compartment="Vpl", initialConcentration=0, unit='mmole',
               name="glucose", hasOnlySubstanceUnits=True, constant=False, port=True),
    mc.Species('lac_ext', compartment="Vpl", initialConcentration=0, unit='mmole',
               name="lactate", hasOnlySubstanceUnits=True, constant=False, port=True),

    mc.Species('glcRBC', compartment="Vrbc", initialConcentration=0, unit='mmole',
               name="glucose", hasOnlySubstanceUnits=True, constant=False),
    mc.Species('lacRBC', compartment="Vrbc", initialConcentration=0, unit='mmole',
               name="lactate", hasOnlySubstanceUnits=True, constant=False),
]


##############################################################
# Parameters
##############################################################
parameters = [
    mc.Parameter('alpha', 0.9, '-', constant=True, name='volume fraction erythrocytes'),
]

##############################################################
# Assignments
##############################################################
assignments = []

##############################################################
# AssignmentRules
##############################################################
rules = [
    # volumes
    mc.AssignmentRule('Vrbc', 'Vpl * alpha', UNIT_KIND_LITRE),
]

##############################################################
# Reactions
##############################################################
reactions = [

    ReactionTemplate(
        rid="GLCIM",
        name="GLCIM (glc_ext -> glcRBC)",
        equation="glc_ext -> glcRBC",
        compartment='Vrbc',
        pars=[
            mc.Parameter('GLCIM_Vmax', 100, 'mmole_per_h', name='Glucose import Vmax'),
            mc.Parameter('GLCIM_Km', 0.1, 'mM', name='Glucose import Km'),
        ],
        rules=[],

        formula=("GLCIM_Vmax/GLCIM_Km * (glc_ext/Vpl-glcRBC/Vrbc)/(1 dimensionless + (glc_ext/Vpl)/GLCIM_Km + (glcRBC/Vrbc)/GLCIM_Km)",
                 'mmole_per_h'),
    ),

    ReactionTemplate(
        rid="LACEX",
        name="LACEX (lacRBC -> Apl_lac)",
        equation="lacRBC -> lac_ext",
        compartment='Vrbc',
        pars=[
            mc.Parameter('LACEX_Vmax', 100, 'mmole_per_h', name='Lactate export Vmax'),
            mc.Parameter('LACEX_Km', 0.1, 'mM', name='Lactate export Km'),
        ],
        rules=[],

        formula=("LACEX_Vmax/LACEX_Km * (lacRBC/Vrbc-lac_ext/Vpl)/(1 dimensionless + (lac_ext/Vpl)/LACEX_Km + (lacRBC/Vrbc)/LACEX_Km)",
                 'mmole_per_h'),
    ),

    ReactionTemplate(
        rid="GLC2LAC",
        name="GLC2LAC (glcRBC -> 2 lacRBC)",
        equation="glcRBC -> 2 lacRBC",
        compartment='Vrbc',
        pars=[
            mc.Parameter('GLC2LAC_Vmax', 5, 'mmole_per_h',
                         name='Glucose utilization rbc'),
            mc.Parameter('GLC2LAC_Km', 0.1, 'mM'),
        ],
        rules=[],

        formula=("GLC2LAC_Vmax * (glcRBC/Vrbc)/(glcRBC/Vrbc + GLC2LAC_Km)", 'mmole_per_h'),
    ),
]

##############################################################
# RateRules
##############################################################
rate_rules = []
