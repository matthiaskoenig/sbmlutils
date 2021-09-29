"""Example models for the sbml4humans API."""
from pathlib import Path
from typing import Dict, List, Optional

import libsbml
from pydantic import BaseModel, FilePath

from sbmlutils import EXAMPLES_DIR
from sbmlutils.console import console
from sbmlutils.io import read_sbml
from sbmlutils.test import BIOMODELS_CURATED_PATH, EXAMPLE_MODELS


class ExampleMetaData(BaseModel):
    """Metadata for example model on sbml4humans."""

    id: str
    file: FilePath
    name: Optional[str] = None
    description: Optional[str] = None
    packages: List[str] = []


def read_example_metadata(sbml_path: Path) -> ExampleMetaData:
    """Read metadata from SBML file."""

    doc: libsbml.SBMLDocument = read_sbml(sbml_path, validate=False)
    model: libsbml.Model = doc.getModel()

    if not model:
        raise ValueError(f"Model could not be read for '{sbml_path}'")

    sid: str = model.getId() if model.isSetId() else None
    if not sid:
        sid = sbml_path.stem
    name: str = model.getName() if model.isSetName() else None
    description: str = model.getNotesString() if model.isSetNotes() else None
    packages: List[str] = []
    for k in range(doc.getNumPlugins()):
        plugin: libsbml.SBMLDocumentPlugin = doc.getPlugin(k)
        packages.append(plugin.getPrefix())

    return ExampleMetaData(
        file=sbml_path,
        id=sid,
        name=name,
        description=description,
        packages=packages,
    )


def biomodels_examples() -> List[ExampleMetaData]:
    """Biomodel examples."""
    examples: List[ExampleMetaData] = []
    with console.status("Processing examples ...", spinner="aesthetic"):
        for k in range(1, 50):
            biomodel_id = f"BIOMD0000000{k:0>3}"
            biomodel_path = BIOMODELS_CURATED_PATH / f"{biomodel_id}.xml.gz"

            example = read_example_metadata(biomodel_path)
            example.id = biomodel_id
            examples.append(example)

    return examples


creator_example_ids = [
    "amount_species",
    "annotation",
    "assignment",
    "boundary_condition",
    "compartment_species_reaction",
    "complete_model",
    "distrib_comp",
    "distrib_distributions",
    "distrib_uncertainties",
    "fbc_example",
    "fbc_mass_charge",
    "linear_chain",
    "minimal_model",
    "minimal_model_comp",
    "model_composition",
    "model_definitions",
    "multiple_substance_units",
    "nan",
    "notes",
    "random_network",
    "reaction",
    "simple_reaction_with_units",
    "unit_definitions",
    "units_namespace",
]

examples = [read_example_metadata(p) for p in EXAMPLE_MODELS]
examples += [
    read_example_metadata(EXAMPLES_DIR / f"{eid}.xml") for eid in creator_example_ids
]
examples += biomodels_examples()

examples_info = {emd.id: emd for emd in examples}
