"""Package for SBML comp."""

from .comp import (
    create_ExternalModelDefinition,
    create_ports,
)
from .flatten import flatten_sbml as flatten_sbml, flatten_sbml_doc

__all__ = [
    "flatten_sbml",
    "flatten_sbml_doc",
    "create_ExternalModelDefinition",
    "create_ports",
]
