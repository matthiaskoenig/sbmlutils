"""
Create SBML/antimony files for interpolation of datasets.
"""

INTERPOLATION_LINEAR = "linear"
INTERPOLATION_CUBIC_SPLINE = "cubic spline"

class Interpolation(object):
    """ Creates SBML which interpolates the given data.

    The second to last components are interpolated against the first component.
    If the first component is time, it is


    """


    def __init__(self, data, interpolation="linear", xIsTime=False):
        self.data = data
        self.interpolation = interpolation
        self.xIsTime

    def create_sbml(self):
        """ Writes an SBML file of the interpolation.

        :return:
        :rtype:
        """



