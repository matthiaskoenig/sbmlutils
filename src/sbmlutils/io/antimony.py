"""Conversion of SBML to antimony.

The inverse direction, antimony to SBML, lives in `sbmlutils.parser`, which
builds on `sbmlutils.factory` and can therefore not be imported here.
"""

import logging
from pathlib import Path

import antimony

logger = logging.getLogger(__name__)


def sbml_to_antimony(source: Path | str) -> str:
    """Convert an SBML model to its antimony serialization.

    Args:
        source: Path to an SBML file or SBML string.

    Returns:
        The antimony string of the model.

    Raises:
        ValueError: If antimony cannot load the SBML.
    """
    antimony.clearPreviousLoads()
    status: int
    if isinstance(source, Path):
        status = antimony.loadSBMLFile(str(source))
    elif source.strip().startswith("<"):
        status = antimony.loadSBMLString(source)
    else:
        status = antimony.loadSBMLFile(source)

    if status == -1:
        error: str = antimony.getLastError()
        logger.error("Antimony could not load the SBML: %s", error)
        raise ValueError(f"Antimony could not load the SBML: {error}")

    return str(antimony.getAntimonyString(None))
