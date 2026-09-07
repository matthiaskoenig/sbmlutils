"""Example for model composition via multiple models."""

from pathlib import Path

from examples.tutorial.minimal_model import model as minimal_model
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *
from sbmlutils.metadata import BQB
from sbmlutils.validation import ValidationOptions

model = Model(
    sid="model_composition",
    name="model composition from multiple models",
    annotations=[(BQB.IS, "taxonomy/911")],
    parameters=[
        Parameter(sid="k2", value=0.1),
    ],
    reactions=[
        Reaction(sid="J1", equation="-> S1", formula="k2"),
    ],
)


def create(output_dir: Path) -> FactoryResult:
    """Create model."""
    results = create_model(
        model=[minimal_model, model],
        filepath=output_dir / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )

    return results


if __name__ == "__main__":
    fac_result = create(output_dir=Path.cwd())
    visualize_sbml(sbml_path=fac_result.sbml_path)
