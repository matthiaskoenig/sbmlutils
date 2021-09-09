"""Simple assignment test case."""
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.units import *


_m = Model("initial_assignment_example")
_m.creators = templates.creators
_m.notes = Notes(
    [
        """<p>Example model for testing InitialAssignments in roadrunner.</p>""",
        templates.terms_of_use,
    ]
)
_m.model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_mmole,
    substance=UNIT_mmole,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
_m.units = [
    UNIT_min,
    UNIT_mmole,
    UNIT_m,
    UNIT_m2,
]
_m.compartments = [Compartment("c", value=2.0, unit=UNIT_KIND_LITRE)]
_m.species = [
    Species(
        "A1",
        initialAmount=1.0,
        constant=False,
        substanceUnit=UNIT_mmole,
        compartment="c",
        hasOnlySubstanceUnits=True,
    )
]
_m.parameters = [
    Parameter("D", 5.0, UNIT_mmole, constant=True),
]
_m.assignments = [
    InitialAssignment("A1", "D * 2 dimensionless", UNIT_mmole),
]


def create(tmp: bool = False) -> None:
    """Create model."""
    create_model(
        models=_m,
        output_dir=EXAMPLE_RESULTS_DIR,
        tmp=tmp,
    )


if __name__ == "__main__":
    create()
