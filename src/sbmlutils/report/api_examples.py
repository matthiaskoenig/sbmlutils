"""Example models for the sbml4humans API."""
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

import libsbml

from sbmlutils.io import read_sbml
from sbmlutils.test import BIOMODELS_CURATED_PATH
from sbmlutils.test import EXAMPLES
from sbmlutils.console import console


class ExampleMetaData(BaseModel):
    """Metadata for example model on sbml4humans."""
    id: str
    file: Path
    name: Optional[str] = None
    description: Optional[str] = None
    packages: List[str] = []


def read_example_metadata(sbml_path: Path) -> ExampleMetaData:
    """Reads metadata from SBML file."""

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
        for k in range(1, 100):
            biomodel_id = f"BIOMD0000000{k:0>3}"
            biomodel_path = BIOMODELS_CURATED_PATH / f"{biomodel_id}.xml.gz"

            example = read_example_metadata(biomodel_path)
            example.id = biomodel_id
            examples.append(example)

    return examples


examples = [read_example_metadata(p) for p in EXAMPLES]
examples += biomodels_examples()

examples_info = {emd.id: emd for emd in examples}
