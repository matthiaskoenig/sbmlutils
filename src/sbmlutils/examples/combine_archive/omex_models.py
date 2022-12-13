"""Example creating minimal model.

This demonstrates just the very core SBML functionality.
"""
from pathlib import Path
from typing import Optional

from pymetadata.omex import EntryFormat, ManifestEntry, Omex

from sbmlutils.comp import flatten_sbml
from sbmlutils.console import console
from sbmlutils.examples.templates import creators, terms_of_use
from sbmlutils.factory import *
from sbmlutils.resources import EXAMPLES_DIR


# -------------------------------------------------------------------------------------
model = Model(
    sid="omex_minimal",
    notes=terms_of_use,
    creators=creators,
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
n_cells: int = 5
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

# transport reactions to couple cells
for k in range(n_cells - 1):
    _m.reactions.append(  # type: ignore
        Reaction(
            sid=f"J{k}", equation=f"S{k} <-> S{k+1}", formula=f"D * (S{k}-S{k+1})"
        ),
    )

# model coupling
for k in range(n_cells):
    _m.external_model_definitions.append(
        ExternalModelDefinition(
            sid=f"emd{k}",
            source=f"{_m.sid}.xml",
            modelRef=f"{_m.sid}",
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

model_comp = _m


def create_omex(tmp_dir: Optional[Path] = None) -> None:
    """Create omex with models."""

    output_dir = tmp_dir if tmp_dir else EXAMPLES_DIR
    sbml_path = output_dir / f"{model.sid}.xml"
    sbml_comp_path = output_dir / f"{_m.sid}.xml"
    sbml_comp_flat_path = output_dir / f"{_m.sid}_flat.xml"

    create_model(
        model=model,
        filepath=sbml_path,
        validation_options=ValidationOptions(units_consistency=False),
        sbml_level=3,
        sbml_version=1,
    )
    create_model(
        model=model_comp,
        filepath=sbml_comp_path,
        validation_options=ValidationOptions(units_consistency=False),
        sbml_level=3,
        sbml_version=1,
    )
    flatten_sbml(sbml_path=sbml_comp_path, sbml_flat_path=sbml_comp_flat_path)

    # Create COMBINE archive
    omex = Omex()
    for path in [sbml_path, sbml_comp_path, sbml_comp_flat_path]:
        omex.add_entry(
            entry_path=path,
            entry=ManifestEntry(
                format=EntryFormat.SBML_L3V1, location=f"./models/{path.name}"
            ),
        )
    omex_path = output_dir / f"{model_comp.sid}.omex"
    omex.to_omex(omex_path)
    console.print(f"OMEX created: {omex_path}")
    console.print(omex.manifest.dict())


if __name__ == "__main__":
    create_omex()
