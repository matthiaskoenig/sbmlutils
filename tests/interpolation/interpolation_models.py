"""The models the tests of driving a model with data use."""

from pathlib import Path

from sbmlutils.factory import (
    Compartment,
    Model,
    Parameter,
    Reaction,
    Species,
    create_model,
)
from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.validation import ValidationOptions

#: the uptake model is written without units, the unit check is not the subject
OPTIONS = ValidationOptions(units_consistency=False)


def uptake_model() -> Model:
    """Glucose uptake: `glc_ext` in `ext` taken up into `glc` in `cell`."""
    return Model(
        "uptake",
        compartments=[Compartment("ext", 2.0), Compartment("cell", 1.0)],
        species=[
            Species("glc_ext", initialConcentration=5.0, compartment="ext"),
            Species("glc", initialConcentration=0.0, compartment="cell"),
        ],
        parameters=[Parameter("k", 0.5), Parameter("f", 1.0)],
        reactions=[
            Reaction("UPTAKE", "glc_ext -> glc", formula="f * k * glc_ext"),
            Reaction("USE", "glc -> ", formula="0.1 * glc"),
        ],
    )


def write_model(model: Model, path: Path, level: int = 3, version: int = 1) -> Path:
    """Write a model, converted to the level and version, and return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    create_model(model, filepath=path, validation_options=OPTIONS)
    if (level, version) != (3, 1):
        doc = read_sbml(path)
        assert doc.setLevelAndVersion(level, version, False)
        write_sbml(doc, filepath=path)
    return path
