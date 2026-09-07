"""cobrapy based helper methods.

cobrapy is not a dependency of sbmlutils, it is the optional `cobra` extra
(`pip install sbmlutils[cobra]`). `cobra` is `None` when it is not installed,
which is what the tests of this module skip on.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

# cobrapy is the optional `cobra` extra, so it is not installed in the
# environment the type check runs in
if TYPE_CHECKING:
    import cobra  # ty: ignore[unresolved-import]
else:
    try:
        import cobra
    except ImportError:
        cobra = None

logger = logging.getLogger(__name__)


def read_cobra_model(sbml_path: Path) -> "cobra.core.Model":
    """Load cobra model from path.

    Sets default flux bounds to allow loading and changes all boundaryConditions to
    False.

    :param sbml_path: str path
    :return: cobra model
    """
    return cobra.io.read_sbml_model(str(sbml_path))


def cobra_reaction_info(cobra_model: "cobra.core.Model") -> pd.DataFrame:
    """Create data frame with bound and objective information.

    :param cobra_model:
    :return: pandas DataFrame
    """
    rids: list[str] = [r.id for r in cobra_model.reactions]
    df = pd.DataFrame(
        data=None,
        index=pd.Index(rids),
        columns=pd.Index(
            [
                "lb",
                "ub",
                "reversibility",
                "boundary",
                "objective_coefficient",
                "forward_variable",
                "reverse_variable",
            ]
        ),
    )
    for rid in rids:
        r = cobra_model.reactions.get_by_id(rid)
        df.loc[rid] = [
            r.lower_bound,
            r.upper_bound,
            r.reversibility,
            r.boundary,
            r.objective_coefficient,
            r.forward_variable,
            r.reverse_variable,
        ]
    return df


def check_mass_balance(sbml_path: Path) -> dict[str, Any]:
    """Check mass and charge balance of the model.

    Args:
        sbml_path: path of the SBML model

    Returns:
        The unbalanced reactions, keyed by reaction id.
    """
    model = read_cobra_model(sbml_path)
    mbs: dict[str, Any] = {}
    for r in model.reactions:
        mb = r.check_mass_balance()
        if len(mb) > 0:
            logger.warning("Reaction '%s' is unbalanced: %s (%s)", r.id, mb, r.reaction)
            mbs[r.id] = mb
    return mbs
