"""FBC mass and charge example."""

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.metadata.miriam import *
from sbmlutils.metadata.sbo import *
from sbmlutils.units import *


mid = "mass_charge_example"
packages = ["fbc"]
notes = Notes(
    [
        """
    <h1>Model demonstrating mass and charge balance</h1>
    <h2>Description</h2>
    <p>Test model demonstrating inline annotations.
    </p>
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators


model_units = ModelUnits(
    time=UNIT_s,
    extent=UNIT_KIND_MOLE,
    substance=UNIT_KIND_MOLE,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_m3,
)
units = [UNIT_kg, UNIT_s, UNIT_m, UNIT_m2, UNIT_m3, UNIT_mM, UNIT_mole_per_s]

compartments = [
    Compartment(
        sid="cyto",
        value="1.0 m3",
        unit="m3",
        constant=False,
        name="cytosol",
        sboTerm=SBO_PHYSICAL_COMPARTMENT,
        annotations=[
            (BQB.IS, "go/GO:0005829"),  # cytosol
            (BQB.IS, "https://en.wikipedia.org/wiki/Cytosol"),  # cytosol
        ],
    )
]
species = [
    Species(
        sid="glc",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_KIND_MOLE,
        boundaryCondition=True,
        name="D-glucose",
        sboTerm=SBO_SIMPLE_CHEMICAL,
        charge=0,
        chemicalFormula="C6H12O6",
        annotations=[(BQB.IS, "vmhmetabolite/glc_D")],
    ),
    Species(
        sid="atp",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_KIND_MOLE,
        boundaryCondition=True,
        name="ATP",
        sboTerm=SBO_SIMPLE_CHEMICAL,
        charge=-4,
        chemicalFormula="C10H12N5O13P3",
        annotations=[(BQB.IS, "vmhmetabolite/atp")],
    ),
    Species(
        sid="glc6p",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_KIND_MOLE,
        boundaryCondition=True,
        name="glucose-6 phosphate",
        sboTerm=SBO_SIMPLE_CHEMICAL,
        charge=-2,
        chemicalFormula="C6H11O9P",
        annotations=[(BQB.IS, "vmhmetabolite/g6p")],
    ),
    Species(
        sid="adp",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_KIND_MOLE,
        boundaryCondition=True,
        name="ADP",
        sboTerm=SBO_SIMPLE_CHEMICAL,
        charge=-3,
        chemicalFormula="C10H12N5O10P2",
        annotations=[(BQB.IS, "vmhmetabolite/adp")],
    ),
    Species(
        sid="h",
        compartment="cyto",
        initialConcentration=3.0,
        substanceUnit=UNIT_KIND_MOLE,
        boundaryCondition=True,
        name="H+",
        sboTerm=SBO_SIMPLE_CHEMICAL,
        charge=1,
        chemicalFormula="H",
        annotations=[(BQB.IS, "vmhmetabolite/h")],
    ),
]

parameters = [
    Parameter(sid="HEX1_v", value=1.0, unit="mole_per_s"),
]

reactions = [
    Reaction(
        sid="HEX1",
        name="Hexokinase (D-Glucose:ATP)",
        equation="glc + atp -> glc6p + adp + h",
        sboTerm=SBO_BIOCHEMICAL_REACTION,
        compartment="cyto",
        pars=[],
        formula=("HEX1_v", "mole_per_s"),
        annotations=[
            (
                BQB.IS,
                "vmhreaction/HEX1",
            )
        ],
    )
]

# write custom annotations:
for s in species:
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

for r in reactions:
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
        modules=["sbmlutils.examples.fbc_mass_charge"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
