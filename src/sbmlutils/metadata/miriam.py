"""Helper module for working with MIRIAM metadata."""

from pymetadata.identifiers.miriam import BQB, BQM


__all__ = [
    "BQM",
    "BQB",
]

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
