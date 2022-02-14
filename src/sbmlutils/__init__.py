"""sbmlutils - Python utilities for SBML."""
from pathlib import Path

__author__ = "Matthias Koenig"
__version__ = "0.6.4"


from sbmlutils.utils import show_versions


program_name = "sbmlutils"

RESOURCES_DIR = Path(__file__).parent / "resources"
EXAMPLES_DIR: Path = RESOURCES_DIR / "examples"
