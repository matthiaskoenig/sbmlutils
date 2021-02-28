"""Distrib and comp example to check flattening."""
import shutil
import tempfile
from pathlib import Path

import libsbml

from sbmlutils.comp import flatten_sbml
from sbmlutils.creator import create_model
from sbmlutils.examples import EXAMPLE_RESULTS_DIR, templates
from sbmlutils.factory import *
from sbmlutils.report import sbmlreport
from sbmlutils.units import *


mid = "distrib_comp_example"
packages = ["distrib", "comp"]
creators = templates.creators
notes = Notes(
    [
        """
    <h1>sbmlutils {}</h1>
    <h2>Description</h2>
    <p>Example creating distrib model with distribution elements.</p>
    """,
        templates.terms_of_use,
    ]
)
model_units = ModelUnits(
    time=UNIT_hr,
    extent=UNIT_KIND_MOLE,
    substance=UNIT_KIND_MOLE,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_KIND_LITRE,
)
units = [
    UNIT_hr,
    UNIT_m,
    UNIT_m2,
]

parameters = [
    Parameter(
        sid="p1",
        value=1.0,
        unit=UNIT_KIND_MOLE,
        constant=True,
        port=True,
        uncertainties=[
            Uncertainty(
                formula="normal(2.0, 2.0)",
                uncertParameters=[
                    UncertParameter(type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=2.0),
                    UncertParameter(
                        type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=2.0
                    ),
                ],
                uncertSpans=[
                    UncertSpan(
                        type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                        valueLower=1.0,
                        valueUpper=4.0,
                    ),
                ],
            )
        ],
    )
]


def create(tmp: bool = False) -> None:
    """Create model."""
    if tmp:
        tmp_dir = tempfile.mkdtemp()
        output_dir = Path(tmp_dir)
    else:
        output_dir = EXAMPLE_RESULTS_DIR
    sbml_path_flat = output_dir / "distrib_comp_example_flat.xml"

    [_, _, sbml_path] = create_model(
        modules=["sbmlutils.examples.distrib_comp"],
        output_dir=output_dir,
    )

    flatten_sbml(sbml_path, filepath=sbml_path_flat)
    # create model report
    sbmlreport.create_report(sbml_path_flat, output_dir=output_dir)

    if tmp:
        shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    create(tmp=True)
