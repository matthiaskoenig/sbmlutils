"""
Validating DFBA files against the guidelines & rules.
"""
from __future__ import print_function, division, absolute_import
from sbmlutils.dfba.model import DFBAModel


def validate_dfba(sbml_path):
    """ Validate given DFBA model against specification
    
    :param sbml_path: path to top model.
    :return: 
    """
    validator = DFBAValidator.from_sbmlpath(sbml_path=sbml_path)
    return validator.validate()


class DFBAValidator(object):
    """ Simulator class to dynamic flux balance models (DFBA). """

    def __init__(self, dfba_model):
        """ Create validator with the top level SBML file.

        :param top_level_path: absolute path of top level SBML file
        :param output_directory: directory where output files are written
        """
        self.dfba_model = dfba_model

    @staticmethod
    def from_sbmlpath(sbml_path):
        """ Create validator with the top level SBML file.
        
        :param sbml_path: path to top model file. 
        :return: 
        """
        dfba_model = DFBAModel(sbml_path)
        return DFBAValidator(dfba_model)

    def validate(self):
        print("-" * 80)
        print("VALIDATION:")
        print("-" * 80)
        print(self.dfba_model)


