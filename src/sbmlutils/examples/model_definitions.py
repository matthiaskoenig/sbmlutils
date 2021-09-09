"""Multiple model definitions."""
from typing import List

from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.units import *


_m = Model("model_definitions_example")
_m.creators = templates.creators
_m.notes = Notes(
    [
        """<p>Example model with multiple ModelDefinitions.</p>""",
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
for unit in _m.units:
    unit.port = False

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

modelDefinitions: List[ModelDefinition] = [
    ModelDefinition(
        sid="m1",
        name="Model Definition 1",
        units=_m.units,
        compartments=[Compartment("d", value=1.0, unit=UNIT_KIND_LITRE)],
        species=[
            Species(
                "A",
                initialAmount=1.0,
                constant=False,
                substanceUnit=UNIT_mmole,
                compartment="d",
                hasOnlySubstanceUnits=True,
            )
        ],
    )
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
