# -*- coding=utf-8 -*-
"""
FBA example with exchange reactions.
"""
import libsbml
from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, \
    UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_GRAM, UNIT_KIND_LITRE

import sbmlutils.factory as mc
from sbmlutils.fbc import Objective
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator.processes.reaction import ReactionTemplate, ExchangeReactionTemplate, EXCHANGE, EXCHANGE_IMPORT, EXCHANGE_EXPORT

# -----------------------------------------------------------------------------
mid = 'fbc_ex1'
version = 1
creators = templates.creators
main_units = {
    'time': 's',
    'extent': UNIT_KIND_MOLE,
    'substance': UNIT_KIND_MOLE,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}
units = list()
compartments = list()
species = list()
parameters = list()
assignments = list()
rules = list()
reactions = list()
events = None

# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------
UNIT_AMOUNT = 'mmol'
UNIT_AREA = 'm2'
UNIT_VOLUME = 'l'
UNIT_TIME = 'h'
UNIT_CONCENTRATION = 'mmol_per_l'
UNIT_FLUX = 'mmol_per_h'

main_units = {
    'time': UNIT_TIME,
    'extent': UNIT_AMOUNT,
    'substance': UNIT_AMOUNT,
    'length': 'm',
    'area': UNIT_AREA,
    'volume': UNIT_VOLUME,
}

units = [
    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)], name='hour'),
    mc.Unit('g', [(UNIT_KIND_GRAM, 1.0)], name="gram"),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)], name="meter"),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)], name="cubic meter"),
    mc.Unit('l', [(UNIT_KIND_LITRE, 1.0)], name="liter"),
    mc.Unit('mmol', [(UNIT_KIND_MOLE, 1.0, -3, 1.0)]),
    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_h', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                           (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mmol_per_hg', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_GRAM, -1.0)]),

    mc.Unit('mmol_per_l', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                           (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('mmol_per_lg', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                           (UNIT_KIND_LITRE, -1.0), (UNIT_KIND_GRAM, -1.0)]),

    mc.Unit('l_per_mmol', [(UNIT_KIND_LITRE, 1.0),
                           (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
    mc.Unit('g_per_l', [(UNIT_KIND_GRAM, 1.0),
                        (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('g_per_mmol', [(UNIT_KIND_GRAM, 1.0),
                           (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
]
# -----------------------------------------------------------------------------
# Compartments
# -----------------------------------------------------------------------------
compartments.extend([
    mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True,
                   name='bioreactor', spatialDimensions=3),
])
# -----------------------------------------------------------------------------
# Species
# -----------------------------------------------------------------------------
species.extend([
    mc.Species(sid='Glcxt', name="glucose", initialConcentration=0.0,
               substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
               compartment="bioreactor"),
    mc.Species(sid='Ac', name="acetate", initialConcentration=0.0,
               substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
               compartment="bioreactor"),
    mc.Species(sid='O2', name="oxygen", initialConcentration=0.0,
               substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
               compartment="bioreactor"),
    mc.Species(sid='X', name="biomass", initialConcentration=0.0,
               substanceUnit=UNIT_AMOUNT, hasOnlySubstanceUnits=False,
               compartment="bioreactor"),
])
# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
FLUX_BOUND_ZERO = "zero"
FLUX_BOUND_PLUS_INF = "ub_inf"
FLUX_BOUND_MINUS_INF = "lb_inf"

FLUX_BOUND_GLC_IMPORT = "glc_import"
FLUX_BOUND_O2_IMPORT = "o2_import"

parameters.extend([
    # bounds
    mc.Parameter(sid=FLUX_BOUND_ZERO, name="zero bound", value=0.0, unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid=FLUX_BOUND_PLUS_INF, name="default upper bound",
                 value=float("Inf"), unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid=FLUX_BOUND_MINUS_INF, name="default lower bound",
                 value=-float("Inf"), unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid=FLUX_BOUND_GLC_IMPORT, name="glc import bound",
                 value=-15, unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid=FLUX_BOUND_O2_IMPORT, name="o2 import bound",
                 value=-10, unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
])

# -----------------------------------------------------------------------------
# Reactions
# -----------------------------------------------------------------------------
# metabolic reactions
reactions.extend([
    ReactionTemplate(
        rid='v1',
        name='v1 (39.43 Ac + 35 O2 -> X)',
        equation='39.43 Ac + 35 O2 => X []',
    ),
    ReactionTemplate(
        rid='v2',
        name='v2 (9.46 Glcxt + 12.92 O2 -> X)',
        equation='9.46 Glcxt + 12.92 O2 => X []',
    ),
    ReactionTemplate(
        rid='v3',
        name='v3 (9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X)',
        equation='9.84 Glcxt + 12.73 O2 => 1.24 Ac + X []',
    ),
    ReactionTemplate(
        rid='v4',
        name='v4 (19.23 Glcxt -> 12.12 Ac + X)',
        equation='19.23 Glcxt => 12.12 Ac + X []',
    ),
])

for rt in reactions:
    if rt.rid in ["v1", "v2", "v3", "v4"]:
        rt.compartment = "bioreactor"
        rt.lowerFluxBound = FLUX_BOUND_ZERO
        rt.upperFluxBound = FLUX_BOUND_PLUS_INF
        rt.flux_unit = UNIT_FLUX

# exchange reactions
reactions.extend([
    ExchangeReactionTemplate(species_id="Ac",
                             flux_unit=UNIT_FLUX,
                             exchange_type=EXCHANGE,
                             lowerFluxBound=FLUX_BOUND_MINUS_INF,
                             upperFluxBound=FLUX_BOUND_PLUS_INF),
    ExchangeReactionTemplate(species_id="O2",
                             flux_unit=UNIT_FLUX,
                             exchange_type=EXCHANGE_IMPORT,
                             lowerFluxBound=FLUX_BOUND_O2_IMPORT,
                             upperFluxBound=FLUX_BOUND_ZERO),
    ExchangeReactionTemplate(species_id="Glcxt",
                             flux_unit=UNIT_FLUX,
                             exchange_type=EXCHANGE_IMPORT,
                             lowerFluxBound=FLUX_BOUND_GLC_IMPORT,
                             upperFluxBound=FLUX_BOUND_ZERO),
    ExchangeReactionTemplate(species_id="X",
                             flux_unit=UNIT_FLUX,
                             exchange_type=EXCHANGE,
                             lowerFluxBound=FLUX_BOUND_MINUS_INF,
                             upperFluxBound=FLUX_BOUND_PLUS_INF),
])


# -----------------------------------------------------------------------------
# Objective function
# -----------------------------------------------------------------------------
objectives = [
    Objective(sid="biomass_max", objectiveType="maximize", active=True,
              fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0})
]

