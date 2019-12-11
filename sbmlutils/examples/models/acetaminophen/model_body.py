# coding=utf-8 -*-
"""
PKPD model for whole-body acetaminophen metabolism
"""
from sbmlutils.modelcreator import creator

import os
import logging
from copy import deepcopy
from sbmlutils.examples.models.acetaminophen import templates

from sbmlutils.units import *
from sbmlutils.annotation.sbo import *
from sbmlutils.factory import *

from sbmlutils.factory import PORT_SUFFIX
import sbmlutils.comp as mcomp

# -----------------------------------------------------------------------------
# Whole Body Metabolism
# -----------------------------------------------------------------------------
mid = "paracetamol_body"

ports = []
deletions = []
replacedElements = []
replacedBy = []

# -----------------------------------------------------------------------------
# Submodels
# -----------------------------------------------------------------------------
COMPARTMENTS_BODY = {
    "gu": "gut",
    "ki": "kidney",
    "li": "liver",
    "lu": "lung",
    "pa": "pancreas",
    "sp": "spleen",
    "re": "rest",
    'ar': "arterial blood",
    "ve": "venous blood",
}

SUBMODEL_SID_DICT = {  # tissue to submodel mapping
    "ki": "KI",     # kidney
    "li": "LI",     # liver
}

kidney_id = 'paracetamol_kidney'
liver_id = 'paracetamol_liver'

externalModelDefinitions = [
    mcomp.ExternalModelDefinition(sid="kidney", source=f"{kidney_id}.xml", modelRef=kidney_id),
    mcomp.ExternalModelDefinition(sid="liver", source=f"{liver_id}.xml", modelRef=liver_id),
]

submodels = [
    mcomp.Submodel(sid=SUBMODEL_SID_DICT['ki'], modelRef="kidney"),
    mcomp.Submodel(sid=SUBMODEL_SID_DICT['li'], modelRef="liver"),
]

for emd in externalModelDefinitions:
    logging.info(f"{emd} ({os.path.abspath(emd.source)})")

# -----------------------------------------------------------------------------
# substances transported via circulation
SUBSTANCES_BODY = {
    "apap": {
        "name": "paracetamol",
        "unit": "mmole",
        # initial concentration
        "cinit": 0.0,  # [mmole/l]
        # Molecular weight
        "Mr": 151.1626 ,  # [g/mole]
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 1.0, 'F': 1.0,  # FIXME: THIS DOES NOT WORK
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes, partition coefficient [-]
        'BP': 1.0, 'fumic': 1.0,  # "Kp": 1.0, 'fup': 1.0,
    },
    "apapglu": {
        "name": "paracetamol glucuronide",
        "unit": "mmole",
        # initial concentration
        "cinit": 0,  # [mmole/l]
        # molecular weight
        "Mr": 327.28672,  # [g/mole]
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 1.0, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'BP': 1.0, 'fumic': 1.0,  # "Kp": 1.0, 'fup': 1.0,
    },
    "apapsul": {
        "name": "paracetamol sulfate",
        "unit": "mmole",
        # initial concentration
        "cinit": 0,  # [mmole/l]
        # molecular weight
        "Mr": 231.2268,  # [g/mole]
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 1.0, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'BP': 1.0, 'fumic': 1.0,  # "Kp": 1.0, 'fup': 1.0,
    },
    "apapcys": {
        "name": "paracetamol cysteine",
        "unit": "mmole",
        # initial concentration
        "cinit": 0,  # [mmole/l]
        # molecular weight
        "Mr": 270.306,  # [g/mole]
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 1.0, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'BP': 1.0, 'fumic': 1.0,  # "Kp": 1.0, 'fup': 1.0,
    },
    "apapgsh": {
        "name": "paracetamol glutathione",
        "unit": "mmole",
        # initial concentration
        "cinit": 0,  # [mmole/l]
        # molecular weight
        "Mr": 151.1626,  # [g/mole]         # FIXME: mass is set to paracetamol mass -> correlates to given mass of paracetamol
        #         # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 1.0, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'BP': 1.0, 'fumic': 1.0,  # "Kp": 1.0, 'fup': 1.0,
    },
    "apapmer": {
        "name": "paracetamol mercapturate",
        "unit": "mmole",
        # initial concentration
        "cinit": 0,  # [mmole/l]
        # molecular weight
        "Mr": 151.1626,  # [g/mole]         # FIXME: mass is set to paracetamol mass -> correlates to given mass of paracetamol
        # doses [mg]
        'IVDOSE': 0, 'PODOSE': 0,
        # Ka [1/hr] absorption & fraction absorbed [-]
        'Ka': 1.0, 'F': 1.0,
        # fraction unbound in plasma (fup), blood to plasma ration (BP), fraction unbound microsomes
        'BP': 1.0, 'fumic': 1.0,  # "Kp": 1.0, 'fup': 1.0,
    },

}

# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------
model_units = deepcopy(templates.MODEL_UNITS)

# units (kind, exponent, scale=0, multiplier=1.0)
units = deepcopy(templates.UNITS)
units.extend([
    UNIT_kg,
    UNIT_per_min,
    UNIT_s,
    UNIT_mg,
    UNIT_ml,
    Unit('hr', [(UNIT_KIND_SECOND, 1.0, 0, 3600)], port=True),
    Unit('per_hr', [(UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True),
    Unit('cm', [(UNIT_KIND_METRE, 1.0, -2, 1.0)], port=True),
    Unit('mg_per_l', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0, 0, 1.0)], port=True),
    Unit('mg_per_g', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                     (UNIT_KIND_GRAM, -1.0, 0, 1.0)], port=True),
    Unit('mg_per_hr', [(UNIT_KIND_GRAM, 1.0, -3, 1.0),
                 (UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True),
    Unit('l_per_min', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                     (UNIT_KIND_SECOND, -1.0, 0, 60)], port=True),
    Unit('l_per_hr', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                              (UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True),
    Unit('l_per_kg', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                     (UNIT_KIND_GRAM, -1.0, 3, 1.0)], port=True),
    Unit('l_per_ml', [(UNIT_KIND_LITRE, 1.0, 0, 1.0),
                             (UNIT_KIND_LITRE, -1.0, -3, 1.0)], port=True),
    Unit('g_per_mole', [(UNIT_KIND_GRAM, 1.0, 0, 1.0),
                           (UNIT_KIND_MOLE, -1.0, 0, 1.0)], port=True),
    Unit('m2_per_kg', [(UNIT_KIND_METRE, 2.0, 0, 1.0),
                           (UNIT_KIND_GRAM, -1.0, 3, 1.0)], port=True),
    Unit('mg_per_min', [(UNIT_KIND_GRAM, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 60)], port=True),
    Unit('mmole_per_hr', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                         (UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True),
    Unit('mmole_per_l', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0, 0, 1.0)], port=True),
    Unit('mmole_per_min_kg', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                              (UNIT_KIND_SECOND, -1.0, 0, 60), (UNIT_KIND_GRAM, -1.0, 3, 1)], port=True),
    Unit('mmole_per_hr_ml', [(UNIT_KIND_MOLE, 1.0, -3, 1),
                             (UNIT_KIND_SECOND, -1.0, 0, 3600),
                             (UNIT_KIND_LITRE, -1.0, -3, 1.0)], port=True),
    Unit('ml_per_s', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                         (UNIT_KIND_SECOND, -1.0, 0, 1)], port=True),
    Unit('ml_per_s_kg', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                           (UNIT_KIND_SECOND, -1.0, 0, 1), (UNIT_KIND_GRAM, -1.0, 3, 1)], port=True),
    Unit('ml_per_l', [(UNIT_KIND_LITRE, 1.0, -3, 1.0),
                          (UNIT_KIND_LITRE, -1.0, 0, 1)], port=True),
    Unit('mulitre_per_g', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                           (UNIT_KIND_GRAM, -1.0, 0, 1)], port=True),
    Unit('mul_per_min_mg', [(UNIT_KIND_LITRE, 1.0, -6, 1.0),
                                (UNIT_KIND_SECOND, -1.0, 0, 60),
                                (UNIT_KIND_GRAM, -1.0, -3, 1.0)], port=True),
    Unit('min_per_hr', [(UNIT_KIND_SECOND, 1.0, 0, 60),
                  (UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True),
    Unit('s_per_min', [(UNIT_KIND_SECOND, 1.0, 0, 60),
                          (UNIT_KIND_SECOND, -1.0, 0, 3600)], metaId='meta_s_per_min', port=True),
    Unit('s_per_hr', [(UNIT_KIND_SECOND, 1.0, 0, 1.0),
                        (UNIT_KIND_SECOND, -1.0, 0, 3600)], port=True),
])

