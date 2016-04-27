# -*- coding=utf-8 -*-
"""
Create SBML/antimony files for interpolation of datasets.


https://github.com/allyhume/SBMLDataTools
https://github.com/allyhume/SBMLDataTools.git

"""
import pandas as pd
import libsbml
import warnings

from sbmlutils.factory import *

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
      <div class="dc:rightsHolder">Copyright © 2016 sbmlutils.</div>
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


# available interpolation methods
INTERPOLATION_CONSTANT = "constant"
INTERPOLATION_LINEAR = "linear"
INTERPOLATION_CUBIC_SPLINE = "cubic spline"


class Interpolator(object):
    """ Interpolator class handles the interpolation of given data series

    Two data series and the type of interpolation are provided.
    """

    def __init__(self, x, y, z=None, method=INTERPOLATION_CONSTANT):
        self.x = x
        self.y = y
        self.z = z
        self.method = method

    def __str__(self):
        s = "--------------------------\n" \
            "Interpolator<{}>\n" \
            "--------------------------\n" \
            "{}\n" \
            "{}\n" \
            "formula:\n {}\n".format(self.method, self.x, self.y, self.formula())
        return s

    @property
    def xid(self):
        return self.x.name

    @property
    def yid(self):
        return self.y.name

    @property
    def zid(self):
        return self.z.name

    def formula(self):
        """"""
        if self.method is INTERPOLATION_CONSTANT:
            return Interpolator.formula_constant(self.x, self.y)
        elif self.method is INTERPOLATION_LINEAR:
            return Interpolator.formula_linear(self.x, self.y)
        if self.method is INTERPOLATION_CUBIC_SPLINE:
            return Interpolator.formula_cubic_spline(self.x, self.y)

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
        return ',\n '.join(items)


class Interpolation(object):
    """ Creates SBML which interpolates the given data.

    The second to last components are interpolated against the first component.
    """

    def __init__(self, data, method="linear"):
        self.doc = None
        self.model = None
        self.data = data
        self.method = method
        self.interpolators = []

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
        if len(self.data.columns) < 2:
            warnings.warn("Interpolation data has <2 columns. At least 2 columns required.")

        # at least 3 rows required
        if len(self.data) < 3:
            warnings.warn("Interpolation data <3 rows. At least 3 rows required.")

        # first column has to be ascending (times)
        def is_sorted(df, colname):
            return pd.Index(df[colname]).is_monotonic

        if not is_sorted(self.data, colname=self.data.columns[0]):
            warnings.warn("First column should contain ascending values.")
            self.data = self.data.sort_values(by=self.data.columns[0])

    @staticmethod
    def from_csv(csv_file, method="linear", sep=","):
        """ Interpolation object from csv file.

        :param csv_file:
        :type csv_file:
        :param method:
        :type method:
        :param sep:
        :type sep:
        :return:
        :rtype:
        """
        data = pd.read_csv(csv_file, sep=sep)
        return Interpolation(data=data, method=method)

    @staticmethod
    def from_tsv(tsv_file, method="linear"):
        """ Interpolation object from tsv file. """
        return Interpolation.from_csv(csv_file=tsv_file, method=method, sep="\t")

    # --- SBML & Interpolation --------------------

    def write_sbml(self, sbml_out):
        """ Write the SBML file.

        First create clean SBML file.

        :param sbml_out:
        :type sbml_out:
        :return:
        :rtype:
        """
        self._create_sbml()
        libsbml.writeSBMLToFile(self.doc, sbml_out)

    def _create_sbml(self):
        """ Create the SBMLDocument.

        :return:
        :rtype:
        """
        self._init_sbml_model()
        self.interpolators = Interpolation.create_interpolators(self.data, self.method)
        for interpolator in self.interpolators:
            Interpolation.add_interpolator_to_model(interpolator, self.model)

        # TODO: validation

    def _init_sbml_model(self):
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
        model.setId("Interpolation_{}".format(self.method))
        model.setName("Interpolation_{}".format(self.method))
        self.model = model

    @staticmethod
    def create_interpolators(data, method):
        """ Creates all interpolators for the given data set.

        The columns 1, ... (Ncol-1) are interpolated against
        column 0.
        """
        interpolators = []
        columns = data.columns
        time = data[columns[0]]
        for k in range(1, len(columns)):
            interpolator = Interpolator(x=time,
                                        y=data[columns[k]],
                                        method=method)
            interpolators.append(interpolator)
        return interpolators

    @staticmethod
    def add_interpolator_to_model(interpolator, model):
        """ The parameters, formulas and rules have to be added to the SBML model.

        :param interpolator:
        :type interpolator:
        :return:
        :rtype:
        """

        # create parameter
        pid = interpolator.yid

        # if parameter exists remove it
        if model.getParameter(pid):
            warnings.warn("Model contains parameter: {}. Parameter is removed.".format(pid))
            model.removeParameter(pid)

        # if assignment rule exists remove it
        for rule in model.getListOfRules():
            if rule.isAssignment():
                if rule.getVariable() == pid:
                    model.removeRule(rule)
                    break

        p = model.createParameter()
        p.setId(pid)
        p.setName(pid)
        p.setConstant(False)

        # create rule
        rule = model.createAssignmentRule()
        rule.setVariable(pid)
        formula = interpolator.formula()
        ast_node = libsbml.parseL3FormulaWithModel(formula, model)
        if ast_node is None:
            warnings.warn(libsbml.getLastParseL3Error())
        else:
            rule.setMath(ast_node)




    def _add_data_to_model(self):
        """
        Adds the data into the SBML model as a parameter
        with an assignment rule.
        """
        # TODO: implement
        pass

if __name__ == "__main__":
    from pandas import DataFrame
    x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
    z = [10.0, 5.0, 2.5, 1.25, 0.6, 0.3]
    data = DataFrame({'x': x, 'y': y, 'z': z})
    # print(data)
    # interpolator = Interpolator(data['x'], data['y'], method=INTERPOLATION_CONSTANT)
    # print(interpolator)

    interpolation = Interpolation(data=data, method=INTERPOLATION_CONSTANT)
    sbml_out = "test_constant.xml"
    print("Writing SBML")
    interpolation.write_sbml(sbml_out)

    # what was written in the file
    doc = libsbml.readSBMLFromFile(sbml_out)
    print(libsbml.writeSBMLToString(doc))


