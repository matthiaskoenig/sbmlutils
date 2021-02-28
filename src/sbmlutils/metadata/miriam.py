"""
Helper module for working with MIRIAM metadata.

This includes identifiers.org, MIRIAM qualifiers and the
identifiers.org collections (MIRIAM registry).
For updating the MIRIAM registry see the parse_registry script.
"""

import json
import logging
import re
from enum import Enum
from typing import Any, Dict

from sbmlutils import RESOURCES_DIR


logger = logging.getLogger(__name__)

__all__ = [
    "BQM",
    "BQB",
    "MIRIAM_COLLECTION",
    "IDENTIFIERS_ORG_PATTERN",
    "IDENTIFIERS_ORG_PREFIX",
]


IDENTIFIERS_ORG_PREFIX = "https://identifiers.org"
IDENTIFIERS_ORG_PATTERN = re.compile(r"^https?://identifiers.org/(.+?)/(.+)")

QualifierType = {
    0: "MODEL_QUALIFIER",
    1: "BIOLOGICAL_QUALIFIER",
    2: "UNKNOWN_QUALIFIER",
}

ModelQualifierType = {
    0: "BQM_IS",
    1: "BQM_IS_DESCRIBED_BY",
    2: "BQM_IS_DERIVED_FROM",
    3: "BQM_IS_INSTANCE_OF",
    4: "BQM_HAS_INSTANCE",
    5: "BQM_UNKNOWN",
}

BiologicalQualifierType = {
    0: "BQB_IS",
    1: "BQB_HAS_PART",
    2: "BQB_IS_PART_OF",
    3: "BQB_IS_VERSION_OF",
    4: "BQB_HAS_VERSION",
    5: "BQB_IS_HOMOLOG_TO",
    6: "BQB_IS_DESCRIBED_BY",
    7: "BQB_IS_ENCODED_BY",
    8: "BQB_ENCODES",
    9: "BQB_OCCURS_IN",
    10: "BQB_HAS_PROPERTY",
    11: "BQB_IS_PROPERTY_OF",
    12: "BQB_HAS_TAXON",
    13: "BQB_UNKNOWN",
}


class BQM(Enum):
    """MIRIAM model qualifier."""

    IS = "BQM_IS"
    IS_DESCRIBED_BY = "BQM_IS_DESCRIBED_BY"
    IS_DERIVED_FROM = "BQM_IS_DERIVED_FROM"
    IS_INSTANCE_OF = "BQM_IS_INSTANCE_OF"
    HAS_INSTANCE = "BQM_HAS_INSTANCE"
    UNKNOWN = "BQM_UNKNOWN"


class BQB(Enum):
    """MIRIAM biological qualifier."""

    IS = "BQB_IS"
    HAS_PART = "BQB_HAS_PART"
    IS_PART_OF = "BQB_IS_PART_OF"
    IS_VERSION_OF = "BQB_IS_VERSION_OF"
    HAS_VERSION = "BQB_HAS_VERSION"
    IS_HOMOLOG_TO = "BQB_IS_HOMOLOG_TO"
    IS_DESCRIBED_BY = "BQB_IS_DESCRIBED_BY"
    IS_ENCODED_BY = "BQB_IS_ENCODED_BY"
    ENCODES = "BQB_ENCODES"
    OCCURS_IN = "BQB_OCCURS_IN"
    HAS_PROPERTY = "BQB_HAS_PROPERTY"
    IS_PROPERTY_OF = "BQB_IS_PROPERTY_OF"
    HAS_TAXON = "BQB_HAS_TAXON"
    UNKNOWN = "BQB_UNKNOWN"


def load_miriam() -> Dict[str, Any]:
    """Load miriam registry file.

    Provides information on the identifiers.org collections.

    :return: dictionary with registry informaiton
    """
    f_miriam = RESOURCES_DIR / "metadata" / "IdentifiersOrg-Registry.json"
    with open(f_miriam) as fp:
        d = json.load(fp)  # type: Dict[str, Any]

    return d


MIRIAM_COLLECTION = load_miriam()

# additional ontologies not in miriam
MIRIAM_COLLECTION["cmo"] = {
    "id": "cmo",
    "pattern": r"^CMO:\d+$",
    "name": "Chemical methods ontology",
    "namespace": "cmo",
    "definition": "Morphological and physiological measurement records "
    "generated from clinical and model "
    "organism research and health programs.",
}
MIRIAM_COLLECTION["chmo"] = {
    "id": "chmo",
    "pattern": r"^CHMO:\d+$",
    "name": "Chemical methods ontology",
    "namespace": "chmo",
    "definition": "CHMO, the chemical methods ontology",
}
MIRIAM_COLLECTION["vto"] = {
    "id": "vto",
    "pattern": r"^VTO:\d+$",
    "name": "Vertebrate Taxonomy Ontology",
    "namespace": "vto",
    "definition": "VTO Vertebrate Taxonomy Ontology",
}
MIRIAM_COLLECTION["opmi"] = {
    "id": "opmi",
    "pattern": r"^OPMI:\d+$",
    "name": "Ontology of Precision Medicine and Investigation",
    "namespace": "opmi",
    "definition": "OPMI: Ontology of Precision Medicine and Investigation",
}
MIRIAM_COLLECTION["mondo"] = {
    "id": "mondo",
    "pattern": r"^MONDO:\d+$",
    "name": "MONDO",
    "namespace": "mondo",
    "definition": "MONDO",
}
MIRIAM_COLLECTION["sio"] = {
    "id": "sio",
    "pattern": r"^SIO:\d+$",
    "name": "SIO",
    "namespace": "sio",
    "definition": "Semanticscience Integrated Ontology",
}
MIRIAM_COLLECTION["atol"] = {
    "id": "atol",
    "pattern": r"^ATOL:\d+$",
    "name": "ATOL",
    "namespace": "atol",
    "definition": "Animal Trait Ontology for Livestock",
}
MIRIAM_COLLECTION["nbo"] = {
    "id": "nbo",
    "pattern": r"^NBO:\d+$",
    "name": "NBO",
    "namespace": "nbo",
    "definition": "Neuro Behavior Ontology",
}
MIRIAM_COLLECTION["omim"] = {
    "id": "omim",
    "pattern": r"^MI:\d+$",
    "name": "OMIM",
    "namespace": "omim",
    "definition": "Molecular Interactions Controlled Vocabulary",
}
MIRIAM_COLLECTION["brenda.ligand"] = {
    "id": "brenda.ligand",
    "pattern": r"^\d+$",
    "name": "BRENDA Ligand",
    "namespace": "brenda.ligand",
    "definition": "BRENDA Ligand Information",
}
MIRIAM_COLLECTION["metabolights.compound"] = {
    "id": "metabolights.compound",
    "pattern": r"^MTBLC\d+$",
    "name": "Metabolights compound",
    "namespace": "metabolights compound",
    "definition": "Metabolights Compound",
}
