# -*- coding=utf-8 -*-
"""
FBA example
"""
import libsbml
from libsbml import UNIT_KIND_MOLE, UNIT_KIND_SECOND, \
    UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_GRAM, UNIT_KIND_LITRE

import sbmlutils.factory as mc
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator.processes.reaction import ReactionTemplate, ExchangeReactionTemplate

# -----------------------------------------------------------------------------
mid = 'fbc_inf_bounds'
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
parameters.extend([
    # bounds
    mc.Parameter(sid="zero", name="zero bound", value=0.0, unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid="ub_inf", name="default upper bound",
                 value=float("Inf"), unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid="lb_inf", name="default lower bound",
                 value=-float("Inf"), unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid="ub_1000", name="upper bound 1000",
                 value=1000, unit=UNIT_FLUX,
                 constant=True, sboTerm=mc.SBO_FLUX_BOUND),
    mc.Parameter(sid="lb_1000", name="lower bound -1000",
                 value=-1000, unit=UNIT_FLUX,
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
        compartment='bioreactor',
    ),
    ReactionTemplate(
        rid='v2',
        name='v2 (9.46 Glcxt + 12.92 O2 -> X)',
        equation='9.46 Glcxt + 12.92 O2 => X []',
        compartment='bioreactor'
    ),
    ReactionTemplate(
        rid='v3',
        name='v3 (9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X)',
        equation='9.84 Glcxt + 12.73 O2 => 1.24 Ac + X []',
        compartment='bioreactor'
    ),
    ReactionTemplate(
        rid='v4',
        name='v4 (19.23 Glcxt -> 12.12 Ac + X)',
        equation='19.23 Glcxt => 12.12 Ac + X []',
        compartment='bioreactor'
    ),
])

for rt in reactions:
    if rt.rid in ["v1", "v2", "v3", "v4"]:
        rt.lowerFluxBound = "zero"
        rt.upperFluxBound = "ub_inf"

"""
# exchange reactions

# reactions: exchange reactions (this species can be changed by the FBA)
for sid in ['Ac', 'Glcxt', 'O2', 'X']:
    builder.create_exchange_reaction(model, species_id=sid,
                                     flux_unit=UNIT_FLUX_PER_G,
                                     exchange_type=builder.EXCHANGE)
# set bounds for the exchange reactions
p_lb_O2 = model.getParameter("lb_EX_O2")
p_lb_O2.setValue(
    -15.0)  # FIXME: this is in mmol/gdw/h (biomass weighting of FBA)
p_lb_Glcxt = model.getParameter("lb_EX_Glcxt")
p_lb_Glcxt.setValue(-10.0)  # FIXME: this is in mmol/gdw/h

# objective function
model_fba = model.getPlugin(builder.SBML_FBC_NAME)
mc.create_objective(model_fba, oid="biomass_max", otype="maximize",
                    fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0})
"""