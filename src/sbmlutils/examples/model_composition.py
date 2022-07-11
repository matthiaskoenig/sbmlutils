"""Example for model composition via multiple models."""
from sbmlutils.resources import EXAMPLES_DIR
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples.minimal_model import model_minimal
from sbmlutils.factory import *
from sbmlutils.metadata import *
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


def create() -> FactoryResult:
    """Create model."""
    return create_model(
        model=[model_minimal, model],
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )


if __name__ == "__main__":
    fac_result = create()
    visualize_sbml(sbml_path=fac_result.sbml_path)
