"""FBC mass and charge example."""
from sbmlutils import EXAMPLES_DIR
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitsDefinitions."""

    m2 = UnitDefinition("m2", "meter^2")
    m3 = UnitDefinition("m3", "meter^3")
    mole_per_s = UnitDefinition("mole_per_s", "mole/s")


_m = Model(
    sid="fbc_mass_charge",
    name="fbc model with mass and charge balance",
    packages=["fbc"],
    notes="""
    # Model demonstrating mass and charge balance
    ## Description
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
    compartments=[
        Compartment(
            sid="cyto",
            value="1.0 m3",
            unit=U.m3,
            constant=False,
            name="cytosol",
            sboTerm=SBO.PHYSICAL_COMPARTMENT,
            annotations=[
                (BQB.IS, "go/GO:0005829"),  # cytosol
                (BQB.IS, "https://en.wikipedia.org/wiki/Cytosol"),  # cytosol
            ],
        )
    ],
    species=[
        Species(
            sid="glc",
            compartment="cyto",
            initialConcentration=3.0,
            substanceUnit=U.mole,
            boundaryCondition=True,
            name="D-glucose",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            charge=0,
            chemicalFormula="C6H12O6",
            annotations=[(BQB.IS, "vmhmetabolite/glc_D")],
        ),
        Species(
            sid="atp",
            compartment="cyto",
            initialConcentration=3.0,
            substanceUnit=U.mole,
            boundaryCondition=True,
            name="ATP",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            charge=-4,
            chemicalFormula="C10H12N5O13P3",
            annotations=[(BQB.IS, "vmhmetabolite/atp")],
        ),
        Species(
            sid="glc6p",
            compartment="cyto",
            initialConcentration=3.0,
            substanceUnit=U.mole,
            boundaryCondition=True,
            name="glucose-6 phosphate",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            charge=-2,
            chemicalFormula="C6H11O9P",
            annotations=[(BQB.IS, "vmhmetabolite/g6p")],
        ),
        Species(
            sid="adp",
            compartment="cyto",
            initialConcentration=3.0,
            substanceUnit=U.mole,
            boundaryCondition=True,
            name="ADP",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            charge=-3,
            chemicalFormula="C10H12N5O10P2",
            annotations=[(BQB.IS, "vmhmetabolite/adp")],
        ),
        Species(
            sid="h",
            compartment="cyto",
            initialConcentration=3.0,
            substanceUnit=U.mole,
            boundaryCondition=True,
            name="H+",
            sboTerm=SBO.SIMPLE_CHEMICAL,
            charge=1,
            chemicalFormula="H",
            annotations=[(BQB.IS, "vmhmetabolite/h")],
        ),
    ],
    parameters=[
        Parameter(sid="HEX1_v", value=1.0, unit=U.mole_per_s),
    ],
    reactions=[
        Reaction(
            sid="HEX1",
            name="Hexokinase (D-Glucose:ATP)",
            equation="glc + atp -> glc6p + adp + h",
            sboTerm=SBO.BIOCHEMICAL_REACTION,
            compartment="cyto",
            pars=[],
            formula=("HEX1_v", U.mole_per_s),
            annotations=[
                (
                    BQB.IS,
                    "vmhreaction/HEX1",
                )
            ],
        )
    ],
)

# write custom annotations:
if _m.species:
    for s in _m.species:
        if s.sid == "glc":
            for item in [
                "bigg.metabolite/glc__D",
                "kegg.compound/C00031",
                "hmdb/HMDB0000122",
                "chebi/CHEBI:0004167",
            ]:
                if s.annotations is None:
                    s.annotations = []
                s.annotations.append((BQB.IS, item))

if _m.reactions:
    for r in _m.reactions:
        if r.sid == "HEX1":
            for item in [
                "ec-code/2.7.1.1",
                "ec-code/2.7.1.2",
                "kegg.reaction/R00299",
                "rhea/17828",
            ]:
                if r.annotations is None:
                    r.annotations = []
                r.annotations.append((BQB.IS, item))


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
