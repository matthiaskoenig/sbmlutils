"""
Test the DFBA validator.
"""
from __future__ import print_function, absolute_import

import unittest
import pytest
import os

from sbmlutils.dfba import utils
from sbmlutils.dfba.toy import settings as toysettings
from sbmlutils.dfba.toy import model_factory as toyfactory
from sbmlutils.dfba.simulator import simulate_dfba

from sbmlutils.dfba import validator


class ValidationTest(unittest.TestCase):
    def test_validate_toy(self):
        """ Validate the toy model. """
        sbml_path = os.path.join(utils.versioned_directory(toysettings.out_dir, toyfactory.version),
                             toysettings.top_file)
        print(sbml_path)


        # run simulation with the top model
        # df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=50, dt=5.0)

        validator.validate_dfba(sbml_path)
        assert False





if __name__ == "__main__":
    unittest.main()
