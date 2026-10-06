"""Drive a model with interpolated data, in place or through comp.

The functions of this module implement `Interpolation.drive`,
`Interpolation.drive_comp` and `Interpolation.assignment_rules` of
`sbmlutils.data.interpolation`, which document the behaviour.
"""

from __future__ import annotations

import logging

import libsbml

logger = logging.getLogger(__name__)


def check_sid(sid: str, what: str) -> None:
    """Check that a name used as an id is an SBML id.

    Args:
        sid: the name
        what: what the name is, for the message, e.g. "Column"

    Raises:
        ValueError: if the name is not an SBML id
    """
    if not libsbml.SyntaxChecker.isValidSBMLSId(sid):
        raise ValueError(f"{what} '{sid}' is not an SBML id.")
