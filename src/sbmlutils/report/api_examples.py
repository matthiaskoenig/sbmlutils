"""Example models for the sbml4humans API."""
from pathlib import Path
from typing import List, Optional

import libsbml
from pydantic import BaseModel, FilePath
from pymetadata.omex import Omex

from sbmlutils.console import console
from sbmlutils.io import read_sbml
from sbmlutils.test import API_EXAMPLES_MODEL, API_EXAMPLES_OMEX, BIOMODELS_CURATED_PATH


class ExampleMetaData(BaseModel):
    """Metadata for example model on sbml4humans."""

    id: str
    file: FilePath
    name: Optional[str] = None
    description: Optional[str] = None
    packages: List[str] = []


def create_models_metadata(sbml_path: Path) -> ExampleMetaData:
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
        id=f"{sid} ({sbml_path.name})",
        name=name,
        description=description,
        packages=packages,
    )


def create_omex_metadata(omex_path: Path) -> ExampleMetaData:
    """Create metadata from OMEX file."""

    omex = Omex.from_omex(omex_path)

    return ExampleMetaData(
        file=omex_path,
        id=omex_path.stem,
        name=omex_path.stem,
        description=str(omex.manifest),
        packages=["OMEX"],
    )


def biomodels_examples() -> List[ExampleMetaData]:
    """Biomodel examples."""
    examples: List[ExampleMetaData] = []
    with console.status("Processing examples ...", spinner="aesthetic"):
        for k in range(1, 50):
            biomodel_id = f"BIOMD0000000{k:0>3}"
            omex_path = BIOMODELS_CURATED_PATH / f"{biomodel_id}.omex"
            omex = Omex.from_omex(omex_path)
            sbml_entries = omex.entries_by_format(format_key="sbml")
            print(biomodel_id)
            print(omex)
            print(sbml_entries)
            biomodel_path = omex.get_path(sbml_entries[0].location)
            example = create_models_metadata(biomodel_path)
            example.id = biomodel_id
            examples.append(example)

    return examples


examples = [create_omex_metadata(p) for p in API_EXAMPLES_OMEX]
examples += [create_models_metadata(p) for p in API_EXAMPLES_MODEL]
examples += biomodels_examples()
examples_info = {emd.id: emd for emd in examples}
