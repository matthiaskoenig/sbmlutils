from sbmlutils.io.sbml import validate_sbml
from sbmlutils.tests import DEMO_SBML, GALACTOSE_SINGLECELL_SBML, BASIC_SBML, VDP_SBML

SBML_FILES = [
    {'path': DEMO_SBML, 'ucheck': True, 'N': 0},
    {'path': GALACTOSE_SINGLECELL_SBML, 'ucheck': True, 'N': 0},
    {'path': BASIC_SBML, 'ucheck': True, 'N': 0},
    {'path': VDP_SBML, 'ucheck': False, 'N': 0},
]


def _validate_file(sbmlpath, units_consistency=True, Nall=0):
    """ Validate given SBML file.

    Helper function called by the other tests.

    :param sbmlpath:
    :param units_consistency:
    :return:
    """
    _Nall, _Nerr, _Nwarn = validate_sbml(sbmlpath, units_consistency=units_consistency)
    assert Nall is not None
    assert Nall == _Nall


def test_files():
    for d in SBML_FILES:
        _validate_file(sbmlpath=d['path'], units_consistency=d['ucheck'], Nall=d['N'])
