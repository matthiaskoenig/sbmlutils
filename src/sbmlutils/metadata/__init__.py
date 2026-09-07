"""Metadata and annotation of SBML models.

The annotation data structures themselves are provided by
[pymetadata](https://github.com/matthiaskoenig/pymetadata): the MIRIAM
qualifiers `BQB` and `BQM` and the terms of the systems biology ontology `SBO`
are re-exported here, so that a model definition only has to import from
`sbmlutils`.
"""

from pymetadata.core.miriam import BQB, BQM
from pymetadata.ontologies import SBO

__all__ = [
    "BQB",
    "BQM",
    "SBO",
]
