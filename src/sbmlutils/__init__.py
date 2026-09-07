"""sbmlutils - Python utilities for SBML."""

import logging
from pathlib import Path

# the package logs, it does not configure logging, see `sbmlutils.log`
logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Matthias König"
__version__ = "0.10.0"


program_name = "sbmlutils"

RESOURCES_DIR = Path(__file__).parent / "resources"
