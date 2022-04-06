"""cobrapy based helper methods."""
from pathlib import Path
from typing import Dict

import pandas as pd

from sbmlutils import log


try:
    import cobra
except ImportError:
    cobra = None

logger = log.get_logger(__name__)


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
    rids = [r.id for r in cobra_model.reactions]
    df = pd.DataFrame(
        data=None,
        index=rids,
        columns=[
            "lb",
            "ub",
            "reversibility",
            "boundary",
            "objective_coefficient",
            "forward_variable",
            "reverse_variable",
        ],
    )
    for rid in rids:
        r = cobra_model.reactions.get_by_sid(rid)
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


def check_mass_balance(sbml_path: Path) -> Dict:
    """Check mass and charge balance of the model.

    :param sbml_path: Path to SBML file
    :return: Dict of unbalanced reactions
    """
    model = read_cobra_model(sbml_path)
    mbs = dict()
    for r in model.reactions:
        mb = r.check_mass_balance()
        if len(mb) > 0:
            logger.warning(r.id, mb, r.reaction)
            mbs[r.getId()] = mb
    return mbs
