"""Distrib and comp example to check flattening."""
import shutil
from pathlib import Path

import libsbml

from sbmlutils.comp import flatten_sbml
from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.metadata import *


class U(Units):
    """UnitsDefinitions."""

    hr = UnitDefinition("hr")
    m2 = UnitDefinition("m2", "meter^2")


model = Model(
    "distrib_comp",
    name="model combining distrib and comp",
    packages=[Package.DISTRIB_V1, Package.COMP_V1],
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


def create(output_dir: Path) -> None:
    """Create and flatten model."""

    sbml_path = output_dir / f"{model.sid}.xml"
    sbml_path_flat = output_dir / f"{model.sid}_flat.xml"

    create_model(model=model, filepath=sbml_path)

    flatten_sbml(sbml_path, sbml_flat_path=sbml_path_flat)


if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    create(output_dir=EXAMPLES_DIR)
