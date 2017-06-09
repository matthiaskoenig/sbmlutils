"""
Test the DFBA validator.
"""
from __future__ import print_function, absolute_import

import os
import pytest

from sbmlutils.dfba import utils
from sbmlutils.dfba import validator
from sbmlutils.dfba.toy_wholecell import settings as toysettings
from sbmlutils.dfba.toy_wholecell import model_factory as toyfactory


@pytest.mark.skip(reason="validation currently not implemented")
def test_validate_toy(self):
    """ Validate the toy model. """
    sbml_path = os.path.join(utils.versioned_directory(toysettings.out_dir, toyfactory.version),
                         toysettings.top_file)
    print(sbml_path)

    # run simulation with the top model
    # df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=50, dt=5.0)

    validator.validate_dfba(sbml_path)
    assert False

