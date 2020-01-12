# -*- coding=utf-8 -*-
try:
    from libsbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE
except ImportError:
    from tesbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE

from sbmlutils.modelcreator import templates
import sbmlutils.factory as mc
from sbmlutils.factory import PORT_SUFFIX
import sbmlutils.comp as mcomp

from sbmlutils.modelcreator.processes import ReactionTemplate

########################################################################################################################
# Brain Metabolism
########################################################################################################################
mid = 'glucose_brain'
version = 5
########################################################################################################################

notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Brain glucose model</h1>
    <h2>Description</h2>
    <p>
        Brain glucose metabolism  
        encoded in <a href="http://sbml.org">SBML</a> format.<br /> 
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
    mc.Unit('mmole_per_hl', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                                (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
]
# add unit ports
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
    mc.Compartment('Vbr', value=1.4, unit=UNIT_KIND_LITRE, constant=False, name='brain tissue', port=True),
    mc.Compartment('Vext', value=1.0, unit=UNIT_KIND_LITRE, constant=False, name='brain blood', port=True),
]

##############################################################
# Species
##############################################################
species = [
    mc.Species('Aext_glc', compartment="Vext", initialConcentration=5.0, unit='mmole',
               name="glucose", hasOnlySubstanceUnits=True, port=True),
    mc.Species('Aext_lac', compartment="Vext", initialConcentration=0.8, unit='mmole',
               name="lactate", hasOnlySubstanceUnits=True, port=True),
    mc.Species('Abr_glc', compartment="Vbr", initialConcentration=5.0, unit='mmole',
               name="glucose", hasOnlySubstanceUnits=True),
    mc.Species('Abr_lac', compartment="Vbr", initialConcentration=0.8, unit='mmole',
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
        equation="Aext_glc <-> Abr_glc",
        compartment='Vbr',
        pars=[
            mc.Parameter('GLCIM_Vmax', 1E3, 'mmole_per_hl',
                         name='Glucose utilization brain'),
            mc.Parameter('GLCIM_Km', 0.1, 'mM'),
        ],
        rules=[],

        formula=("GLCIM_Vmax/GLCIM_Km * Vbr * (Cext_glc-Cbr_glc)/(1 dimensionless + Cext_glc/GLCIM_Km + Cbr_glc/GLCIM_Km)", 'mmole_per_h'),
    ),

    ReactionTemplate(
        rid="LACIM",
        name="LACIM (lac_ext <-> lac)",
        equation="Aext_lac <-> Abr_lac",
        compartment='Vbr',
        pars=[
            mc.Parameter('LACIM_Vmax', 1E3, 'mmole_per_hl',
                         name='Glucose utilization brain'),
            mc.Parameter('LACIM_Km', 0.1, 'mM'),
        ],
        rules=[],

        formula=(
        "LACIM_Vmax/LACIM_Km * Vbr * (Cext_lac-Cbr_lac)/(1 dimensionless + Cext_lac/LACIM_Km + Cbr_lac/LACIM_Km)", 'mmole_per_h'),
    ),

    ReactionTemplate(
        rid="GLC2LAC",
        name="GLC2LAC (glc -> 2 lac)",
        equation="Abr_glc -> 2 Abr_lac",
        compartment='Vbr',
        pars=[
            mc.Parameter('GLC2LAC_Vmax', 2000, 'mmole_per_hl',
                         name='Glucose utilization brain'),
            mc.Parameter('GLC2LAC_Km', 0.01, 'mM'),
        ],
        rules=[],

        formula=("GLC2LAC_Vmax * Vbr * (Cbr_glc/(Cbr_glc + GLC2LAC_Km))", 'mmole_per_h'),
    ),
]

##############################################################
# RateRules
##############################################################
rate_rules = []
