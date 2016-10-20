import unittest
import os
import tempfile
import shutil
import matplotlib
# no backend for testing, must be imported before pyplot
matplotlib.use('Agg')
from sbmlutils.dfba.toymodel import run_all
from sbmlutils.dfba.toymodel import toysettings


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

    def test_toy_model_creation(self):
        """ Creates all SBML files and runs the DFBA simulation.

        :return:
        """
        run_all.create_toy_model(directory=self.test_dir)
        print(os.listdir(self.test_dir))

        self.file_exists(toysettings.fba_file)
        self.file_exists(toysettings.ode_bounds_file)
        self.file_exists(toysettings.ode_model_file)
        self.file_exists(toysettings.ode_update_file)
        self.file_exists(toysettings.top_level_file)
        self.file_exists(toysettings.flattened_file)

    def test_toy_model_simulation(self):
        """

        :return:
        """
        run_all.create_toy_model(self.test_dir)
        run_all.simulate_model(self.test_dir, tend=50.0, steps=20)

        self.file_exists("reactions.png")
        self.file_exists("species.png")
        self.file_exists("simulation.csv")


if __name__ == '__main__':
    unittest.main()
