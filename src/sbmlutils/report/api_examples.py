"""Example models for the sbml4humans API."""
from typing import Dict, List

import libsbml

from sbmlutils.io import read_sbml

from sbmlutils.test import (
    COMP_ICG_BODY,
    COMP_ICG_BODY_FLAT,
    COMP_ICG_LIVER,
    COMP_MODEL_DEFINITIONS_SBML,
    DISTRIB_DISTRIBUTIONS_SBML,
    DISTRIB_UNCERTAINTIES_SBML,
    FBC_ECOLI_CORE_SBML,
    FBC_RECON3D_SBML,
    GLUCOSE_SBML,
    REPRESSILATOR_SBML,
    BIOMODELS_CURATED_PATH,
)


# Data and Endpoints for Example Models
examples: List[Dict] = [
    {
        "file": GLUCOSE_SBML,
        "metadata": {
            "id": "glucose",
            "name": "Koenig2012 - Glucose",
            "description": "Koenig 2021 model of Human liver glucose homeostasis.",
            "packages": [],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": REPRESSILATOR_SBML,
        "metadata": {
            "id": "repressilator",
            "name": "BIOMD0000000012 - Elowitz2000 - Repressilator (biomodels)",
            "description": "Ellowitz 2000 repressilator example",
            "packages": [],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": FBC_ECOLI_CORE_SBML,
        "metadata": {
            "id": "ecoli_core",
            "name": "E.coli core metabolism (BiGG)",
            "description": "Small-scale FBC example",
            "packages": ["fbc", "groups"],
            "keywords": ["fbc"],
        },
    },
    {
        "file": COMP_MODEL_DEFINITIONS_SBML,
        "metadata": {
            "id": "model_definitions",
            "name": "Comp ModelDefinitions",
            "description": "Example model for comp ModelDefinitions",
            "packages": ["comp"],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": DISTRIB_DISTRIBUTIONS_SBML,
        "metadata": {
            "id": "distributions",
            "name": "Distrib distributions",
            "description": "Example model for distrib distributions",
            "packages": ["distrib"],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": DISTRIB_UNCERTAINTIES_SBML,
        "metadata": {
            "id": "uncertainties",
            "name": "Distrib uncertainties",
            "description": "Example model for distrib uncertainties",
            "packages": ["distrib"],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": COMP_ICG_BODY_FLAT,
        "metadata": {
            "id": "icg_body_flat",
            "name": "Flattened ICG comp model",
            "description": "Example model for comp flattening",
            "packages": [],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": COMP_ICG_BODY,
        "metadata": {
            "id": "icg_body",
            "name": "ICG comp model",
            "description": "Example model for comp",
            "packages": ["comp"],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": COMP_ICG_LIVER,
        "metadata": {
            "id": "icg_liver",
            "name": "ICG comp submodel",
            "description": "Example model for comp submodel",
            "packages": ["comp"],
            "keywords": ["kinetic"],
        },
    },
    {
        "file": FBC_RECON3D_SBML,
        "metadata": {
            "id": "recon3d",
            "name": "RECON3D human metabolism (BiGG)",
            "description": "Genome-scale FBC example",
            "packages": ["fbc", "groups"],
            "keywords": ["fbc"],
        },
    },
]


biomodels_paths = []
# for k in range(1, 988)

for k in range(1, 988):
    if k in [649, 694, 923]:
        continue
    biomodel_id = f"BIOMD0000000{k:0>3}"
    biomodel_path = BIOMODELS_CURATED_PATH / f"{biomodel_id}.xml.gz"
    doc: libsbml.SBMLDocument = read_sbml(biomodel_path, validate=False)
    model: libsbml.Model = doc.getModel()

    name = model.getName() if model.isSetName() else None
    packages = []
    for k in range(doc.getNumPlugins()):
        plugin: libsbml.SBMLDocumentPlugin = doc.getPlugin(k)
        packages.append(plugin.getPrefix())


    examples.append({
        "file": biomodel_path,
        "metadata": {
            "id": biomodel_id,
            "name": name,
            "description": "",
            "packages": packages,
            "keywords": [],
        }
    })


examples_info = {example["metadata"]["id"]: example for example in examples}
