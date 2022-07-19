"""Example creating composite model."""
import shutil
import tempfile
from pathlib import Path

from sbmlutils.comp import flatten_sbml
from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.factory import *
from sbmlutils.metadata import *
from sbmlutils.resources import EXAMPLES_DIR
from sbmlutils.validation import ValidationOptions


n_cells = 10
# -------------------------------------------------------------------------------------
model = Model(
    "minimal_model_comp",
    notes="""
    Hierarchical model reusing the minimal model in composite model coupling.
    """,
)

# create grid of compartments with main species
model.compartments = []
model.species = []
for k in range(n_cells):
    model.compartments.append(
        Compartment(sid=f"cell{k}", value=1.0),
    )
    model.species.append(
        Species(
            sid=f"S{k}",
            # metaId=f"meta_S{k}",
            initialConcentration=10.0 if k == 0 else 0.0,
            compartment=f"cell{k}",
        )
    )

model.parameters = [Parameter("D", 0.01)]

# transport reactions to couple cells
model.reactions = []
for k in range(n_cells - 1):
    model.reactions.append(
        Reaction(
            sid=f"J{k}", equation=f"S{k} <-> S{k+1}", formula=f"D * (S{k}-S{k+1})"
        ),
    )

# -------------------------------------------------------------------------------------
# model coupling
model.external_model_definitions = []
model.replaced_elements = []
model.submodels = []
for k in range(n_cells):
    model.external_model_definitions.append(
        ExternalModelDefinition(
            sid=f"emd{k}", source="minimal_model.xml", modelRef="minimal_model"
        ),
    )
    model.submodels.append(Submodel(sid=f"submodel{k}", modelRef=f"emd{k}"))
    model.replaced_elements.extend(
        [
            # replace compartments
            ReplacedElement(
                sid=f"cell{k}_RE",
                metaId=f"cell{k}_RE",
                elementRef=f"cell{k}",
                submodelRef=f"submodel{k}",
                portRef=f"cell{PORT_SUFFIX}",
            ),
            # replace species
            ReplacedElement(
                sid=f"S{k}_RE",
                metaId=f"S{k}_RE",
                elementRef=f"S{k}",
                submodelRef=f"submodel{k}",
                portRef=f"S1{PORT_SUFFIX}",
            ),
        ]
    )
# -------------------------------------------------------------------------------------


def create(tmp: bool = False) -> None:
    """Create model."""
    if tmp:
        tmp_dir = tempfile.mkdtemp()
        output_dir = Path(tmp_dir)
    else:
        output_dir = EXAMPLES_DIR

    result = create_model(
        model=model,
        filepath=EXAMPLES_DIR / f"{model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=False),
    )

    # flatten SBML model
    sbml_path_flat = EXAMPLES_DIR / f"{model.sid}_flat.xml"
    flatten_sbml(result.sbml_path, sbml_flat_path=sbml_path_flat)
    visualize_sbml(sbml_path=sbml_path_flat)

    if tmp:
        shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    create(tmp=False)