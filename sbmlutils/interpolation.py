"""
Create SBML/antimony files for interpolation of datasets.


https://github.com/allyhume/SBMLDataTools
https://github.com/allyhume/SBMLDataTools.git

"""
import pandas as pd
import libsbml
import warnings


##########################################################################
# Model information
##########################################################################

notes = libsbml.XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Data interpolator</h1>
    <h2>Description</h2>
    <p>This is a SBML submodel for interpolation of spreadsheet data.</p>

    <div class="dc:publisher">This file has been produced by
      <a href="https://livermetabolism.com/contact.html" title="Matthias Koenig" target="_blank">Matthias Koenig</a>.
      </div>

    <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2016 Wholecell Consortium.</div>
      <div class="dc:license">
      <p>Redistribution and use of any part of this model, with or without modification, are permitted provided that
      the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions
              and the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of
              conditions and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>
        This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
             the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.</p>
      </div>
    </body>
""")


INTERPOLATION_CONSTANT = "constant"
INTERPOLATION_LINEAR = "linear"
INTERPOLATION_CUBIC_SPLINE = "cubic spline"


class Interpolator(object):

    def __init__(self, series1, series2, interpolation):
        self.series1 = series1
        self.series2 = series2
        self.interpolation = interpolation

    def formula(self):
        """"""

    @staticmethod
    def formula_cubic_spline(col1, col2):
        """ Formula for the cubic spline.

        This is more complicated and requires the coefficients
        from the spline interpolation.

        """
        # TODO: implement
        pass

    @staticmethod
    def formula_linear(col1, col2):
        # TODO: implement
        pass

    @staticmethod
    def formula_constant(col1, col2):
        """ Constant value between data points
        piecewise x1, y1, [x2, y2, ][...][z]
        A piecewise function: if (y1), x1.Otherwise, if (y2), x2, etc.Otherwise, z.
        :return:
        :rtype:
        """
        items = []

        for k in range(len(col1) - 1):
            s = 'time >= {} && time <= {}, {}'.format(col1.ix[k], col1.ix[k + 1], col2.ix[k])
            items.append(s)
        items.append('0.0')
        return ', '.join(items)



    def _add_data_to_model(self):
        """
        Adds the data into the SBML model as a parameter
        with an assignment rule.
        """
        pass


class Interpolation(object):
    """ Creates SBML which interpolates the given data.

    The second to last components are interpolated against the first component.
    If the first component is time, it is


    """

    def from_csv(self, csv_file, interpolation="linear"):
        data = pd.read_csv(csv_file, sep=sep)
        return Interpolation(data=data, interpolation=interpolation)

    def __init__(self, data, interpolation="linear", xIsTime=False):
        self.doc = None
        self.model = None
        self.data = data
        self.interpolation = interpolation
        self.interpolators = []
        self.xIsTime

        self.validate_data()


    def create_sbml(self, sbml_out):
        self.init_sbml_model()
        self.create_interpolators()
        libsbml.writeSBMLToFile(self.doc, sbml_out)


    def init_sbml_model(self):
        """ Initializes the SBML model.

        :return:
        :rtype:
        """
        sbmlns = libsbml.SBMLNamespaces(3, 1)
        sbmlns.addPackageNamespace("comp", 1)
        doc = libsbml.SBMLDocument(sbmlns)
        doc.setPackageRequired("comp", True)
        self.doc = doc
        model = doc.createModel()
        model.setNotes(notes)
        model.setId("Interpolation_{}".format(self.interpolation))
        model.setName("Interpolation_{}".format(self.interpolation))
        self.model = model

    def create_interpolators(self):
        columns = self.data.columns
        for k in range(len(columns)-1):



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



    def add_interpolation_to_sbml()


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
    data = DataFrame({'x': x, 'y': y})
    print(data)
    interpolator = Interpolator(data=data, interpolation=INTERPOLATION_CONSTANT)

    columns = data.columns
    formula = interpolator.formula_constant(data[columns[0]], data[columns[1]])
    print(formula)

