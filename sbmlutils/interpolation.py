"""
Create SBML/antimony files for interpolation of datasets.


https://github.com/allyhume/SBMLDataTools
https://github.com/allyhume/SBMLDataTools.git

"""
import pandas as pd
import libsbml
import warnings


INTERPOLATION_LINEAR = "linear"
INTERPOLATION_CUBIC_SPLINE = "cubic spline"



class Interpolator(object):

    def __init__(self, data, interpolation):
        self.data = data
        self.functions = None
        self.functionConditions = None
        self.interpolation = interpolation


    @staticmethod
    def formula_constant(col1, col2):
        """ Constant value between data points
        piecewise x1, y1, [x2, y2, ][...][z]
        A piecewise function: if (y1), x1.Otherwise, if (y2), x2, etc.Otherwise, z.
        :return:
        :rtype:
        """
        items = []

        for k in range(len(col1)-1):
            s = 'time >= {} && time <= {}, {}'.format(col1.ix[k], col1.ix[k+1], col2.ix[k])
            items.append(s)
        items.append('0.0')
        return ', '.join(items)

    def __str__(self):
        return Interpolator.formula_constant(self.data[0], self.data[1])



class Interpolation(object):
    """ Creates SBML which interpolates the given data.

    The second to last components are interpolated against the first component.
    If the first component is time, it is


    """


    def from_csv(self, csv_file, interpolation="linear"):
        data = pd.read_csv(csv_file, sep=sep)
        return Interpolation(data=data, interpolation=interpolation)

    def __init__(self, data, interpolation="linear", xIsTime=False):
        self.doc = libsbml.SBMLDocument()
        self.data = data
        self.interpolation = interpolation
        self.xIsTime

        self.validate_data()


    def validate_data(self):
        """ Validates the input data

        * The data is expected to have at least 2 columns.
        * The data is expected to have at least three data rows.
        * The first column should be in ascending order.

        :return:
        :rtype:
        """
        # more than 1 column required
        if len(self.data.columns)<2:
            warnings.warn("Interpolation data has <2 columns. At least 2 columns required.")

        # at least 3 rows required
        if len(self.data)<3:
            warnings.warn("Interpolation data <3 rows. At least 3 rows required.")

        # first column has to be ascending (times)
        def is_sorted(df, colname):
            return pd.Index(df[colname]).is_monotonic
        if not is_sorted(self.data, colname=self.data.columns[0]):
            warnings.warn("First column should contain ascending values.")
            self.data = self.data.sort_values(by=self.data.columns[0])


    def add_data_to_doc(self):
        """
        Adds the data into the SBML model as a parameter
        with an assignment rule.
        """
        pass


    def create_sbml(self):
        """ Writes an SBML file of the interpolation.
        Time is column 0, process each other column in turn

        :return:
        :rtype:
        """

if __name__ == "__main__":
    from pandas import DataFrame
    x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
    self.data = DataFrame(data=(x, y), columns=('x', 'y'))