# unit replacements
unit_replace_keys = [unit.sid for unit in templates.UNITS]
replace_tissues = ['ki', 'li']

for key in unit_replace_keys:
    for tissue in replace_tissues:
        replacedElements.append(
            mcomp.ReplacedElement(sid=f"{tissue}_{key}_RE", metaId=f"{tissue}_{key}_RE", elementRef=f"{key}",
                                  submodelRef=SUBMODEL_SID_DICT[tissue], portRef=f"{key}{PORT_SUFFIX}")
        )

# -------------------------------------------------------------------------------------------------
# Compartments
# -------------------------------------------------------------------------------------------------
compartments = [
    Compartment('Vre', metaId="meta_Vre", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='rest of body'),
    Compartment('Vgu', metaId="meta_Vgu", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='gut'),
    Compartment('Vki', metaId="meta_Vki", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='kidney'),
    Compartment('Vli', metaId="meta_Vli", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='liver'),
    Compartment('Vlu', metaId="meta_Vlu", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='lung'),
    Compartment('Vsp', metaId="meta_Vsp", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='spleen'),
    Compartment('Vpa', metaId="meta_Vpa", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='pancreas'),

    Compartment('Vve', metaId="meta_Vve", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='venous blood'),
    Compartment('Var', metaId="meta_Var", value=1, unit=UNIT_KIND_LITRE,
                constant=False, name='arterial blood'),

    Compartment('Vurine', metaId="meta_Vurine", value=1, unit=UNIT_KIND_LITRE,
                constant=True, name='urine'),
]

# create blood and tissue compartments (for correct blood volume)
for c_id in COMPARTMENTS_BODY.keys():
    if c_id not in ["ar", "ve"]:
        compartments.extend([
            Compartment(f'V{c_id}_tissue', value=1, unit=UNIT_KIND_LITRE, constant=False,
                        name=f'{c_id} tissue', metaId=f'meta_V{c_id}_tissue', port=True),
            Compartment(f'V{c_id}_blood', value=1, unit=UNIT_KIND_LITRE, constant=False,
                        name=f'{c_id} blood', metaId=f'meta_V{c_id}_blood', port=True),
        ])

# replace volumes of submodels
replacedElements.extend([

    # kidney
    mcomp.ReplacedElement(sid="Vki_tissue_RE", metaId="Vki_tissue_RE", elementRef="Vki_tissue",
                          submodelRef=SUBMODEL_SID_DICT['ki'], portRef=f"Vki{PORT_SUFFIX}"),
    mcomp.ReplacedElement(sid="Vki_blood_RE", metaId="Vki_blood_RE", elementRef="Vki_blood",
                          submodelRef=SUBMODEL_SID_DICT['ki'], portRef=f"Vext{PORT_SUFFIX}"),
    # liver
    mcomp.ReplacedElement(sid="Vli_tissue_RE", metaId="Vli_tissue_RE", elementRef="Vli_tissue",
                          submodelRef=SUBMODEL_SID_DICT['li'], portRef=f"Vli{PORT_SUFFIX}"),
    mcomp.ReplacedElement(sid="Vli_blood_RE", metaId="Vli_blood_RE", elementRef="Vli_blood",
                          submodelRef=SUBMODEL_SID_DICT['li'], portRef=f"Vext{PORT_SUFFIX}"),

])

