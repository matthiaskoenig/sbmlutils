"""
Test cell model creation.

Reading of model dictionaries from given python files
and creation of the SBML.
"""

import unittest
from sbmlutils.modelcreator.creator import CoreModel, Preprocess

# test model creation
from sbmlutils.examples.models.assignment import factory as assignment_factory
from sbmlutils.examples.models.basic import factory as basic_factory
from sbmlutils.examples.models.demo import factory as demo_factory
from sbmlutils.examples.models.glucose import factory as glucose_factory


class TestCellModel(unittest.TestCase):
    def test_create_assignment(self):
        """
        Create assignment model.
        :return:
        """
        assignment_factory.create()

    def test_create_basic(self):
        """
        Create basic model.
        :return:
        """
        basic_factory.create()

    def test_create_demo(self):
        """
        Create demo model.
        :return:
        """
        demo_factory.create()

    def test_create_glucose(self):
        """
        Create glucose model.
        :return:
        """
        glucose_factory.create()

    def test_demo(self):
        """
        Create demo model.
        :return:
        """
        model_dict = Preprocess.dict_from_modules(['sbmlutils.examples.models.demo.Cell'])
        cell_model = CoreModel.from_dict(model_dict)
        cell_model.create_sbml()

    def test_galactose(self):
        """
        Create galactose model.
        :return:
        """
        model_dict = Preprocess.dict_from_modules(
            [
                'sbmlutils.examples.models.hepatocyte',
                'sbmlutils.examples.models.galactose'
            ])

        cell_model = CoreModel.from_dict(model_dict);
        cell_model.create_sbml()


if __name__ == "__main__":
    unittest.main()
