"""Example creating composite model."""
from pathlib import Path
from typing import List

from sbmlutils import EXAMPLES_DIR
from sbmlutils.factory import *
from sbmlutils.metadata import *


n_cells = 10
# -------------------------------------------------------------------------------------
_m = Model(
    "minimal_model_comp",
    notes="""
    Hierarchical model reusing the minimal model in composite model coupling.
    """,
)

# create grid of compartments with main species
_m.compartments = []
_m.species = []
for k in range(n_cells):
    _m.compartments.append(
        Compartment(sid=f"cell{k}", value=1.0),
    )
    _m.species.append(
        Species(
            sid=f"S{k}",
            # metaId=f"meta_S{k}",
            initialConcentration=10.0 if k == 0 else 0.0,
            compartment=f"cell{k}",
        )
    )

_m.parameters = [Parameter("D", 0.01)]

# transport reactions to couple cells
_m.reactions = []
for k in range(n_cells - 1):
    _m.reactions.append(
        Reaction(
            sid=f"J{k}", equation=f"S{k} <-> S{k+1}", formula=f"D * (S{k}-S{k+1})"
        ),
    )

# -------------------------------------------------------------------------------------
# model coupling
_m.external_model_definitions = []
_m.replaced_elements = []
_m.submodels = []
for k in range(n_cells):
    _m.external_model_definitions.append(
        ExternalModelDefinition(
            sid=f"emd{k}", source="minimal_model.xml", modelRef="minimal_model"
        ),
    )
    _m.submodels.append(Submodel(sid=f"submodel{k}", modelRef=f"emd{k}"))
    _m.replaced_elements.extend(
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


def create(tmp: bool = False) -> FactoryResult:
    """Create model."""
    return create_model(
        models=_m,
        output_dir=EXAMPLES_DIR,
        units_consistency=False,
        tmp=tmp,
    )


if __name__ == "__main__":
    from sbmlutils.comp import flatten_sbml
    from sbmlutils.cytoscape import visualize_sbml

    fac_result = create()
    sbml_path_flat = Path(__file__).parent / "comp_model_flat.xml"

    # flatten SBML model
    flatten_sbml(fac_result.sbml_path, sbml_flat_path=sbml_path_flat)

    # visualize_sbml(sbml_path=fac_result.sbml_path)
    visualize_sbml(sbml_path=sbml_path_flat)
