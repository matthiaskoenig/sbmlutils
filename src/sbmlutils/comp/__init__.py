"""Package for SBML comp."""
from .comp import (
    PORT_TYPE_INPUT,
    PORT_TYPE_OUTPUT,
    PORT_TYPE_PORT,
    # Port,
    Deletion,
    ExternalModelDefinition,
    ReplacedElement,
    ReplacedBy,
    Submodel,
    create_ExternalModelDefinition,
    create_ports,
)
from .flatten import flatten_sbml, flatten_sbml_doc
