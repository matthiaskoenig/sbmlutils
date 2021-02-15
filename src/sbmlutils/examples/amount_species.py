"""Model with amount species."""

from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.units import *


mid = "amount_species_example"
notes = Notes(
    [
        """
    <h1>Koenig Demo Metabolism</h1>
    <h2>Description</h2>
    <p>This is a demonstration model for species in amounts
    <a href="http://sbmlutils.org" target="_blank" title="Access the definition of the SBML file format.">
    SBML</a>&#160;format.
    </p>
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators

model_units = ModelUnits(
    time=UNIT_s,
    substance=UNIT_mmole,
    extent=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_m3,
)
units = [
    UNIT_s,
    UNIT_kg,
    UNIT_m,
    UNIT_m2,
    UNIT_m3,
    UNIT_mM,
    UNIT_mmole,
    UNIT_per_s,
    UNIT_mmole_per_s,
]
compartments = [
    Compartment(
        sid="Vc", value=1e-06, unit=UNIT_m3, constant=False, name="cell compartment"
    ),
]
species = [
    Species(
        sid="Aglc",
        compartment="Vc",
        initialAmount=5.0,
        substanceUnit=UNIT_mmole,
        hasOnlySubstanceUnits=True,
        boundaryCondition=False,
        name="glucose",
    ),
]
reactions = [
    Reaction(
        sid="R1",
        equation="Aglc =>",
        compartment="Vc",
        pars=[Parameter("k1", 1.0, UNIT_per_s)],
        rules=[],
        formula=("k1 * Aglc", UNIT_mmole_per_s),
    )
]
rules = [AssignmentRule("Vc", "2.0 m3 * exp(time/1 s)")]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        modules=["sbmlutils.examples.amount_species"],
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
