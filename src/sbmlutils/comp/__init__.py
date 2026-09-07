"""Package for SBML comp."""

from .comp import (
    create_ExternalModelDefinition,
    create_ports,
)
from .flatten import flatten_sbml as flatten_sbml
from .flatten import flatten_sbml_doc

__all__ = [
    "create_ExternalModelDefinition",
    "create_ports",
    "flatten_sbml",
    "flatten_sbml_doc",
]
