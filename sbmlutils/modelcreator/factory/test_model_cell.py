"""
Test model_cell.
"""

import unittest
from sbmlutils.modelcreator import CellModel


class TestCellModel(unittest.TestCase):

    def test_demo(self):
        cell_dict = CellModel.createCellDict(['sbmlutils.examples.models.demo'])
        cell_model = CellModel(cell_dict=cell_dict)
        cell_model.create_sbml()
    
    def test_galactose(self):
        cell_dict = CellModel.createCellDict(['sbmlutils.examples.models.hepatocyte',
                                         'sbmlutils.examples.models.galactose'])
        cell_model = CellModel(cell_dict=cell_dict)
        cell_model.create_sbml()

if __name__ == "__main__":
    unittest.main()