# -------------------------------------------------------------------------------------------------
# Species
# -------------------------------------------------------------------------------------------------
species = []
for s_id, s_dict in SUBSTANCES_BODY.items():
    for c_id, c_name in COMPARTMENTS_BODY.items():
        if c_id in ['ve', 'ar']:
            sid_ex = f'A{c_id}_{s_id}'
            cid_ex = f'V{c_id}'
        else:
            # blood compartment
            sid_ex = f'A{c_id}_blood_{s_id}'
            cid_ex = f'V{c_id}_blood'

        species.append(
            Species(sid_ex,
                    metaId=f"meta_{sid_ex}",
                    initialConcentration=s_dict['cinit'],
                    compartment=cid_ex,
                    substanceUnit=s_dict['unit'],
                    name=f"{s_dict['name']} ({c_name})",
                    hasOnlySubstanceUnits=True, port=True)
        )

    species.append(
        Species(f'Aurine_{s_id}',
                metaId=f"meta_Aurine_{s_id}",
                initialConcentration=0,
                compartment="Vurine",
                substanceUnit=s_dict['unit'],
                name=f"{s_dict['name']} (urine)",
                hasOnlySubstanceUnits=True),
    )

# replace species
replaced_species = {
    "li": ['apap','apapglu','apapsul','apapcys','apapgsh','apapmer'],
    "ki": ['apap','apapglu','apapsul','apapcys','apapgsh','apapmer'],

}
# blood to external species
for tkey, skey_list in replaced_species.items():
    for skey in skey_list:
        replacedElements.append(
            mcomp.ReplacedElement(sid=f"A{tkey}_blood_{skey}_RE", metaId=f"A{tkey}_blood_{skey}_RE",
                                  elementRef=f"A{tkey}_blood_{skey}",
                                  submodelRef=SUBMODEL_SID_DICT[tkey],
                                  portRef=f"{skey}_ext{PORT_SUFFIX}")
        )
# urine to urine species
for skey in ['apap','apapglu','apapsul','apapcys','apapgsh','apapmer']:
    replacedElements.append(
            mcomp.ReplacedElement(sid=f"Aurine_{skey}_RE", metaId=f"Aurine_{skey}_RE",
                                  elementRef=f"Aurine_{skey}",
                                  submodelRef=SUBMODEL_SID_DICT["ki"],
                                  portRef=f"{skey}_urine{PORT_SUFFIX}")
        )

