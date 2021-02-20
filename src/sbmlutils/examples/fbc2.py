"""FBA example with exchange reactions & boundaryCondition=True."""
from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


# -----------------------------------------------------------------------------
mid = "fbc_example2"
packages = ["fbc"]
creators = templates.creators
notes = Notes(
    [
        """
    <h1>sbmlutils {}</h1>
    <h2>Description</h2>
    <p>Example creating fbc model.</p>
    """,
        templates.terms_of_use,
    ]
)


# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------
UNIT_AMOUNT = "mmol"
UNIT_AREA = "m2"
UNIT_VOLUME = "l"
UNIT_TIME = UNIT_hr
UNIT_CONCENTRATION = "mmol_per_l"
UNIT_FLUX = "mmol_per_h"


model_units = ModelUnits(
    time=UNIT_hr,
    extent=UNIT_AMOUNT,
    substance=UNIT_AMOUNT,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_VOLUME,
)

units = [
    Unit("hr", [(UNIT_KIND_SECOND, 1.0, 0, 3600)], name="hour"),
    Unit("g", [(UNIT_KIND_GRAM, 1.0)], name="gram"),
    Unit("m", [(UNIT_KIND_METRE, 1.0)], name="meter"),
    Unit("m2", [(UNIT_KIND_METRE, 2.0)], name="cubic meter"),
    Unit("l", [(UNIT_KIND_LITRE, 1.0)], name="liter"),
    Unit("mmol", [(UNIT_KIND_MOLE, 1.0, -3, 1.0)]),
    Unit("per_h", [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    Unit(
        "mmol_per_h",
        [(UNIT_KIND_MOLE, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)],
    ),
    Unit(
        "mmol_per_hg",
        [
            (UNIT_KIND_MOLE, 1.0, -3, 1.0),
            (UNIT_KIND_SECOND, -1.0, 0, 3600),
            (UNIT_KIND_GRAM, -1.0),
        ],
    ),
    Unit("mmol_per_l", [(UNIT_KIND_MOLE, 1.0, -3, 1.0), (UNIT_KIND_LITRE, -1.0)]),
    Unit(
        "mmol_per_lg",
        [
            (UNIT_KIND_MOLE, 1.0, -3, 1.0),
            (UNIT_KIND_LITRE, -1.0),
            (UNIT_KIND_GRAM, -1.0),
        ],
    ),
    Unit("l_per_mmol", [(UNIT_KIND_LITRE, 1.0), (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
    Unit("g_per_l", [(UNIT_KIND_GRAM, 1.0), (UNIT_KIND_LITRE, -1.0)]),
    Unit("g_per_mmol", [(UNIT_KIND_GRAM, 1.0), (UNIT_KIND_MOLE, -1.0, -3, 1.0)]),
]
# -----------------------------------------------------------------------------
# Compartments
# -----------------------------------------------------------------------------
compartments = [
    Compartment(
        sid="bioreactor",
        value=1.0,
        unit=UNIT_VOLUME,
        constant=True,
        name="bioreactor",
        spatialDimensions=3,
    ),
]
# -----------------------------------------------------------------------------
# Species
# -----------------------------------------------------------------------------
species = [
    Species(
        sid="Glcxt",
        name="glucose",
        initialConcentration=0.0,
        substanceUnit=UNIT_AMOUNT,
        hasOnlySubstanceUnits=False,
        compartment="bioreactor",
    ),
    Species(
        sid="Ac",
        name="acetate",
        initialConcentration=0.0,
        substanceUnit=UNIT_AMOUNT,
        hasOnlySubstanceUnits=False,
        compartment="bioreactor",
        boundaryCondition=True,
    ),
    Species(
        sid="O2",
        name="oxygen",
        initialConcentration=0.0,
        substanceUnit=UNIT_AMOUNT,
        hasOnlySubstanceUnits=False,
        compartment="bioreactor",
    ),
    Species(
        sid="X",
        name="biomass",
        initialConcentration=0.0,
        substanceUnit=UNIT_AMOUNT,
        hasOnlySubstanceUnits=False,
        compartment="bioreactor",
        boundaryCondition=True,
    ),
]
# -----------------------------------------------------------------------------
# Parameters
# -----------------------------------------------------------------------------
FLUX_BOUND_ZERO = "zero"
FLUX_BOUND_PLUS_INF = "ub_inf"
FLUX_BOUND_PLUS_1000 = "ub_1000"
FLUX_BOUND_MINUS_INF = "lb_inf"
FLUX_BOUND_MINUS_1000 = "lb_1000"

FLUX_BOUND_GLC_IMPORT = "glc_import"
FLUX_BOUND_O2_IMPORT = "o2_import"

parameters = [
    # bounds
    Parameter(
        sid=FLUX_BOUND_ZERO,
        name="zero bound",
        value=0.0,
        unit=UNIT_FLUX,
        constant=True,
        sboTerm=SBO_FLUX_BOUND,
    ),
    Parameter(
        sid=FLUX_BOUND_PLUS_INF,
        name="default upper bound",
        value=float("Inf"),
        unit=UNIT_FLUX,
        constant=True,
        sboTerm=SBO_FLUX_BOUND,
    ),
    Parameter(
        sid=FLUX_BOUND_MINUS_INF,
        name="default lower bound",
        value=-float("Inf"),
        unit=UNIT_FLUX,
        constant=True,
        sboTerm=SBO_FLUX_BOUND,
    ),
    Parameter(
        sid=FLUX_BOUND_GLC_IMPORT,
        name="glc import bound",
        value=-15,
        unit=UNIT_FLUX,
        constant=True,
        sboTerm=SBO_FLUX_BOUND,
    ),
    Parameter(
        sid=FLUX_BOUND_O2_IMPORT,
        name="o2 import bound",
        value=-10,
        unit=UNIT_FLUX,
        constant=True,
        sboTerm=SBO_FLUX_BOUND,
    ),
]

# -----------------------------------------------------------------------------
# Reactions
# -----------------------------------------------------------------------------
# metabolic reactions
reactions = [
    Reaction(
        sid="v1",
        name="v1 (39.43 Ac + 35 O2 -> X)",
        equation="39.43 Ac + 35 O2 => X []",
    ),
    Reaction(
        sid="v2",
        name="v2 (9.46 Glcxt + 12.92 O2 -> X)",
        equation="9.46 Glcxt + 12.92 O2 => X []",
    ),
    Reaction(
        sid="v3",
        name="v3 (9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X)",
        equation="9.84 Glcxt + 12.73 O2 => 1.24 Ac + X []",
    ),
    Reaction(
        sid="v4",
        name="v4 (19.23 Glcxt -> 12.12 Ac + X)",
        equation="19.23 Glcxt => 12.12 Ac + X []",
    ),
]

for rt in reactions:
    if rt.sid in ["v1", "v2", "v3", "v4"]:
        rt.compartment = "bioreactor"
        rt.lowerFluxBound = FLUX_BOUND_ZERO
        rt.upperFluxBound = FLUX_BOUND_PLUS_INF

# exchange reactions
reactions.extend(
    [
        ExchangeReaction(
            species_id="Glcxt",
            lowerFluxBound=FLUX_BOUND_GLC_IMPORT,
            upperFluxBound=FLUX_BOUND_ZERO,
        ),
        ExchangeReaction(
            species_id="O2",
            lowerFluxBound=FLUX_BOUND_O2_IMPORT,
            upperFluxBound=FLUX_BOUND_ZERO,
        ),
    ]
)


# -----------------------------------------------------------------------------
# Objective function
# -----------------------------------------------------------------------------
objectives = [
    Objective(
        sid="biomass_max",
        objectiveType="maximize",
        active=True,
        fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0},
    )
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.fbc2"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
