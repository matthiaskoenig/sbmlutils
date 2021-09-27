"""sbmlutils - Python utilities for SBML."""
from pathlib import Path

__author__ = "Matthias Koenig"
__version__ = "0.5.3"


from sbmlutils.utils import show_versions


program_name = "sbmlutils"
RESOURCES_DIR = Path(__file__).parent / "resources"
