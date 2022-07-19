"""Annotation example.

Model demonstrates how to annotate model objects with SBOTerms and Terms from
other ontologies. Annotations use the functionality from `pymetadata`.
"""
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.resources import EXAMPLES_DIR


class U(Units):
    """ModelDefinitions."""

    mM = UnitDefinition("mM", "mmole/l")
    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")
    kg = UnitDefinition("kg", "kg")
    per_s = UnitDefinition("per_s", "1/s")
    mole_per_s = UnitDefinition("mole_per_s", "mole/s")


model = Model(
    sid="annotation",
    name="model with inline annotations",
    notes="""
    # Model with inline annotations

    Test model demonstrating inline annotations.
    """
    + templates.terms_of_use,
    creators=templates.creators,
    units=U,
    model_units=ModelUnits(
        time=U.second,
        extent=U.mole,
        substance=U.mole,
        length=U.meter,
        area=U.m2,
        volume=U.m3,
    ),
)

model.compartments = [
    Compartment(
        sid="ext",
        value="Vol_e",
        unit=U.m3,
        constant=True,
        name="external",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=[
            (BQB.IS, "bto/BTO:0000089"),  # blood
        ],
    ),
    Compartment(
        sid="cyto",
        value="Vol_c",
        unit=U.m3,
        constant=False,
        name="cytosol",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=[
            (BQB.IS, "go/GO:0005829"),  # cytosol
            (BQB.IS, "https://en.wikipedia.org/wiki/Cytosol"),  # cytosol
        ],
    ),
    Compartment(
        sid="pm",
        value="A_m",
        unit=U.m2,
        constant=True,
        spatialDimensions=2,
        name="membrane",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=[
            (BQB.IS, "go/GO:0005886"),  # plasma membrane
        ],
    ),
]

model.species = [
    Species(
        sid="e__gal",
        compartment="ext",
        initialConcentration=3.0,
        substanceUnit=U.mole,
        boundaryCondition=True,
        name="D-galactose",
        sboTerm=SBO.SIMPLE_CHEMICAL,
        annotations=[
            (BQB.IS, "bigg.metabolite/gal"),  # galactose
            (BQB.IS, "chebi/CHEBI:28061"),  # alpha-D-galactose
            (BQB.IS, "vmhmetabolite/gal"),
        ],
    ),
    Species(
        sid="c__gal",
        compartment="cyto",
        initialConcentration=0.00012,
        substanceUnit=U.mole,
        boundaryCondition=False,
        name="D-galactose",
        sboTerm=SBO.SIMPLE_CHEMICAL,
    ),
]

model.parameters = [
    Parameter(
        sid="x_cell", value=25e-6, unit=U.meter, constant=True, name="cell diameter"
    ),
    Parameter(
        sid="Vol_e", value=100e-14, unit=U.m3, constant=True, name="external volume"
    ),
    Parameter(sid="A_m", value=1.0, unit=U.m2, constant=True, name="membrane area"),
]

model.assignments = [
    InitialAssignment(symbol="Vol_c", value="x_cell*x_cell*x_cell", unit=U.m3),
]

model.reactions = [
    Reaction(
        sid="e__GLUT2_GAL",
        name="galactose transport [e__]",
        equation="e__gal <-> c__gal []",
        # C6H1206 (0) <-> C6H1206 (0)
        compartment="pm",
        pars=[
            Parameter(sid="GLUT2_Vmax", value=1e-13, unit=U.mole_per_s),
            Parameter("GLUT2_k_gal", 1.0, U.mM),
            Parameter("GLUT2_keq", 1.0, U.dimensionless),
        ],
        formula=(
            "GLUT2_Vmax/GLUT2_k_gal * (e__gal - c__gal/GLUT2_keq)/"
            "(1 dimensionless + c__gal/GLUT2_k_gal + e__gal/GLUT2_k_gal)",
            U.mole_per_s,
        ),
        annotations=[
            (BQB.IS, "sbo/SBO:0000284"),  # transporter
        ],
    )
]


if __name__ == "__main__":
    create_model(model=model, filepath=EXAMPLES_DIR / f"{model.sid}.xml")