# -------------------------------------------------------------------------------------------------
# Parameters
# -------------------------------------------------------------------------------------------------
rules = []
parameters = [
    # conversion factors
    Parameter('conversion_ml_per_l', 1000, 'ml_per_l', constant=True, name='volume conversion factor'),
    Parameter('conversion_l_per_ml', 0.001, 'l_per_ml', constant=True, name='volume conversion factor'),

    # whole body data
    Parameter('BW', 75, 'kg', constant=True, name='body weight [kg]'),
    Parameter('HEIGHT', 170, 'cm', constant=True, name='height [cm]'),
    Parameter('HR', 70, 'per_min', constant=True, name='heart rate [1/min]'),
    Parameter('HRrest', 70, 'per_min', constant=True, name='heart rate [1/min]'),

    Parameter('BSA', 0, 'm2', constant=False, name='body surface area [m^2]'),
    Parameter('COBW', 1.548, 'ml_per_s_kg', constant=True, name='cardiac output per bodyweight [ml/s/kg]'),
    Parameter('CO', 108.33, 'ml_per_s', constant=False, name='cardiac output [ml/s]'),
    Parameter('QC', 108.33*1000*60, 'l_per_min', constant=False, name='cardiac output [L/hr]'),
    Parameter('COHRI', 150, 'ml', constant=True, name="increase of cardiac output per heartbeat [ml/min*min]"),

    # fractional tissue volumes
    Parameter('Fblood', 0.02, '-', constant=False, name='blood fraction of organ volume'),

    # fractional tissue volumes
    Parameter('FVgu', 0.0171, 'l_per_kg', constant=True, name='gut fractional tissue volume'),
    Parameter('FVki', 0.0044, 'l_per_kg', constant=True, name='kidney fractional tissue volume'),
    Parameter('FVli', 0.0210, 'l_per_kg', constant=True, name='liver fractional tissue volume'),
    Parameter('FVlu', 0.0076, 'l_per_kg', constant=True, name='lung fractional tissue volume'),
    Parameter('FVsp', 0.0026, 'l_per_kg', constant=True, name='spleen fractional tissue volume'),
    Parameter('FVpa', 0.01, 'l_per_kg', constant=True, name='pancreas fractional tissue volume'),
    Parameter('FVre', 0, 'l_per_kg', constant=False, name='rest of body fractional tissue volume'),  # calculated based on other tissues

    Parameter('FVve', 0.0514, 'l_per_kg', constant=True, name='venous fractional tissue volume'),
    Parameter('FVar', 0.0257, 'l_per_kg', constant=True, name='arterial fractional tissue volume'),

    # fractional tissue blood flows
    Parameter('FQgu', 0.146, '-', constant=True, name='gut fractional tissue blood flow'),
    Parameter('FQki', 0.190, '-', constant=True, name='kidney fractional tissue blood flow'),
    Parameter('FQh',  0.215, '-', constant=True, name='hepatic (venous side) fractional tissue blood flow'),
    Parameter('FQlu', 1, '-', constant=True, name='lung fractional tissue blood flow'),
    Parameter('FQsp', 0.017, '-', constant=True, name='spleen fractional tissue blood flow'),
    Parameter('FQpa', 0.017, '-', constant=True, name='pancreas fractional tissue blood flow'),
    Parameter('FQre', 0, '-', constant=False, name='rest of body fractional tissue blood flow'),  # calculated based on other tissues
]

# species specific parameters
for s_id, s_dict in SUBSTANCES_BODY.items():

    parameters.extend([
        # molecular weights
        Parameter(f'Mr_{s_id}', s_dict["Mr"], 'g_per_mole', constant=True,
                  name=f'Molecular weight {s_id} [g/mole]'),

        # dosing
        Parameter(f'IVDOSE_{s_id}', s_dict["IVDOSE"], 'mg', constant=True,
                  name=f'IV bolus dose {s_id} [mg]'),
        Parameter(f'PODOSE_{s_id}', s_dict["PODOSE"], 'mg', constant=True,
                  name=f'oral bolus dose {s_id} [mg]'),

        # absorption
        Parameter(f'Ka_{s_id}', s_dict["Ka"], 'per_hr', constant=True,
                  name=f'Ka [1/hr] absorption {s_id}'),
        Parameter(f'F_{s_id}', s_dict["F"], '-', constant=True,
                  name=f'fraction absorbed {s_id}'),

        # injection kinetics (IV)
        # bolus parameters
        Parameter(f'ti_{s_id}', 10, 's', constant=True,
                  name=f'injection time {s_id} [s]'),
        Parameter(f'Ki_{s_id}', 0.02, 'per_min', constant=False,
                  name=f'Ki [1/min] injection {s_id}'),
        # continuous infusion
        Parameter(f'Ri_{s_id}', 0, 'mg_per_min', constant=True,
                  name=f'Ri [mg/min] rate of injection {s_id}'),
        Parameter(f'cum_dose_{s_id}', 0, 'mg', constant=False,
                  name=f'Cumulative dose due to infusion {s_id}'),

        # in vitro binding data
        # Parameter(f'fup_{s_id}', s_dict["fup"], '-', constant=True,
        #          name=f'fraction unbound in plasma {s_id}'),
        Parameter(f'BP_{s_id}', s_dict["BP"], '-', constant=True,
                  name=f'blood to plasma ratio {s_id}'),
    ])

