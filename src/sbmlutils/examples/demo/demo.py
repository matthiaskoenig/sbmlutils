"""Demo kinetic network."""
from pathlib import Path

from sbmlutils.examples import templates
from sbmlutils.factory import *


class U(Units):
    """UnitsDefinition."""

    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")
    mM = UnitDefinition("mM", "mmole/liter")
    mole_per_s = UnitDefinition("mole_per_s", "mole/s")


model = Model(
    "Koenig_demo_v15",
    packages=[Package.FBC_V2],
    notes="""
    # Koenig Demo Metabolism
    ## Description
    This is a demonstration model in
    <a href="http://sbmlutils.org" target="_blank" title="Access the definition of the SBML file format.">
    SBML</a> format.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    units=U,
    model_units=ModelUnits(
        time=U.second,
        substance=U.mole,
        extent=U.mole,
        length=U.meter,
        area=U.m2,
        volume=U.m3,
    ),
)
model.compartments = [
    Compartment(
        sid="e", value=1e-06, unit=U.m3, constant=False, name="external compartment"
    ),
    Compartment(
        sid="c", value=1e-06, unit=U.m3, constant=False, name="cell compartment"
    ),
    Compartment(
        sid="m",
        value=1,
        unit=U.m2,
        constant=False,
        spatialDimensions=2,
        name="plasma membrane",
    ),
]

model.species = [
    Species(
        sid="c__A",
        compartment="c",
        initialConcentration=0.0,
        substanceUnit=U.mole,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="A",
    ),
    Species(
        sid="c__B",
        compartment="c",
        initialConcentration=0.0,
        substanceUnit=U.mole,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="B",
    ),
    Species(
        sid="c__C",
        compartment="c",
        initialConcentration=0.0,
        substanceUnit=U.mole,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="C",
    ),
    Species(
        sid="e__A",
        compartment="e",
        initialConcentration=0.0,
        substanceUnit=U.mole,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="A",
    ),
    Species(
        sid="e__B",
        compartment="e",
        initialConcentration=0.0,
        substanceUnit=U.mole,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="B",
    ),
    Species(
        sid="e__C",
        compartment="e",
        initialConcentration=0.0,
        substanceUnit=U.mole,
        hasOnlySubstanceUnits=False,
        boundaryCondition=False,
        name="C",
    ),
]

model.parameters = [
    Parameter(
        "scale_f",
        value=1e-6,
        unit=U.dimensionless,
        constant=True,
        name="metabolic scaling factor",
    ),
    Parameter("Vmax_bA", 5.0, U.mole_per_s, True),
    Parameter("Km_A", 1.0, U.mM, True),
    Parameter("Vmax_bB", 2.0, U.mole_per_s, True),
    Parameter("Km_B", 0.5, U.mM, True),
    Parameter("Vmax_bC", 2.0, U.mole_per_s, True),
    Parameter("Km_C", 3.0, U.mM, True),
    Parameter("Vmax_v1", 1.0, U.mole_per_s, True),
    Parameter("Keq_v1", 10.0, U.dimensionless, True),
    Parameter("Vmax_v2", 0.5, U.mole_per_s, True),
    Parameter("Vmax_v3", 0.5, U.mole_per_s, True),
    Parameter("Vmax_v4", 0.5, U.mole_per_s, True),
    Parameter("Keq_v4", 2.0, U.dimensionless, True),
]

model.reactions = [
    Reaction(
        sid="bA",
        name="bA (A import)",
        equation="e__A => c__A []",
        compartment="m",
        pars=[],
        rules=[],
        formula=(
            "scale_f*(Vmax_bA/Km_A)*(e__A - c__A)/ (1 dimensionless + e__A/Km_A + c__A/Km_A)",
            U.mole_per_s,
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
            U.mole_per_s,
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
            U.mole_per_s,
        ),
    ),
    Reaction(
        sid="v1",
        name="v1 (A -> B)",
        equation="c__A -> c__B []",
        compartment="c",
        formula=(
            "(scale_f*Vmax_v1)/Km_A*(c__A - 1 dimensionless/Keq_v1*c__B)",
            U.mole_per_s,
        ),
    ),
    Reaction(
        sid="v2",
        name="v2 (A -> C)",
        equation="c__A -> c__C []",
        compartment="c",
        formula=("(scale_f*Vmax_v2)/Km_A*c__A", U.mole_per_s),
    ),
    Reaction(
        sid="v3",
        name="v3 (C -> A)",
        equation="c__C -> c__A []",
        compartment="c",
        formula=("(scale_f*Vmax_v3)/Km_A*c__C", U.mole_per_s),
    ),
    Reaction(
        sid="v4",
        name="v4 (C -> B)",
        equation="c__C -> c__B []",
        compartment="c",
        formula=(
            "(scale_f*Vmax_v4)/Km_A*(c__C - 1 dimensionless/Keq_v4*c__B)",
            U.mole_per_s,
        ),
    ),
]


def create(output_dir: Path) -> None:
    """Create model."""

    # with annotations
    create_model(
        model=model,
        filepath=output_dir / f"{model.sid}.xml",
        annotations=Path(__file__).parent / "demo_annotations.xlsx",
    )

    # without annotations
    create_model(
        model=model,
        filepath=output_dir / f"{model.sid}_no_annotations.xml",
    )


if __name__ == "__main__":
    create(output_dir=Path(__file__).parent / "results")
