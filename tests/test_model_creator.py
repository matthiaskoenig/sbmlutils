"""Test the creator module."""
from pathlib import Path

import pytest

from sbmlutils.factory import *
from sbmlutils.io import read_sbml
from sbmlutils.validation import ValidationOptions


level_version_testdata = [
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (3, 1),
    (3, 2),
]


@pytest.mark.parametrize("level, version", level_version_testdata)
def test_sbml_level_version(level: int, version: int, tmp_path: Path) -> None:
    """Test that the various levels and versions of SBML can be generated."""
    md = {
        "sid": "level_version",
        "compartments": [Compartment(sid="C", value=1.0)],
        "species": [
            Species(
                sid="S1",
                initialConcentration=10.0,
                compartment="C",
                hasOnlySubstanceUnits=False,
                boundaryCondition=True,
            )
        ],
        "parameters": [Parameter(sid="k1", value=1.0)],
        "reactions": [
            Reaction(
                sid="R1",
                equation="S1 ->",
                formula=("k1 * S1 * sin(time)", Units.dimensionless),
            )
        ],
    }

    results = create_model(
        model=Model(**md),  # type: ignore
        filepath=tmp_path / "model.xml",
        sbml_level=level,
        sbml_version=version,
        validation_options=ValidationOptions(units_consistency=False),
    )
    doc = read_sbml(source=results.sbml_path, validate=False)
    assert level == doc.getLevel()
    assert version == doc.getVersion()