# -------------------------------------------------------------------------------------------------
# AssignmentRules
# -------------------------------------------------------------------------------------------------
rules = rules + [
    # Rest body volume
    AssignmentRule('FVre', '1.0 l_per_kg - (FVgu + FVki + FVli + FVlu + FVsp + FVpa + FVve + FVar)', 'l_per_kg'),
    # Rest body perfusion
    AssignmentRule('FQre', '1.0 dimensionless - (FQki + FQh)', 'dimensionless'),

    # Body surface area (Haycock1978)
    AssignmentRule('BSA', '0.024265 m2 * power(BW/1 kg, 0.5378) * power(HEIGHT/1 cm, 0.3964)', 'm2'),

    # cardiac output (depending on heart rate and bodyweight)
    AssignmentRule('CO', 'BW*COBW + (HR-HRrest)*COHRI / 60 s_per_min', 'ml_per_s'),
    # cardiac output (depending on bodyweight)
    AssignmentRule('QC', 'CO/1000 ml_per_l * 60 s_per_min', 'l_per_min'),

    # volumes
    AssignmentRule('Vgu', 'BW*FVgu', UNIT_KIND_LITRE),
    AssignmentRule('Vki', 'BW*FVki', UNIT_KIND_LITRE),
    AssignmentRule('Vli', 'BW*FVli', UNIT_KIND_LITRE),
    AssignmentRule('Vlu', 'BW*FVlu', UNIT_KIND_LITRE),
    AssignmentRule('Vsp', 'BW*FVsp', UNIT_KIND_LITRE),
    AssignmentRule('Vpa', 'BW*FVpa', UNIT_KIND_LITRE),
    AssignmentRule('Vre', 'BW*FVre', UNIT_KIND_LITRE),

    # venous and arterial blood volume (corrected for tissue blood volumes)
    AssignmentRule('Vve', 'BW*FVve - FVve/(FVar+FVve) * BW * Fblood * (1 l_per_kg - FVve - FVar)', UNIT_KIND_LITRE),
    AssignmentRule('Var', 'BW*FVar - FVar/(FVar+FVve) * BW * Fblood * (1 l_per_kg - FVve - FVar)', UNIT_KIND_LITRE),

    # blood flows
    AssignmentRule('Qgu', 'QC*FQgu', 'l_per_min', name='gut blood flow'),
    AssignmentRule('Qki', 'QC*FQki', 'l_per_min', name='kidney blood flow'),
    AssignmentRule('Qh', 'QC*FQh', 'l_per_min', name='hepatic (venous side) blood flow'),
    AssignmentRule('Qha', 'Qh - Qgu - Qsp - Qpa', 'l_per_min', name='hepatic artery blood flow'),
    AssignmentRule('Qlu', 'QC*FQlu', 'l_per_min', name='lung blood flow'),
    AssignmentRule('Qsp', 'QC*FQsp', 'l_per_min', name='spleen blood flow'),
    AssignmentRule('Qpa', 'QC*FQpa', 'l_per_min', name='pancreas blood flow'),
    AssignmentRule('Qre', 'QC*FQre', 'l_per_min', name='rest of body blood flow'),
]

# Volumes for explicit tissue models
for c_id in COMPARTMENTS_BODY.keys():
    if c_id not in ['ve', 'ar']:
        rules.extend([
            AssignmentRule(f'V{c_id}_tissue', value=f'V{c_id}*(1 dimensionless - Fblood)', unit=UNIT_KIND_LITRE),
            AssignmentRule(f'V{c_id}_blood', value=f'V{c_id}*Fblood', unit=UNIT_KIND_LITRE),
        ])

