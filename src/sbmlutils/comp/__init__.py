"""Package for SBML comp."""
from .comp import (
    # Port,
    create_ExternalModelDefinition,
    create_ports,
)
from .flatten import flatten_sbml, flatten_sbml_doc
