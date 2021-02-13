"""Demo kinetic network."""
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.units import *


mid = "Koenig_demo"
packages = ["fbc"]
version = 14
notes = Notes(
    [
        """
    <h1>Koenig Demo Metabolism</h1>
    <h2>Description</h2>
    <p>This is a demonstration model in
    <a href="http://sbmlutils.org" target="_blank" title="Access the definition of the SBML file format.">
    SBML</a>&#160;format.
    </p>
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators

model_units = ModelUnits(
    time=UNIT_KIND_SECOND,
    substance=UNIT_KIND_MOLE,
    extent=UNIT_KIND_MOLE,
    length=UNIT_KIND_METRE,
    area=UNIT_m2,
    volume=UNIT_m3,
)
units = [
    Unit("s", [(UNIT_KIND_SECOND, 1.0)]),
    Unit("kg", [(UNIT_KIND_KILOGRAM, 1.0)]),
    Unit("m", [(UNIT_KIND_METRE, 1.0)]),
    Unit("m2", [(UNIT_KIND_METRE, 2.0)]),
    Unit("m3", [(UNIT_KIND_METRE, 3.0)]),
    Unit("mM", [(UNIT_KIND_MOLE, 1.0, 0), (UNIT_KIND_METRE, -3.0)]),
    Unit("mole_per_s", [(UNIT_KIND_MOLE, 1.0), (UNIT_KIND_SECOND, -1.0)]),
]

compartments = [
    Compartment(
        sid="e", value=1e-06, unit="m3", constant=False, name="external compartment"
    ),
    Compartment(
        sid="c", value=1e-06, unit="m3", constant=False, name="cell compartment"
    ),
    Compartment(
        sid="m",
        value=1,
        unit="m2",
        constant=False,
        spatialDimensions=2,
        name="plasma membrane",
    ),
]

species = [
    Species(
        sid="c__A",
        compartment="c",
        initialConcentration=0.0,
        substanceUnit=UNIT_KIND_MOLE,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="A",
    ),
    Species(
        sid="c__B",
        compartment="c",
        initialConcentration=0.0,
        substanceUnit=UNIT_KIND_MOLE,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="B",
    ),
    Species(
        sid="c__C",
        compartment="c",
        initialConcentration=0.0,
        substanceUnit=UNIT_KIND_MOLE,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="C",
    ),
    Species(
        sid="e__A",
        compartment="e",
        initialConcentration=0.0,
        substanceUnit=UNIT_KIND_MOLE,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="A",
    ),
    Species(
        sid="e__B",
        compartment="e",
        initialConcentration=0.0,
        substanceUnit=UNIT_KIND_MOLE,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="B",
    ),
    Species(
        sid="e__C",
        compartment="e",
        initialConcentration=0.0,
        substanceUnit=UNIT_KIND_MOLE,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="C",
    ),
]

parameters = [
    Parameter(
        "scale_f", value=1e-6, unit="-", constant=True, name="metabolic scaling factor"
    ),
    Parameter("Vmax_bA", 5.0, "mole_per_s", True),
    Parameter("Km_A", 1.0, "mM", True),
    Parameter("Vmax_bB", 2.0, "mole_per_s", True),
    Parameter("Km_B", 0.5, "mM", True),
    Parameter("Vmax_bC", 2.0, "mole_per_s", True),
    Parameter("Km_C", 3.0, "mM", True),
    Parameter("Vmax_v1", 1.0, "mole_per_s", True),
    Parameter("Keq_v1", 10.0, "-", True),
    Parameter("Vmax_v2", 0.5, "mole_per_s", True),
    Parameter("Vmax_v3", 0.5, "mole_per_s", True),
    Parameter("Vmax_v4", 0.5, "mole_per_s", True),
    Parameter("Keq_v4", 2.0, "-", True),
]

reactions = [
    Reaction(
        sid="bA",
        name="bA (A import)",
        equation="e__A => c__A []",
        compartment="m",
        pars=[],
        rules=[],
        formula=(
            "scale_f*(Vmax_bA/Km_A)*(e__A - c__A)/ (1 dimensionless + e__A/Km_A + c__A/Km_A)",
            "mole_per_s",
        ),
    ),
    Reaction(
        sid="bB",
        name="bB (B export)",
        equation="c__B => e__B []",
        compartment="m",
        pars=[],
        rules=[],
        formula=(
            "(scale_f*(Vmax_bB/Km_B)*(c__B - e__B))/(1 dimensionless + e__B/Km_B + c__B/Km_B)",
            "mole_per_s",
        ),
    ),
    Reaction(
        sid="bC",
        name="bC (C export)",
        equation="c__C => e__C []",
        compartment="m",
        pars=[],
        rules=[],
        formula=(
            "(scale_f*(Vmax_bC/Km_C)*(c__C - e__C))/(1 dimensionless + e__C/Km_C + c__C/Km_C)",
            "mole_per_s",
        ),
    ),
    Reaction(
        sid="v1",
        name="v1 (A -> B)",
        equation="c__A -> c__B []",
        compartment="c",
        formula=(
            "(scale_f*Vmax_v1)/Km_A*(c__A - 1 dimensionless/Keq_v1*c__B)",
            "mole_per_s",
        ),
    ),
    Reaction(
        sid="v2",
        name="v2 (A -> C)",
        equation="c__A -> c__C []",
        compartment="c",
        formula=("(scale_f*Vmax_v2)/Km_A*c__A", "mole_per_s"),
    ),
    Reaction(
        sid="v3",
        name="v3 (C -> A)",
        equation="c__C -> c__A []",
        compartment="c",
        formula=("(scale_f*Vmax_v3)/Km_A*c__C", "mole_per_s"),
    ),
    Reaction(
        sid="v4",
        name="v4 (C -> B)",
        equation="c__C -> c__B []",
        compartment="c",
        formula=(
            "(scale_f*Vmax_v4)/Km_A*(c__C - 1 dimensionless/Keq_v4*c__B)",
            "mole_per_s",
        ),
    ),
]
