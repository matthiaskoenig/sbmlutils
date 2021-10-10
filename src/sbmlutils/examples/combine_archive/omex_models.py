"""Example creating minimal model.

This demonstrates just the very core SBML functionality.
"""
import tempfile
from pathlib import Path
from typing import Dict

from pymetadata.omex import EntryFormat, ManifestEntry, Omex

from sbmlutils import EXAMPLES_DIR
from sbmlutils.comp import flatten_sbml
from sbmlutils.console import console
from sbmlutils.examples.templates import creators, terms_of_use
from sbmlutils.factory import *


# -------------------------------------------------------------------------------------
model_minimal = Model(
    sid="omex_minimal",
    notes=terms_of_use,
    creators=creators,
    packages=["fbc"],
    compartments=[
        Compartment(sid="cell", value=1.0, port=True),
    ],
    species=[
        Species(sid="S1", initialConcentration=10.0, compartment="cell", port=True),
        Species(sid="S2", initialConcentration=0.0, compartment="cell"),
    ],
    parameters=[
        Parameter(sid="k1", value=0.1),
    ],
    reactions=[
        Reaction(sid="J0", equation="S1 -> S2", formula="k1 * S2"),
    ],
)
# -------------------------------------------------------------------------------------

n_cells = 5

_m = Model(
    sid="omex_comp",
    notes="""
    Hierarchical model reusing the minimal model in composite model coupling.
    """,
    compartments=[],
    species=[],
    reactions=[],
    parameters=[Parameter("D", 0.01)],
    external_model_definitions=[],
    replaced_elements=[],
    submodels=[],
)

# create grid of compartments with main species
for k in range(n_cells):
    _m.compartments.append(  # type: ignore
        Compartment(sid=f"cell{k}", value=1.0),
    )
    _m.species.append(  # type: ignore
        Species(
            sid=f"S{k}",
            # metaId=f"meta_S{k}",
            initialConcentration=10.0 if k == 0 else 0.0,
            compartment=f"cell{k}",
        )
    )

# transport reactions to couple cells
for k in range(n_cells - 1):
    _m.reactions.append(  # type: ignore
        Reaction(
            sid=f"J{k}", equation=f"S{k} <-> S{k+1}", formula=f"D * (S{k}-S{k+1})"
        ),
    )

# model coupling
for k in range(n_cells):
    _m.external_model_definitions.append(  # type: ignore
        ExternalModelDefinition(
            sid=f"emd{k}",
            source=f"{model_minimal.sid}.xml",
            modelRef=f"{model_minimal.sid}",
        ),
    )
    _m.submodels.append(Submodel(sid=f"submodel{k}", modelRef=f"emd{k}"))  # type: ignore
    _m.replaced_elements.extend(  # type: ignore
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

comp_model = _m
# -------------------------------------------------------------------------------------
results: Dict[str, Path] = {}


def create_omex(tmp: bool = False) -> None:
    """Create omex with models."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        if tmp:
            output_dir = Path(tmp_dir)
        else:
            output_dir = EXAMPLES_DIR

        results_minimal_model = create_model(
            models=model_minimal,
            output_dir=output_dir,
            units_consistency=False,
        )
        results_comp_model = create_model(
            models=comp_model,
            output_dir=output_dir,
            units_consistency=False,
        )
        sbml_flat_path = (
            results_comp_model.sbml_path.parent / f"{comp_model.sid}_flat.xml"
        )
        flatten_sbml(
            sbml_path=results_comp_model.sbml_path, sbml_flat_path=sbml_flat_path
        )

        sbml_paths = [
            results_minimal_model.sbml_path,
            results_comp_model.sbml_path,
            sbml_flat_path,
        ]

        # Create COMBINE archive
        omex = Omex()
        for path in sbml_paths:
            omex.add_entry(
                entry_path=path,
                entry=ManifestEntry(
                    format=EntryFormat.SBML_L3V1, location=f"./models/{path.name}"
                ),
            )
        omex_path = output_dir / f"{comp_model.sid}.omex"
        omex.to_omex(omex_path)
        console.print(f"OMEX created: {omex_path}")
        console.print(omex.manifest.dict())


if __name__ == "__main__":
    create_omex()
