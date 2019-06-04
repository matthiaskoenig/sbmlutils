"""
Helper class to work with the MIRIAM resources.
"""
from enum import Enum

# TODO: parse the latest miriam information and use for annotation checking

IDENTIFIERS_ORG_PREFIX = "https://identifiers.org"

_collections = [
    ["sbo", "Systems Biology Ontology", "^SBO:\d{7}$"],
    ["bto", "Brenda Tissue Ontology", "^BTO:\d{7}$"],
    ["chebi", "ChEBI", "^CHEBI:\d+$"],
    ["ec-code", "Enzyme Nomenclature", "^\d+\.-\.-\.-|\d+\.\d+\.-\.-|\d+\.\d+\.\d+\.-|\d+\.\d+\.\d+\.(n)?\d+$"],
    ["fma", "Foundational Model of Anatomy Ontology", "^FMA:\d+$"],
    ["go", "Gene Ontology", "^GO:\d{7}$"],
    ["kegg.compound", "KEGG Compound", "^C\d+$"],
    ["kegg.pathway", "KEGG Pathway", "^\w{2,4}\d{5}$"],
    ["kegg.reaction", "KEGG Reaction", "^R\d+$"],
    ["omim", "OMIM", "^[*#+%^]?\d{6}$"],
    ["pubmed", "PubMed", "^\d+$"],
    ["pw", "Pathway Ontology", "^PW:\d{7}$"],
    ["reactome", "Reactome", "(^(REACTOME:)?R-[A-Z]{3}-[0-9]+(-[0-9]+)?$)|(^REACT_\d+$)"],
    ["rhea", "Rhea", "^\d{5}$"],
    ["sabiork.kineticrecord", "SABIO-RK Kinetic Record", "^\d+$"],
    ["smpdb", "Small Molecule Pathway Database", "^SMP\d{5}$"],
    ["taxonomy", "Taxonomy", "^\d+$"],
    ["tcdb", "Transport Classification Database", "^\d+\.[A-Z]\.\d+\.\d+\.\d+$"],
    ["uberon", "UBERON", "^UBERON\:\d+$"],
    ["uniprot", "UniProt Knowledgebase",
     "^([A-N,R-Z][0-9]([A-Z][A-Z, 0-9][A-Z, 0-9][0-9]){1,2})|([O,P,Q][0-9]"
     "[A-Z, 0-9][A-Z, 0-9][A-Z, 0-9][0-9])(\.\d+)?$"],
    ["uo", "Ontology of standardized units", "^UO:\d{7}?"],
]

########################################################################
# Qualifier
########################################################################
# from libsbmlconstants
# TODO: use ModelQualifierType_toString

QualifierType = {
    0: "MODEL_QUALIFIER",
    1: "BIOLOGICAL_QUALIFIER",
    2: "UNKNOWN_QUALIFIER"
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
    IS = "BQM_IS"
    IS_DESCRIBED_BY = "BQM_IS_DESCRIBED_BY"
    IS_DERIVED_FROM = "BQM_IS_DERIVED_FROM"
    IS_INSTANCE_OF = "BQM_IS_INSTANCE_OF"
    HAS_INSTANCE = "BQM_HAS_INSTANCE"
    UNKNOWN = "BQM_UNKNOWN"


class BQB(Enum):
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


__all__ = [
    'BQM',
    'BQB',
]
