"""Example for model composition via multiple models."""
import shutil
import tempfile
from pathlib import Path

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples.minimal_model import model
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.resources import EXAMPLES_DIR
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


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    if tmp:
        tmp_dir = tempfile.mkdtemp()
        output_dir = Path(tmp_dir)
    else:
        output_dir = EXAMPLES_DIR

    results = create_model(
        model=[model, model],
        filepath=output_dir / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )

    if tmp:
        shutil.rmtree(tmp_dir)

    return results


if __name__ == "__main__":
    fac_result = create(tmp=False)
    visualize_sbml(sbml_path=fac_result.sbml_path)
