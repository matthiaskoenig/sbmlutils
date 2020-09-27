# coding=utf-8 -*-
"""
PKPD model for whole-body glucose homeostasis..
"""
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

mid = 'glucose_pkpd'
version = "v10"
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>PBPK model for whole-body glucose homeostasis.</h1>
    <h2>Description</h2>
    <p>
        This model is a physiological-base pharmacokinetic model (PBPK) for the
        absorption, distribution, metabolism and elimination of glucose 
        encoded in <a href="http://sbml.org">SBML</a> format.<br />
        The model contains the main organs relevant for whole-body glucose homeostasis, i.e.,
        pancreas, liver, muscle, brain. Insulin and glucagon regulation of glucose
        homeostasis are included.</br> 
    </p>    
    """ + templates.terms_of_use + """
    </body>
    """)
creators = templates.creators

ports = []
deletions = []
replacedElements = []
replacedBy = []

#########################################################################
# Submodels
##########################################################################
from .glucose_liver_model import mid as mid_liver
from .glucose_liver_model import version as version_liver
from .glucose_brain_model import mid as mid_brain
from .glucose_brain_model import version as version_brain
from .glucose_rbc_model import mid as mid_rbc
from .glucose_rbc_model import version as version_rbc

rbc_simple = True
liver_simple = True

externalModelDefinitions = [
    mcomp.ExternalModelDefinition(sid="glucose_brain", source=f"{mid_brain}_{version_brain}.xml",
                                  modelRef="{mid_brain}_{mid_brain}"),
]
if liver_simple:
    externalModelDefinitions.append(
        mcomp.ExternalModelDefinition(sid="glucose_liver", source=f"{mid_liver}_{version_liver}.xml",
                                      modelRef=f"{mid_liver}_{version_liver}"),
    )
else:
    mcomp.ExternalModelDefinition(sid="glucose_liver", source=f"Hepatic_glucose_5.xml",
                                  modelRef=f"Hepatic_glucose_5"),

# tissue to submodel mapping
SUBMODEL_SID_DICT = {
    "li": "LI",     # liver model
    "br": "BR",     # brain model
    "ve": "RBCVE",  # venous RBC
    "ar": "RBCAR",  # venous RBC
}

submodels = [
    mcomp.Submodel(sid=SUBMODEL_SID_DICT['li'], modelRef="glucose_liver"),
    mcomp.Submodel(sid=SUBMODEL_SID_DICT['br'], modelRef="glucose_brain"),

]
if rbc_simple:
    externalModelDefinitions.append(
        mcomp.ExternalModelDefinition(sid="glucose_rbc", source="{}_{}.xml".format(mid_rbc, version_rbc),
                                      modelRef="{}_{}".format(mid_rbc, version_rbc)),
    )
else:
    externalModelDefinitions.append(
        mcomp.ExternalModelDefinition(sid="glucose_rbc", source="rbc_parasite_model.xml",
                                  modelRef="rbc_parasite_model"),
    )

submodels.extend([
    mcomp.Submodel(sid=SUBMODEL_SID_DICT['ve'], modelRef="glucose_rbc"),
    mcomp.Submodel(sid=SUBMODEL_SID_DICT['ar'], modelRef="glucose_rbc"),
])


########################################################################################################################

COMPARTMENTS_BODY = {
    "ad": "adipose",
    "br": "brain",
    "gu": "gut",
    "he": "heart",
    "ki": "kidney",
    "li": "liver",
    "lu": "lung",
    "mu": "muscle",
    "pa": "pancreas",
    "sp": "spleen",
    "re": "rest",

    # "pl": "plasma",
    'ar': "arterial blood",
    "ve": "venous blood",
    # "rbc": "erythrocythes",
}

# substances which are transported via the circulation
SUBSTANCES_BODY = {
    # --------------
    # Glucose
    # --------------
    "glc": {
        "name": "glucose",
        "unit": "mmole",
        # initial concentration
        "cinit": 5.0,  # [mmole/l] (5.0 [mM], overnight fast, Gerich1993)
        # partition coefficients [-]
        "Kpad": 1.0, "Kpbr": 1.0, "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0, "Kpmu": 1.0, "Kppa": 1.0, "Kpre": 1.0,
        # Molecular weight
        "Mr": 180.16,  # [g/mole]
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 1.0, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,
    },
    # -------------------
    # Lactate
    # -------------------
    "lac": {
        "name": "lactate",
        "unit": "mmole",
        # initial concentration
        "cinit": 0.8,  # [mmole/l] (0.8 [mM], overnight fast, Gerich1993)
        # partition coefficients [-]
        "Kpad": 1.0, "Kpbr": 1.0, "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0, "Kpmu": 1.0, "Kppa": 1.0, "Kpre": 1.0,
        # molecular weight
        "Mr": 89.07,  # [g/mole]
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 0.2, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,
    },

    # -------------------
    # Alanine
    # -------------------
    "ala": {
        "name": "ala",
        "unit": "mmole",
        # initial concentration
        "cinit": 0.3,  # [mmole/l]  (0.3 [mM], overnight fast, Gerich1993)
        # partition coefficients [-]
        "Kpad": 1.0, "Kpbr": 1.0, "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0,
        "Kpmu": 1.0, "Kppa": 1.0, "Kpre": 1.0,
        # molecular weight
        "Mr": 89.09,  # [g/mole] CHEBI:16449
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 0.2, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,
    },

    # -------------------
    # FFA
    # -------------------
    "ffa": {
        "name": "FFA",
        "unit": "mmole",
        # initial concentration
        "cinit": 0.5,  # [mmole/l]  (0.5 [mM], overnight fast, Gerich1993)
        # partition coefficients [-]
        "Kpad": 1.0, "Kpbr": 1.0, "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0,
        "Kpmu": 1.0, "Kppa": 1.0, "Kpre": 1.0,
        # molecular weight
        "Mr": 256.43,  # [g/mole] (palmitate)
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 0.2, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,
    },

    # --------------
    # Insulin
    # --------------
    "ins": {
        "name": "insulin",
        "unit": "mmole",
        # initial concentration
        "cinit": 60E-6,  # [mmole/l] (60 [pmole/l], overnight fast, Gerich1993)
        # partition coefficients [-]
        "Kpad": 1.0, "Kpbr": 1.0, "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0, "Kpmu": 1.0, "Kppa": 1.0, "Kpre": 1.0,
        # Molecular weight
        "Mr": 5793.54,  # [g/mole] CHEBI:5931
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 0.2, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,
    },

    # --------------
    # Glucagon
    # --------------
    "glu": {
        "name": "glucagon",
        "unit": "mmole",
        # initial concentration
        "cinit": 40E-6,  # [pmole/l] (100 [ng/l] ~ 30 [pmole/l], overnight fast, Gerich1993)
        # partition coefficients [-]
        "Kpad": 1.0, "Kpbr": 1.0, "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0, "Kpmu": 1.0, "Kppa": 1.0, "Kpre": 1.0,
        # Molecular weight
        "Mr": 3482.75,  # [g/mole] CHEBI:5391
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 0.2, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,
    },

    # --------------
    # Epinephrine
    # --------------
    "epi": {
        "name": "epinephrine",
        "unit": "mmole",
        # initial concentration
        "cinit": 0.2E-3,  # [mmole/l] (0.2 [nmole/l], overnight fast, Gerich1993)
        # partition coefficients [-]
        "Kpad": 1.0, "Kpbr": 1.0, "Kphe": 1.0, "Kpgu": 1.0, "Kpki": 1.0, "Kpli": 1.0, "Kplu": 1.0, "Kpsp": 1.0,
        "Kpmu": 1.0, "Kppa": 1.0, "Kpre": 1.0,
        # Molecular weight
        "Mr": 183.20,  # [g/mole] CHEBI:33568
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 0.2, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'fup': 1.0, 'BP': 1.0, 'fumic': 1.0,
        # renal clearance [L/hr]
        'CLrenal': 0.0,
    },

}

########################################################################################################################
# Hepatic Metabolism
########################################################################################################################
SPECIES = []
REACTIONS = [

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
    mc.Unit('mmole_per_hml', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_LITRE, -1.0, -3, 1.0)]),

    mc.Unit('ml_per_l', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                         (UNIT_KIND_LITRE, -1.0, 0, 1.0)]),
    mc.Unit('litre_per_ml', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                             (UNIT_KIND_LITRE, -1.0, 0, 0.001)]),
]

for unit in units:
    ports.append(
        mcomp.Port(sid=f"{unit.sid}{PORT_SUFFIX}", unitRef=unit.sid)
    )

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

    mc.Compartment('Vad', value=1, unit=UNIT_KIND_LITRE, constant=False, name='adipose'),
    mc.Compartment('Vbr', value=1, unit=UNIT_KIND_LITRE, constant=False, name='brain'),
    mc.Compartment('Vhe', value=1, unit=UNIT_KIND_LITRE, constant=False, name='heart'),
    mc.Compartment('Vgu', value=1, unit=UNIT_KIND_LITRE, constant=False, name='gut'),
    mc.Compartment('Vki', value=1, unit=UNIT_KIND_LITRE, constant=False, name='kidney'),
    mc.Compartment('Vli', value=1, unit=UNIT_KIND_LITRE, constant=False, name='liver'),
    mc.Compartment('Vlu', value=1, unit=UNIT_KIND_LITRE, constant=False, name='lung'),
    mc.Compartment('Vsp', value=1, unit=UNIT_KIND_LITRE, constant=False, name='spleen'),
    mc.Compartment('Vmu', value=1, unit=UNIT_KIND_LITRE, constant=False, name='muscle'),
    mc.Compartment('Vpa', value=1, unit=UNIT_KIND_LITRE, constant=False, name='pancreas'),

    mc.Compartment('Vve', value=1, unit=UNIT_KIND_LITRE, constant=False, name='venous blood'),
    mc.Compartment('Var', value=1, unit=UNIT_KIND_LITRE, constant=False, name='arterial blood'),

    mc.Compartment('Vpl', value=1, unit=UNIT_KIND_LITRE, constant=False, name='plasma'),
    # mc.Compartment('Vrbc', value=1, unit=UNIT_KIND_LITRE, constant=False, name='erythrocyte'),
    mc.Compartment('Vplas_ven', value=1, unit=UNIT_KIND_LITRE, constant=False, name='venous plasma'),
    mc.Compartment('Vplas_art', value=1, unit=UNIT_KIND_LITRE, constant=False, name='arterial plasma'),

    mc.Compartment('Vurine', value=1, unit=UNIT_KIND_LITRE, constant=True, name='urine'),
]

# --------------------------------------------
# Volumes for explicit tissue models
# --------------------------------------------
# create the blood and tissue compartments for organ with tissue models
for c_id in SUBMODEL_SID_DICT.keys():
    compartments.extend([
        mc.Compartment(f'V{c_id}_tissue', value=1, unit=UNIT_KIND_LITRE, constant=False, name=f'{c_id} tissue',
                       metaId=f'meta_V{c_id}_tissue', port=True),
        mc.Compartment(f'V{c_id}_blood', value=1, unit=UNIT_KIND_LITRE, constant=False, name=f'{c_id} blood',
                       metaId=f'meta_V{c_id}_blood', port=True),
    ])

# --------------------------------------------
# Replace Compartments
# --------------------------------------------
replacedElements.extend([
    # brain
    mcomp.ReplacedElement(sid="Vbr_tissue_RE", metaId="Vbr_tissue_RE", elementRef="Vbr_tissue",
                          submodelRef=SUBMODEL_SID_DICT['br'], portRef=f"Vbr{PORT_SUFFIX}"),
    mcomp.ReplacedElement(sid="Vbr_blood_RE", metaId="Vbr_blood_RE", elementRef="Vbr_blood",
                          submodelRef=SUBMODEL_SID_DICT['br'], portRef=f"Vext{PORT_SUFFIX}"),
])
# liver
if liver_simple:
    replacedElements.extend([
        mcomp.ReplacedElement(sid="Vli_tissue_RE", metaId="Vli_tissue_RE", elementRef="Vli_tissue",
                              submodelRef=SUBMODEL_SID_DICT['li'], portRef=f"Vli{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Vli_blood_RE", metaId="Vli_blood_RE", elementRef="Vli_blood",
                              submodelRef=SUBMODEL_SID_DICT['li'], portRef=f"Vext{PORT_SUFFIX}")
    ])
else:
    replacedElements.extend([
        mcomp.ReplacedElement(sid="Vli_blood_RE", metaId="Vli_blood_RE", elementRef="Vli_blood",
                              submodelRef=SUBMODEL_SID_DICT['li'], portRef=f"ext{PORT_SUFFIX}")
    ])

# rbc model
if rbc_simple:
    replacedElements.extend([
        mcomp.ReplacedElement(sid="Vve_RE", elementRef="Vve",
                              submodelRef=SUBMODEL_SID_DICT['ve'], portRef=f"Vpl{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Var_RE", elementRef="Var",
                              submodelRef=SUBMODEL_SID_DICT['ar'], portRef=f"Vpl{PORT_SUFFIX}"),
    ])
else:
    # FIXME: check conversion factors! (RBC volumes in [ml])
    replacedElements.extend([
        mcomp.ReplacedElement(sid="Vve_RE", metaId="Vve_RE", elementRef="Vve",
                              submodelRef=SUBMODEL_SID_DICT['ve'], portRef=f"Vplasma{PORT_SUFFIX}",
                              conversionFactor="conversion_ml_to_l"),
        mcomp.ReplacedElement(sid="Var_RE", metaId="Var_RE", elementRef="Var",
                              submodelRef=SUBMODEL_SID_DICT['ar'], portRef=f"Vplasma{PORT_SUFFIX}",
                              conversionFactor="conversion_ml_to_l"),
    ])


##############################################################
# Species
##############################################################
# species in whole-body model
species = SPECIES
for s_id, s_dict in SUBSTANCES_BODY.items():
    for c_id, c_name in COMPARTMENTS_BODY.items():

        if c_id in SUBMODEL_SID_DICT.keys():
            if c_id in ['ve', 'ar']:
                sid_ex = f'A{c_id}_{s_id}'
                cid_ex = f'V{c_id}'
            else:
                # blood compartment of explicit tissue model
                sid_ex = f'A{c_id}_blood_{s_id}'
                cid_ex = f'V{c_id}_blood'

            species.append(
                mc.Species(sid_ex,
                           initialConcentration=s_dict['cinit'],
                           compartment=cid_ex,
                           unit=s_dict['unit'],
                           name=f"{s_dict['name']} ({c_name})",
                           hasOnlySubstanceUnits=True, port=True)
            )
        else:
            # only tissue compartment
            sid_ex = f'A{c_id}_{s_id}'
            cid_ex = f'V{c_id}'

            species.append(
                mc.Species(sid_ex,
                           initialConcentration=s_dict['cinit'],
                           compartment=cid_ex,
                           unit=s_dict['unit'],
                           name=f"{s_dict['name']} ({c_name})",
                           hasOnlySubstanceUnits=True)
            )

    species.append(
        mc.Species(f'Aurine_{s_id}',
                   initialConcentration=0,
                   compartment="Vurine",
                   unit='mmole',
                   name=f"{s_dict['name']} (urine)",
                   hasOnlySubstanceUnits=True),
    )

# --------------------------------------------
# Replace Species
# --------------------------------------------
replacedElements.extend([
    # brain
    mcomp.ReplacedElement(sid="Abr_blood_glc_RE", metaId="Abr_blood_glc_RE", elementRef="Abr_blood_glc",
                          submodelRef=SUBMODEL_SID_DICT['br'], portRef=f"Aext_glc{PORT_SUFFIX}"),
    mcomp.ReplacedElement(sid="Abr_blood_lac_RE", metaId="Abr_blood_lac_RE", elementRef="Abr_blood_lac",
                          submodelRef=SUBMODEL_SID_DICT['br'], portRef=f"Aext_lac{PORT_SUFFIX}"),
])

# liver
if liver_simple:
    replacedElements.extend([
        mcomp.ReplacedElement(sid="Ali_blood_glc_RE", metaId="Abr_blood_lac_RE", elementRef="Ali_blood_glc",
                              submodelRef=SUBMODEL_SID_DICT['li'], portRef=f"Aext_glc{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Ali_blood_lac_RE", metaId="Ali_blood_lac_RE", elementRef="Ali_blood_lac",
                              submodelRef=SUBMODEL_SID_DICT['li'], portRef=f"Aext_lac{PORT_SUFFIX}"),
    ])
else:
    pass

# rbc
if rbc_simple:
    replacedElements.extend([
        mcomp.ReplacedElement(sid="Ave_glc_RE", elementRef="Ave_glc",
                             submodelRef=SUBMODEL_SID_DICT['ve'], portRef=f"glc_ext{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Ave_lac_RE", elementRef="Ave_lac",
                              submodelRef=SUBMODEL_SID_DICT['ve'], portRef=f"lac_ext{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Aar_glc_RE", elementRef="Aar_glc",
                              submodelRef=SUBMODEL_SID_DICT['ar'], portRef=f"glc_ext{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Aar_lac_RE", elementRef="Aar_lac",
                              submodelRef=SUBMODEL_SID_DICT['ar'], portRef=f"lac_ext{PORT_SUFFIX}"),
    ])
else:
    # FIXME: check conversion factor (RBC in amounts [mmole])
    replacedElements.extend([
        mcomp.ReplacedElement(sid="Ave_glc_RE", metaId="Ave_glc_RE", elementRef="Ave_glc",
                              submodelRef=SUBMODEL_SID_DICT['ve'], portRef=f"glcEXT{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Ave_lac_RE", metaId="Ave_lac_RE", elementRef="Ave_lac",
                              submodelRef=SUBMODEL_SID_DICT['ve'], portRef=f"lacEXT{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Aar_glc_RE", metaId="Aar_glc_RE", elementRef="Aar_glc",
                              submodelRef=SUBMODEL_SID_DICT['ar'], portRef=f"glcEXT{PORT_SUFFIX}"),
        mcomp.ReplacedElement(sid="Aar_lac_RE", metaId="Aar_lac_RE", elementRef="Aar_lac",
                              submodelRef=SUBMODEL_SID_DICT['ar'], portRef=f"lacEXT{PORT_SUFFIX}"),
    ])


##############################################################
# Parameters
##############################################################
rules = []
parameters = [
    # conversion factors
    mc.Parameter('conversion_ml_to_l', 1000, 'ml_per_litre', constant=True, name='body weight [kg]'),


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
    mc.Parameter('Ftissue', 0.85, '-', constant=False, name='tissue fraction of organ volume'),

    # fractional tissue volumes
    mc.Parameter('FVre', 0, 'litre_per_kg', constant=False, name='rest of body fractional tissue volume'),

    mc.Parameter('FVad', 0.213, 'litre_per_kg', constant=True, name='adipose fractional tissue volume'),
    mc.Parameter('FVbr', 0.02, 'litre_per_kg', constant=True, name='brain fractional tissue volume'),
    mc.Parameter('FVhe', 0.0047, 'litre_per_kg', constant=True, name='heart fractional tissue volume'),
    mc.Parameter('FVgu', 0.0171, 'litre_per_kg', constant=True, name='gut fractional tissue volume'),
    mc.Parameter('FVki', 0.0044, 'litre_per_kg', constant=True, name='kidney fractional tissue volume'),
    mc.Parameter('FVli', 0.0210, 'litre_per_kg', constant=True, name='liver fractional tissue volume'),
    mc.Parameter('FVlu', 0.0076, 'litre_per_kg', constant=True, name='lung fractional tissue volume'),
    mc.Parameter('FVsp', 0.0026, 'litre_per_kg', constant=True, name='spleen fractional tissue volume'),
    mc.Parameter('FVmu', 0.4, 'litre_per_kg', constant=True, name='muscle fractional tissue volume'),

    # FIXME: check pancreatic tissue fraction
    mc.Parameter('FVpa', 0.01, 'litre_per_kg', constant=True, name='pancreas fractional tissue volume'),

    mc.Parameter('FVve', 0.0514, 'litre_per_kg', constant=True, name='venous fractional tissue volume'),
    mc.Parameter('FVar', 0.0257, 'litre_per_kg', constant=True, name='arterial fractional tissue volume'),
    # FIXME: calculate with haematocrit
    mc.Parameter('FVpl', 0.0424, 'litre_per_kg', constant=True, name='plasma fractional tissue volume'),
    # mc.Parameter('FVrbc', 0.0347, 'litre_per_kg', constant=True, name='erythrocytes fractional tissue volume'),


    # fractional tissue blood flows
    mc.Parameter('FQre', 0, '-', constant=False, name='rest of body fractional tissue blood flow'),

    mc.Parameter('FQad', 0.050, '-', constant=True, name='adipose fractional tissue blood flow'),
    mc.Parameter('FQbr', 0.012, '-', constant=True, name='brain fractional tissue blood flow'),
    mc.Parameter('FQhe', 0.040, '-', constant=True, name='heart fractional tissue blood flow'),
    mc.Parameter('FQgu', 0.146, '-', constant=True, name='gut fractional tissue blood flow'),
    mc.Parameter('FQki', 0.190, '-', constant=True, name='kidney fractional tissue blood flow'),
    mc.Parameter('FQh',  0.215, '-', constant=True, name='hepatic (venous side) fractional tissue blood flow'),
    mc.Parameter('FQlu', 1, '-', constant=True, name='lung fractional tissue blood flow'),
    mc.Parameter('FQsp', 0.017, '-', constant=True, name='spleen fractional tissue blood flow'),
    mc.Parameter('FQmu', 0.17, '-', constant=True, name='muscle fractional tissue blood flow'),
    # FIXME: check pancreatic perfusion fraction
    mc.Parameter('FQpa', 0.017, '-', constant=True, name='pancreas fractional tissue blood flow'),
]

# species specific parameters
for s_id, s_dict in SUBSTANCES_BODY.items():

    parameters.extend([
        # molecular weights
        mc.Parameter(f'Mr_{s_id}', s_dict["Mr"], 'g_per_mole', constant=True,
                     name=f'Molecular weight {s_id} [g/mole]'),

        # dosing
        mc.Parameter(f'IVDOSE_{s_id}', s_dict["IVDOSE"], 'mg', constant=True,
                     name=f'IV bolus dose {s_id} [mg]'),
        mc.Parameter(f'PODOSE_{s_id}', s_dict["PODOSE"], 'mg', constant=True,
                     name=f'oral bolus dose {s_id} [mg]'),

        # absorption
        mc.Parameter(f'Ka_{s_id}', s_dict["Ka"], 'per_h', constant=True,
                     name=f'Ka [1/hr] absorption {s_id}'),
        mc.Parameter(f'F_{s_id}', s_dict["F"], '-', constant=True,
                     name=f'fraction absorbed {s_id}'),

        # injection kinetics (IV)
        # bolus parameters
        mc.Parameter(f'ti_{s_id}', 10, 's', constant=True,
                     name=f'injection time {s_id} [s]'),
        mc.Parameter(f'Ki_{s_id}', 1, 'per_h', constant=False,
                     name=f'Ki [1/hr] injection {s_id}'),
        # continuous infusion
        mc.Parameter(f'Ri_{s_id}', 0, 'mg_per_min', constant=True,
                     name=f'Ri [mg/min] rate of injection {s_id}'),
        mc.Parameter(f'cum_dose_{s_id}', 0, 'mg', constant=False,
                     name=f'Cumulative dose due to infusion {s_id}'),

        # in vitro binding data
        mc.Parameter(f'fup_{s_id}', s_dict["fup"], '-', constant=True,
                     name=f'fraction unbound in plasma {s_id}'),
        mc.Parameter(f'BP_{s_id}', s_dict["BP"], '-', constant=True,
                     name=f'blood to plasma ratio {s_id}'),

        # renal clearance
        # FIXME: handle via kidney model
        mc.Parameter(f'CLrenal_{s_id}', s_dict["CLrenal"], 'litre_per_h',
                     constant=True, name=f'renal clearance {s_id} [L/hr]'),
    ])

    # Tissue partition coefficients
    for c_id, c_name in COMPARTMENTS_BODY.items():
        if c_id in ['ve', 'ar']:
            continue

        if c_id in SUBMODEL_SID_DICT.keys():
            # blood compartment of explicit tissue model
            pass

        else:
            # only tissue compartment
            value = s_dict[f'Kp{c_id}']
            if isinstance(value, str):
                # set value via assignment rule
                parameters.append(
                    mc.Parameter(f'Kp{c_id}_{s_id}', value=None, unit='-', constant=False,
                                 name=f'{c_name} plasma partition coefficient')
                )
                rules.append(
                    mc.AssignmentRule(f'Kp{c_id}_{s_id}', value, '-')
                )
            else:
                # create constant parameter with numerical value
                parameters.append(
                    mc.Parameter(f'Kp{c_id}_{s_id}', value=value, unit='-', constant=True,
                                 name=f'{c_name} plasma partition coefficient')
                )

##############################################################
# Assignments
##############################################################
assignments = []

##############################################################
# AssignmentRules
##############################################################
rules = rules + [
    # Rest body volume
    mc.AssignmentRule('FVre', '1.0 litre_per_kg - (FVad + FVbr + FVhe + FVgu + FVki + FVli + FVlu + FVsp + FVmu + FVpa + FVve + FVar + FVpl)', 'litre_per_kg'),
    # Rest body perfusion
    mc.AssignmentRule('FQre', '1.0 dimensionless - (FQmu + FQad + FQbr + FQhe + FQki + FQh)', 'dimensionless'),

    # Body surface area (Haycock1978)
    mc.AssignmentRule('BSA', '0.024265 m2 * power(BW/1 kg, 0.5378) * power(HEIGHT/1 cm, 0.3964)', 'm2'),

    # cardiac output (depending on heart rate and bodyweight)
    mc.AssignmentRule('CO', 'BW*COBW + (HR-HRrest)*COHRI / 60 s_per_min', 'ml_per_s'),
    # cardiac output (depending on bodyweight)
    mc.AssignmentRule('QC', 'CO/1000 ml_per_litre * 3600 s_per_h', 'litre_per_h'),

    # volumes
    mc.AssignmentRule('Vad', 'BW*FVad', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vbr', 'BW*FVbr', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vhe', 'BW*FVhe', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vgu', 'BW*FVgu', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vki', 'BW*FVki', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vli', 'BW*FVli', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vlu', 'BW*FVlu', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vsp', 'BW*FVsp', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vmu', 'BW*FVmu', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vpa', 'BW*FVpa', UNIT_KIND_LITRE),
    # mc.AssignmentRule('Vrbc', 'BW*FVrbc', UNIT_KIND_LITRE),

    mc.AssignmentRule('Vve', 'BW*FVve', UNIT_KIND_LITRE),
    mc.AssignmentRule('Var', 'BW*FVar', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vpl', 'BW*FVpl', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vre', 'BW*FVre', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vplas_ven', 'Vpl*Vve/(Vve + Var)', UNIT_KIND_LITRE),
    mc.AssignmentRule('Vplas_art', 'Vpl*Var/(Vve + Var)', UNIT_KIND_LITRE),

    # blood flows
    mc.AssignmentRule('Qad', 'QC*FQad', 'litre_per_h', name='adipose blood flow'),
    mc.AssignmentRule('Qbr', 'QC*FQbr', 'litre_per_h', name='brain blood flow'),
    mc.AssignmentRule('Qhe', 'QC*FQhe', 'litre_per_h', name='heart blood flow'),
    mc.AssignmentRule('Qgu', 'QC*FQgu', 'litre_per_h', name='gut blood flow'),
    mc.AssignmentRule('Qki', 'QC*FQki', 'litre_per_h', name='kidney blood flow'),
    mc.AssignmentRule('Qh', 'QC*FQh', 'litre_per_h', name='hepatic (venous side) blood flow'),
    mc.AssignmentRule('Qha', 'Qh - Qgu - Qsp - Qpa', 'litre_per_h', name='hepatic artery blood flow'),
    mc.AssignmentRule('Qlu', 'QC*FQlu', 'litre_per_h', name='lung blood flow'),
    mc.AssignmentRule('Qsp', 'QC*FQsp', 'litre_per_h', name='spleen blood flow'),
    mc.AssignmentRule('Qmu', 'QC*FQmu', 'litre_per_h', name='muscle blood flow'),
    mc.AssignmentRule('Qpa', 'QC*FQpa', 'litre_per_h', name='pancreas blood flow'),
    mc.AssignmentRule('Qre', 'QC*FQre', 'litre_per_h', name='rest of body blood flow'),
]

# --------------------------------------------
# Volumes for explicit tissue models
# --------------------------------------------
for c_id in SUBMODEL_SID_DICT.keys():
    if c_id not in ['ve', 'ar']:
        rules.extend([
            mc.AssignmentRule(f'V{c_id}_tissue', value=f'V{c_id}*Ftissue', unit=UNIT_KIND_LITRE),
            mc.AssignmentRule(f'V{c_id}_blood', value=f'V{c_id}*(1 dimensionless - Ftissue)', unit=UNIT_KIND_LITRE),
        ])

for s_id, s_dict in SUBSTANCES_BODY.items():
    s_name = s_dict['name']

    # free concentrations & clearance
    rules.extend([
        mc.AssignmentRule(f'Cpl_ve_{s_id}', f'Cve_{s_id}/BP_{s_id}', 'mM',
                          name=f'{s_name} venous plasma concentration'),
        #mc.AssignmentRule('Cli_free_{}'.format(s_id),
        #                  'Cli_{}*fup_{}'.format(s_id, s_id), 'mM',
        #                  name='{} free liver concentration'.format(s_name)),

        mc.AssignmentRule(f'Cki_free_{s_id}', f'Cki_{s_id}*fup_{s_id}', 'mM',
                          name=f'{s_name} free kidney concentration'),
    ])

    # injection
    rules.extend([
        mc.AssignmentRule(f'Ki_{s_id}', f'1.386 dimensionless/ti_{s_id} * 3600 s_per_h', 'mg_per_h'),  # 2*ln2
    ])

    # ---------------------------------
    # X Amount [mg], C Concentration
    # ---------------------------------
    for c_id, c_name in COMPARTMENTS_BODY.items():

        if c_id in SUBMODEL_SID_DICT.keys() and c_id not in ["ve", "ar"]:
            # blood compartment of explicit tissue model
            sid_ex = f'A{c_id}_blood_{s_id}'
            cid_ex = f'V{c_id}_blood'
            rules.extend([
                # FIXME: this depends on the unit of the species
                mc.AssignmentRule(f'C{c_id}_blood_{s_id}',
                                  f'A{c_id}_blood_{s_id}/V{c_id}_blood',
                                  'mM', name=f'{s_name} concentration ({c_name})'),

                mc.AssignmentRule(f'X{c_id}_blood_{s_id}',
                                  f'A{c_id}_blood_{s_id}*Mr_{s_id}',
                                  f'mg', name='{s_name} amount ({c_name})'),

                mc.AssignmentRule(f'M{c_id}_blood_{s_id}',
                                  f'A{c_id}_blood_{s_id}/V{c_id}_blood*Mr_{s_id}',
                                  'mg_per_litre', name=f'{s_name} amount ({c_name})')
            ])
        else:
            # compartment with distribution
            rules.extend([
                # FIXME: this depends on the unit of the species
                mc.AssignmentRule(f'C{c_id}_{s_id}',
                                  f'A{c_id}_{s_id}/V{c_id}',
                                  'mM', name=f'{s_name} concentration ({c_name})'),

                mc.AssignmentRule(f'X{c_id}_{s_id}',
                                  f'A{c_id}_{s_id}*Mr_{s_id}',
                                  'mg', name=f'{s_name} amount ({c_name})'),

                mc.AssignmentRule(f'M{c_id}_{s_id}',
                                  f'A{c_id}_{s_id}/V{c_id}*Mr_{s_id}',
                                  'mg_per_litre', name=f'{s_name} amount ({c_name})')
            ])

    # urine metabolites
    c_id, c_name = ("urine", "urine")
    rules.append(
        mc.AssignmentRule(f'X{c_id}_{s_id}',
                          f'A{c_id}_{s_id}*Mr_{s_id}',
                          'mg', name=f'{s_name} amount ({c_name})'),
    )


##############################################################
# Reactions
##############################################################
reactions = REACTIONS


for s_id, s_dict in SUBSTANCES_BODY.items():
    s_name = s_dict['name']
    reactions.extend([
        # --------------------
        # injection
        # --------------------
        # Injection venous (I.V. dose)
        ReactionTemplate(rid=f"Injection_{s_id}",
                         name=f"injection {s_name}",
                         formula=(f"Ki_{s_id}*IVDOSE_{s_id}/Mr_{s_id}", 'mmole_per_h'),
                         equation=f"-> Ave_{s_id}",
                         compartment='Vve'),
        ReactionTemplate(rid=f"Infusion_{s_id}",
                         name=f"infusion {s_name}",
                         formula=(f"Ri_{s_id}/Mr_{s_id}*60 min_per_h", 'mmole_per_h'),
                         equation=f"-> Ave_{s_id}",
                         compartment='Vve'),

        # ---------------------------
        # absorption (oral dose gut)
        # ---------------------------
        ReactionTemplate(rid="absorption_{}".format(s_id),
                         name="absorption {}".format(s_name),
                         formula=("Ka_{}*PODOSE_{}/Mr_{}*F_{}".format(s_id, s_id, s_id, s_id), 'mmole_per_h'),
                         equation="-> Agu_{}".format(s_id),
                         compartment='Vgu'),

        # --------------------
        # renal clearance
        # --------------------
        ReactionTemplate(rid="reclearance_{}".format(s_id),
                         name="clearance {} (kidney)".format(s_name),
                         formula=("CLrenal_{}*Cki_free_{}".format(s_id, s_id), 'mmole_per_h'),
                         equation='Aki_{} -> Aurine_{}'.format(s_id, s_id), compartment='Vki'),
    ])

    for c_id, c_name in COMPARTMENTS_BODY.items():
        if c_id in ['ve', 'ar']:
            continue

        # --------------------
        # ve -> lung -> ar
        # --------------------
        if c_id == 'lu':
            rid_in = f"Flow_ve_{c_id}_{s_id}"
            name_in = f"inflow {c_name} {s_name}"

            rid_out = f"Flow_{c_id}_ar_{s_id}"
            name_out = f"outflow {c_name} {s_name}"

            if c_id in SUBMODEL_SID_DICT:
                # only distribution in blood volume
                reactions.extend([
                    ReactionTemplate(rid=rid_in, name=name_in,
                                 formula=(f"Q{c_id}*Cve_{s_id}", 'mmole_per_h'),
                                 equation=f'Ave_{s_id} -> A{c_id}_blood_{s_id}'),
                    ReactionTemplate(rid=rid_out, name=name_out,
                                 formula=(f"Q{c_id}*C{c_id}_blood_{s_id}*BP_{s_id}", 'mmole_per_h'),
                                 equation=f'A{c_id}_blood_{s_id} -> Aar_{s_id}'),
                ])
            else:
                # distribution coefficient
                reactions.extend([
                    ReactionTemplate(rid=rid_in, name=name_in,
                                 formula=(f"Q{c_id}*Cve_{s_id}", 'mmole_per_h'),
                                 equation=f'Ave_{s_id} -> A{c_id}_{s_id}'),
                    ReactionTemplate(rid=rid_out, name=name_out,
                                 formula=(f"Q{c_id}*(C{c_id}_{s_id}/Kp{c_id}_{s_id}*BP_{s_id})", 'mmole_per_h'),
                                 equation=f'A{c_id}_{s_id} -> Aar_{s_id}'),
                ])

        # --------------------
        # ar -> organ -> ve
        # --------------------
        if c_id in ['ad', 'br', 'he', 'ki', 'mu', 're']:
            rid_in = f"Flow_ar_{c_id}_{s_id}"
            name_in = f"inflow {c_name} {s_name}"
            rid_out = f"Flow_{c_id}_ve_{s_id}"
            name_out = f"outflow {c_name} {s_name}"

            if c_id in SUBMODEL_SID_DICT:
                # only distribution in blood volume
                reactions.extend([
                    ReactionTemplate(rid=rid_in, name=name_in,
                                 formula=(f"Q{c_id}*Car_{s_id}", 'mmole_per_h'),
                                 equation=f'Aar_{s_id} -> A{c_id}_blood_{s_id}'),
                    ReactionTemplate(rid=rid_out, name=name_out,
                                 formula=(f"Q{c_id}*C{c_id}_blood_{s_id}*BP_{s_id}", 'mmole_per_h'),
                                 equation=f'A{c_id}_blood_{s_id} -> Ave_{s_id}'),
                ])
            else:
                # distribution coefficient
                reactions.extend([
                    ReactionTemplate(rid=rid_in, name=name_in,
                                 formula=(f"Q{c_id}*Car_{s_id}", 'mmole_per_h'),
                                 equation=f'Aar_{s_id} -> A{c_id}_{s_id}'),
                    ReactionTemplate(rid=rid_out, name=name_out,
                                 formula=(f"Q{c_id}*(C{c_id}_{s_id}/Kp{c_id}_{s_id}*BP_{s_id})", 'mmole_per_h'),
                                 equation=f'A{c_id}_{s_id} -> Ave_{s_id}'),
                ])
        # --------------------
        # ar -> organ -> li
        # --------------------
        if c_id in ['gu', 'sp', 'pa']:
            rid_in = f'Flow_ar_{c_id}_{s_id}'
            name_in = f'inflow {c_name} {s_name}'
            rid_out = f'Flow_{c_id}_li_{s_id}'
            name_out = f'outflow {c_name} {s_name}'

            if 'li' in SUBMODEL_SID_DICT:
                ali = f'Ali_blood_{s_id}'
            else:
                ali = f'Ali_{s_id}'

            if c_id in SUBMODEL_SID_DICT:
                reactions.extend([
                    # only distribution in blood volume
                    ReactionTemplate(rid=rid_in, name=name_in,
                                     formula=(f'Q{c_id}*Car_{s_id}', 'mmole_per_h'),
                                     equation=f'Aar_{s_id} -> A{c_id}_blood_{s_id}'),
                    ReactionTemplate(rid=rid_out, name=name_out,
                                     formula=(f'Q{c_id}*C{c_id}_blood_{s_id}*BP_{s_id})', 'mmole_per_h'),
                                     equation=f'A{c_id}_blood_{s_id} -> {ali}'),
                ])
            else:
                reactions.extend([
                    # distribution coefficient
                    ReactionTemplate(rid=rid_in, name=name_in,
                                     formula=(f'Q{c_id}*Car_{s_id}', 'mmole_per_h'),
                                     equation=f'Aar_{s_id} -> A{c_id}_{s_id}'),
                    ReactionTemplate(rid=rid_out, name=name_out,
                                     formula=(f'Q{c_id}*(C{c_id}_{s_id}/Kp{c_id}_{s_id}*BP_{s_id})', 'mmole_per_h'),
                                     equation=f'A{c_id}_{s_id} -> {ali}'),
                ])

        # --------------------
        # ar -> li -> ve
        # --------------------
        if c_id == "li":
            # liver
            if 'li' in SUBMODEL_SID_DICT:
                reactions.extend([
                    ReactionTemplate(rid=f"Flow_ar_li_{s_id}",
                                     name=f"inflow liver {s_name}",
                                     formula=(f"Qha*Car_{s_id}", 'mmole_per_h'),
                                     equation=f'Aar_{s_id} -> Ali_blood_{s_id}'),
                    ReactionTemplate(rid=f"Flow_li_ve_{s_id}",
                                     name=f"outflow liver {s_name}",
                                     formula=(f"Qh*Cli_blood_{s_id}*BP_{s_id}", 'mmole_per_h'),
                                     equation=f'Ali_blood_{s_id} -> Ave_{s_id}'),
                ])
            else:
                reactions.extend([
                    ReactionTemplate(rid=f"Flow_ar_li_{s_id}",
                                     name=f"inflow liver {s_name}",
                                     formula=(f"Qha*Car_{s_id}", 'mmole_per_h'),
                                     equation=f'Aar_{s_id} -> Ali_{s_id}'),
                    ReactionTemplate(rid=f"Flow_li_ve_{s_id}",
                                     name=f"outflow liver {s_name}",
                                     formula=(f"Qh*(Cli_{s_id}/Kpli_{s_id}*BP_{s_id})", 'mmole_per_h'),
                                     equation=f'Ali_{s_id} -> Ave_{s_id}'),
                ])

assignments.extend([
    # liver balance
    mc.AssignmentRule(f'inflow_li_{s_id}', f'Flow_gu_li_{s_id} + Flow_sp_li_{s_id} + Flow_pa_li_{s_id} + Flow_ar_li_{s_id}',
                'mmole_per_h'),
    mc.AssignmentRule(f'outflow_li_{s_id}',
                f'Flow_li_ve_{s_id}', 'mmole_per_h'),
])

##############################################################
# RateRules
##############################################################
rate_rules = []

for s_id, s_dict in SUBSTANCES_BODY.items():
    rate_rules.extend([


        # absorption of dose
        mc.RateRule(f'PODOSE_{s_id}', f'-absorption_{s_id}*Mr_{s_id}', 'mg_per_h'),
        # injection of dose
        mc.RateRule(f'IVDOSE_{s_id}', f'-Injection_{s_id}*Mr_{s_id}', 'mg_per_h'),

        # cumulative infusion dose
        mc.RateRule(f'cum_dose_{s_id}', f'Ri_{s_id}*60 min_per_h', 'mg_per_h'),
    ])
