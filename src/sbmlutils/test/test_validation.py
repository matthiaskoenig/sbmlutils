from pathlib import Path

from sbmlutils.io.sbml import validate_sbml
from sbmlutils.test import BASIC_SBML, DEMO_SBML, GALACTOSE_SINGLECELL_SBML, VDP_SBML


SBML_FILES = [
    {"path": DEMO_SBML, "ucheck": True, "N": 0},
    {"path": GALACTOSE_SINGLECELL_SBML, "ucheck": True, "N": 0},
    {"path": BASIC_SBML, "ucheck": True, "N": 0},
    {"path": VDP_SBML, "ucheck": False, "N": 0},
]


def _validate_file(
    sbmlpath: Path, units_consistency: bool = True, Nall: int = 0
) -> None:
    """Validate given SBML file.

    Helper function called by the other tests.

    :param sbmlpath:
    :param units_consistency:
    :return:
    """
    v_results = validate_sbml(sbmlpath, units_consistency=units_consistency)
    assert v_results
    assert Nall == v_results.all_count


def test_files() -> None:
    for d in SBML_FILES:
        _validate_file(sbmlpath=d["path"], units_consistency=d["ucheck"], Nall=d["N"])  # type: ignore