for s_id, s_dict in SUBSTANCES_BODY.items():
    s_name = s_dict['name']

    # free concentrations & clearance
    rules.extend([
        AssignmentRule(f'Cpl_ve_{s_id}', f'Cve_{s_id}/BP_{s_id}', 'mM',
                       name=f'{s_name} venous plasma concentration'),

        # FIXME: check plasma binding
        #AssignmentRule('Cli_free_{}'.format(s_id),
        #                  'Cli_{}*fup_{}'.format(s_id, s_id), 'mM',
        #                  name='{} free liver concentration'.format(s_name)),

        # AssignmentRule(f'Cki_free_{s_id}', f'Cki_{s_id}*fup_{s_id}', 'mM',
        #               name=f'{s_name} free kidney concentration'),
    ])

    # injection
    rules.extend([
        AssignmentRule(f'Ki_{s_id}', f'1.386 dimensionless/ti_{s_id} * 3600 s_per_hr', 'mg_per_hr'),  # 2*ln2
    ])

    # ---------------------------------
    # X Amount [mg], C Concentration
    # ---------------------------------
    for c_id, c_name in COMPARTMENTS_BODY.items():
        if c_id not in ["ve", "ar"]:
            rules.extend([
                AssignmentRule(f'C{c_id}_blood_{s_id}',
                                  f'A{c_id}_blood_{s_id}/V{c_id}_blood',
                                  'mM', name=f'{s_name} concentration ({c_name})'),
                AssignmentRule(f'X{c_id}_blood_{s_id}',
                                  f'A{c_id}_blood_{s_id}*Mr_{s_id}',
                                  f'mg', name='{s_name} amount ({c_name})'),
                AssignmentRule(f'M{c_id}_blood_{s_id}',
                                  f'A{c_id}_blood_{s_id}/V{c_id}_blood*Mr_{s_id}',
                                  'mg_per_l', name=f'{s_name} amount ({c_name})')
            ])
        else:
            rules.extend([
                AssignmentRule(f'C{c_id}_{s_id}',
                               f'A{c_id}_{s_id}/V{c_id}',
                               'mM', name=f'{s_name} concentration ({c_name})'),
                AssignmentRule(f'X{c_id}_{s_id}',
                               f'A{c_id}_{s_id}*Mr_{s_id}',
                               f'mg', name='{s_name} amount ({c_name})'),
                AssignmentRule(f'M{c_id}_{s_id}',
                               f'A{c_id}_{s_id}/V{c_id}*Mr_{s_id}',
                               'mg_per_l', name=f'{s_name} amount ({c_name})')
            ])

    # urine metabolites
    c_id, c_name = ("urine", "urine")
    rules.append(
        AssignmentRule(f'X{c_id}_{s_id}',
                          f'A{c_id}_{s_id}*Mr_{s_id}',
                          'mg', name=f'{s_name} amount ({c_name})'),
    )


# --------------------------------------------------------------------------------------------------
# Reactions
# --------------------------------------------------------------------------------------------------
reactions = []

