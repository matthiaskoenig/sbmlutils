"""
Test cell model creation.

Reading of model dictionaries from given python files
and creation of the SBML.
"""

import unittest
from sbmlutils.modelcreator.creator import CoreModel, Preprocess


class TestCellModel(unittest.TestCase):

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
