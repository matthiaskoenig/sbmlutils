"""
Validating DFBA files against the guidelines & rules.
"""
from __future__ import print_function, division

from sbmlutils.dfba.model import DFBAModel


class DFBAValidator(object):
    """ Simulator class to dynamic flux balance models (DFBA). """

    def __init__(self, dfba_model):
        """ Create validator with the top level SBML file.

        :param top_level_path: absolute path of top level SBML file
        :param output_directory: directory where output files are written
        """
        self.dfba_model = dfba_model

    @staticmethod
    def from_sbmlpath(sbml_top_path):
        """ Create validator with the top level SBML file. """
        dfba_model = DFBAModel(sbml_top_path)
        return DFBAValidator(dfba_model)
