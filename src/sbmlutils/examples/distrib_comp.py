"""Distrib and comp example to check flattening."""
import shutil
import tempfile
from pathlib import Path

import libsbml

from sbmlutils import EXAMPLES_DIR
from sbmlutils.comp import flatten_sbml
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitsDefinitions."""

    hr = UnitDefinition("hr")
    m2 = UnitDefinition("m2", "meter^2")


_m = Model(
    "distrib_comp",
    name="model combining distrib and comp",
    packages=["distrib", "comp"],
    creators=templates.creators,
    notes="""
    # Example model using distrib and comp packages
    Example creating distrib model with distribution elements.
    """
    + templates.terms_of_use,
    units=U,
    model_units=ModelUnits(
        time=U.hr,
        extent=U.mole,
        substance=U.mole,
        length=U.meter,
        area=U.m2,
        volume=U.liter,
    ),
    parameters=[
        Parameter(
            sid="p1",
            value=1.0,
            unit=U.mole,
            constant=True,
            port=True,
            uncertainties=[
                Uncertainty(
                    formula="normal(2.0, 2.0)",
                    uncertParameters=[
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=2.0
                        ),
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
    ],
)


def create(tmp: bool = False) -> None:
    """Create model."""
    if tmp:
        tmp_dir = tempfile.mkdtemp()
        output_dir = Path(tmp_dir)
    else:
        output_dir = EXAMPLES_DIR
    sbml_path_flat = output_dir / "distrib_comp_flat.xml"

    result = create_model(
        models=_m,
        output_dir=output_dir,
    )

    flatten_sbml(result.sbml_path, sbml_flat_path=sbml_path_flat)
    # create model report
    # sbmlreport.create_report(sbml_path_flat)

    if tmp:
        shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    create(tmp=False)