for s_id, s_dict in SUBSTANCES_BODY.items():
    s_name = s_dict['name']
    reactions.extend([
        # --------------------
        # injection
        # --------------------
        # Injection venous (I.V. dose)
        Reaction(sid=f"injection_{s_id}",
                         name=f"injection {s_name}",
                         formula=(f"Ki_{s_id}*IVDOSE_{s_id}/Mr_{s_id}", 'mmole_per_min'),
                         equation=f"-> Ave_{s_id}",
                         compartment='Vve'),
        Reaction(sid=f"infusion_{s_id}",
                         name=f"infusion {s_name}",
                         formula=(f"Ri_{s_id}/Mr_{s_id}", 'mmole_per_min'),
                         equation=f"-> Ave_{s_id}",
                         compartment='Vve'),

        # ---------------------------
        # absorption (oral dose gut)
        # ---------------------------
        Reaction(sid=f"absorption_{s_id}",
                 name=f"absorption {s_name}",
                 formula=(f"Ka_{s_id}/60 min_per_hr*PODOSE_{s_id}/Mr_{s_id}*F_{s_id}", 'mmole_per_min'),
                         equation=f"-> Agu_blood_{s_id}",
                         compartment='Vgu'),
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


            # distribution in blood volume
            reactions.extend([
                Reaction(sid=rid_in, name=name_in,
                             formula=(f"Q{c_id}*Cve_{s_id}", 'mmole_per_min'),
                             equation=f'Ave_{s_id} -> A{c_id}_blood_{s_id}'),
                Reaction(sid=rid_out, name=name_out,
                             formula=(f"Q{c_id}*C{c_id}_blood_{s_id}*BP_{s_id}", 'mmole_per_min'),
                             equation=f'A{c_id}_blood_{s_id} -> Aar_{s_id}'),
            ])
        # --------------------
        # ar -> organ -> ve
        # --------------------
        if c_id in ['ki', 're']:
            rid_in = f"Flow_ar_{c_id}_{s_id}"
            name_in = f"inflow {c_name} {s_name}"
            rid_out = f"Flow_{c_id}_ve_{s_id}"
            name_out = f"outflow {c_name} {s_name}"

            # only distribution in blood volume
            reactions.extend([
                Reaction(sid=rid_in, name=name_in,
                         formula=(f"Q{c_id}*Car_{s_id}", 'mmole_per_min'),
                         equation=f'Aar_{s_id} -> A{c_id}_blood_{s_id}'),
                Reaction(sid=rid_out, name=name_out,
                         formula=(f"Q{c_id}*C{c_id}_blood_{s_id}*BP_{s_id}", 'mmole_per_min'),
                         equation=f'A{c_id}_blood_{s_id} -> Ave_{s_id}'),
            ])
        # --------------------
        # ar -> organ -> li
        # --------------------
        if c_id in ['gu', 'sp', 'pa']:
            rid_in = f'Flow_ar_{c_id}_{s_id}'
            name_in = f'inflow {c_name} {s_name}'
            rid_out = f'Flow_{c_id}_li_{s_id}'
            name_out = f'outflow {c_name} {s_name}'

            reactions.extend([
                # only distribution in blood volume
                Reaction(sid=rid_in, name=name_in,
                         formula=(f'Q{c_id}*Car_{s_id}', 'mmole_per_min'),
                         equation=f'Aar_{s_id} -> A{c_id}_blood_{s_id}'),
                Reaction(sid=rid_out, name=name_out,
                         formula=(f'Q{c_id}*C{c_id}_blood_{s_id}*BP_{s_id}', 'mmole_per_min'),
                         equation=f'A{c_id}_blood_{s_id} -> Ali_blood_{s_id}'),
            ])
        # --------------------
        # ar -> li -> ve
        # --------------------
        if c_id == "li":
            # liver

            reactions.extend([
                Reaction(sid=f"Flow_ar_li_{s_id}",
                         name=f"inflow liver {s_name}",
                         formula=(f"Qha*Car_{s_id}", 'mmole_per_min'),
                         equation=f'Aar_{s_id} -> Ali_blood_{s_id}'),
                Reaction(sid=f"Flow_li_ve_{s_id}",
                         name=f"outflow liver {s_name}",
                         formula=(f"Qh*Cli_blood_{s_id}*BP_{s_id}", 'mmole_per_min'),
                         equation=f'Ali_blood_{s_id} -> Ave_{s_id}'),
            ])

rules.extend([
    # liver balance
    AssignmentRule(f'inflow_li_{s_id}',
                   f'Flow_gu_li_{s_id} + Flow_sp_li_{s_id} + Flow_pa_li_{s_id} + Flow_ar_li_{s_id}',
                   'mmole_per_min'),
    AssignmentRule(f'outflow_li_{s_id}',
                   f'Flow_li_ve_{s_id}', 'mmole_per_min'),
])

# --------------------------------------------------------------------------------------------------
# RateRules
# --------------------------------------------------------------------------------------------------
rate_rules = []

for s_id, s_dict in SUBSTANCES_BODY.items():
    rate_rules.extend([

        # absorption of dose
        RateRule(f'PODOSE_{s_id}', f'-absorption_{s_id}*Mr_{s_id}', 'mg_per_min'),
        # injection of dose
        RateRule(f'IVDOSE_{s_id}', f'-injection_{s_id}*Mr_{s_id}', 'mg_per_min'),

        # cumulative infusion dose
        RateRule(f'cum_dose_{s_id}', f'Ri_{s_id}', 'mg_per_min'),
    ])

def create_model(target_dir):
    return creator.create_model(
        modules=['model_body'],
        target_dir=target_dir,
        create_report=True
    )


if __name__ == "__main__":
    create_model("./models")
