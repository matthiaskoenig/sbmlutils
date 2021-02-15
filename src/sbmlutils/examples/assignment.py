"""AssignmentRule and InitialAssignment example."""
from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.units import *


mid = "assignment_example"
creators = templates.creators
notes = Notes(
    [
        """<p>Example model for testing InitialAssignments in roadrunner.</p>""",
        templates.terms_of_use,
    ]
)
model_units = ModelUnits(
    time=UNIT_hr,
    extent=UNIT_mg,
    substance=UNIT_mg,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
units = [
    UNIT_kg,
    UNIT_hr,
    UNIT_mg,
    UNIT_m,
    UNIT_m2,
    Unit("per_h", [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    Unit(
        "mg_per_litre",
        [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_LITRE, -1.0, 0, 1.0)],
    ),
    Unit("mg_per_g", [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_GRAM, -1.0, 0, 1.0)]),
    Unit(
        "mg_per_h", [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)]
    ),
    Unit(
        "litre_per_h",
        [(UNIT_KIND_LITRE, 1.0, 0, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)],
    ),
    Unit(
        "litre_per_kg", [(UNIT_KIND_LITRE, 1.0, 0, 1.0), (UNIT_KIND_GRAM, -1.0, 3, 1.0)]
    ),
    Unit(
        "mulitre_per_min_mg",
        [
            (UNIT_KIND_LITRE, 1.0, -6, 1.0),
            (UNIT_KIND_SECOND, -1.0, 0, 60),
            (UNIT_KIND_GRAM, -1.0, -3, 1.0),
        ],
    ),
    Unit("ml_per_s", [(UNIT_KIND_LITRE, 1.0, -3, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 1)]),
    # conversion factors
    Unit(
        "s_per_h", [(UNIT_KIND_SECOND, 1.0, 0, 1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)]
    ),
    Unit(
        "min_per_h", [(UNIT_KIND_SECOND, 1.0, 0, 60), (UNIT_KIND_SECOND, -1.0, 0, 3600)]
    ),
    Unit(
        "ml_per_litre", [(UNIT_KIND_LITRE, 1.0, -3, 1.0), (UNIT_KIND_LITRE, -1.0, 0, 1)]
    ),
    Unit(
        "mulitre_per_g", [(UNIT_KIND_LITRE, 1.0, -6, 1.0), (UNIT_KIND_GRAM, -1.0, 0, 1)]
    ),
]

parameters = [
    # dosing
    Parameter("Ave", 0, "mg", constant=False),
    Parameter("D", 0, "mg", constant=False),
    Parameter("IVDOSE", 0, "mg", constant=True),
    Parameter("PODOSE", 100, "mg", constant=True),
    Parameter("k1", 0.1, "litre_per_h", constant=True),
    # whole body data
    Parameter("BW", 70, "kg", True),
    Parameter("FVve", 0.0514, "litre_per_kg", True),
]

assignments = [
    InitialAssignment("Ave", "IVDOSE", "mg"),
    InitialAssignment("D", "PODOSE", "mg"),
]

rules = [
    # concentrations
    AssignmentRule("Cve", "Ave/Vve", "mg_per_litre"),
    # volumes
    AssignmentRule("Vve", "BW*FVve", UNIT_KIND_LITRE),
]

rate_rules = [
    RateRule("Ave", "- k1*Cve", "mg_per_h"),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.assignment"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
