from __future__ import print_function, absolute_import

import unittest
import os
import shutil
import tempfile


from sbmlutils.dfba.utils import versioned_directory

from sbmlutils.dfba.toy import toysettings
from sbmlutils.dfba.toy import model_factory as toyfactory
from sbmlutils.dfba.toy import simulate as toysimulate

from sbmlutils.dfba.diauxic_growth import dgsettings
from sbmlutils.dfba.diauxic_growth import model_factory as dgfactory
from sbmlutils.dfba.diauxic_growth import simulate as dgsimulate


# no backend for testing, must be imported before pyplot
import matplotlib
matplotlib.use('Agg')


class DFBATestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def file_exists(self, directory, filename):
        """ Check if file with filename was generated in the test_dir.

        :param filename:
        :return:
        """
        path = os.path.join(directory, filename)
        print('Check file path:', path)
        self.assertTrue(os.path.exists(path))

    def test_toy_creation(self):
        directory = toyfactory.create_model(output_dir=self.test_dir)
        print(os.listdir(self.test_dir))

        self.file_exists(directory, toysettings.fba_file)
        self.file_exists(directory, toysettings.bounds_file)
        self.file_exists(directory, toysettings.update_file)
        self.file_exists(directory, toysettings.top_file)
        self.file_exists(directory, toysettings.flattened_file)

    def test_diauxic_creation(self):
        directory = dgfactory.create_model(output_dir=self.test_dir)

        print(os.listdir(self.test_dir))

        self.file_exists(directory, dgsettings.fba_file)
        self.file_exists(directory, dgsettings.bounds_file)
        self.file_exists(directory, dgsettings.update_file)
        self.file_exists(directory, dgsettings.top_file)
        self.file_exists(directory, dgsettings.flattened_file)

    def test_toy_simulation(self):

        toyfactory.create_model(self.test_dir)
        sbml_path = os.path.join(versioned_directory(self.test_dir, toyfactory.version),
                                 toysettings.top_file)
        print(sbml_path)
        toysimulate.simulate_toy(sbml_path, self.test_dir, dts=[1.0], figures=False)

        # self.file_exists("reactions.png")
        # self.file_exists("species.png")
        # self.file_exists("simulation.csv")

    def test_diauxic_simulation(self):

        dgfactory.create_model(self.test_dir)
        sbml_path = os.path.join(versioned_directory(self.test_dir, dgfactory.version),
                                 dgsettings.top_file)
        print(sbml_path)
        dgsimulate.simulate_diauxic_growth(sbml_path, self.test_dir, dts=[0.01], figures=False)

        # self.file_exists("reactions.png")
        # self.file_exists("species.png")
        # self.file_exists("simulation.csv")

if __name__ == '__main__':
    unittest.main()
