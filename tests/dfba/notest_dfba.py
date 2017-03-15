import os
import shutil
import tempfile
import unittest

import matplotlib

# no backend for testing, must be imported before pyplot
matplotlib.use('Agg')

from src.sbmlutils.dfba.toy import toysettings
from src.sbmlutils.dfba.toy import model_factory as toyfactory
from src.sbmlutils.dfba.toy import simulate as toysimulate

from src.sbmlutils.dfba.diauxic_growth import dgsettings
from src.sbmlutils.dfba import model_factory as dgfactory


class DFBATestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def file_exists(self, filename):
        """ Check if file with filename was generated in the test_dir.

        :param filename:
        :return:
        """
        self.assertTrue(
            os.path.exists(os.path.join(self.test_dir, filename)))

    def test_toy_creation(self):
        """ Creates all SBML files and runs the DFBA simulation.

        :return:
        """
        toyfactory.create_model(out_dir=self.test_dir)
        print(os.listdir(self.test_dir))

        self.file_exists(toysettings.fba_file)
        self.file_exists(toysettings.bounds_file)
        self.file_exists(toysettings.update_file)
        self.file_exists(toysettings.top_file)
        self.file_exists(toysettings.flattened_file)

    def test_toy_simulation(self):
        """

        :return:
        """
        toyfactory.create_model(self.test_dir)
        toysimulate.simulate_model(self.test_dir, tend=50.0, steps=20)

        self.file_exists("reactions.png")
        self.file_exists("species.png")
        self.file_exists("simulation.csv")

    def test_diauxic_creation(self):
        """ Creates all SBML files and runs the DFBA simulation.

        :return:
        """
        dgfactory.create_model(directory=self.test_dir)
        print(os.listdir(self.test_dir))

        self.file_exists(dgsettings.fba_file)
        self.file_exists(dgsettings.bounds_file)
        self.file_exists(dgsettings.update_file)
        self.file_exists(dgsettings.top_file)
        self.file_exists(dgsettings.flattened_file)

if __name__ == '__main__':
    unittest.main()
