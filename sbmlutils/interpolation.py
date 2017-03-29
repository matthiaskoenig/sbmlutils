# -*- coding=utf-8 -*-
"""
Create SBML/antimony files for interpolation of datasets.


https://github.com/allyhume/SBMLDataTools
https://github.com/allyhume/SBMLDataTools.git

"""
from __future__ import print_function, division

import os.path
import shutil
import tempfile
import warnings

import libsbml
import pandas as pd
from sbmlutils import validation

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
    def formula_cubic_spline(x, y):
        """ Formula for the cubic spline.

        This is more complicated and requires the coefficients
        from the spline interpolation.
        """
        # calculate spline coefficients
        coeffs = Interpolator.natural_spline_coeffs(x, y)

        # create piecewise terms
        items = []
        for k in range(len(x) - 1):
            x1 = x.ix[k]
            x2 = x.ix[k + 1]
            (a, b, c, d) = coeffs[k]
            formula = '{d}*(time-{x1})^3 + {c}*(time-{x1})^2 + {b}*(time-{x1}) + {a}'.format(a=a, b=b, c=c, d=d, x1=x1)
            condition = 'time >= {x1} && time <= {x2}'.format(x1=x1, x2=x2)
            s = '{}, {}'.format(formula, condition)
            items.append(s)

        # otherwise
        items.append('0.0')
        return 'piecewise({})'.format(', '.join(items))

    @staticmethod
    def natural_spline_coeffs(X, Y):
        """ Calculate natural spline coefficients.

        Calculation of coefficients for
            di*(x - xi)^3 + ci*(x - xi)^2 + bi*(x - xi) + ai
        for x in [xi, xi+1]

        Natural splines use a fixed second derivative, such that S''(x0)=S''(xn)=0,
        whereas clamped splines use fixed bounding conditions for S(x) at x0 and xn.

        A trig-diagonal matrix is constructed which can be efficiently solved.

        Equations and derivation from:
        https://jayemmcee.wordpress.com/cubic-splines/
        http://pastebin.com/EUs31Hvh

        :return:
        :rtype:
        """
        np1 = len(X)
        n = np1 - 1
        a = Y[:]
        b = [0.0] * n
        d = [0.0] * n
        h = [X[i + 1] - X[i] for i in range(n)]
        alpha = [0.0] * n
        for i in range(1, n):
            alpha[i] = 3 / h[i] * (a[i + 1] - a[i]) - 3 / h[i - 1] * (a[i] - a[i - 1])
        c = [0.0] * np1
        L = [0.0] * np1
        u = [0.0] * np1
        z = [0.0] * np1
        L[0] = 1.0
        u[0] = z[0] = 0.0
        for i in range(1, n):
            L[i] = 2 * (X[i + 1] - X[i - 1]) - h[i - 1] * u[i - 1]
            u[i] = h[i] / L[i]
            z[i] = (alpha[i] - h[i - 1] * z[i - 1]) / L[i]
        L[n] = 1.0
        z[n] = c[n] = 0.0
        for j in range(n - 1, -1, -1):
            c[j] = z[j] - u[j] * c[j + 1]
            b[j] = (a[j + 1] - a[j]) / h[j] - (h[j] * (c[j + 1] + 2 * c[j])) / 3
            d[j] = (c[j + 1] - c[j]) / (3 * h[j])
        # store coefficients
        coeffs = []
        for i in range(n):
            coeffs.append((a[i], b[i], c[i], d[i]))
        return coeffs

    @staticmethod
    def formula_linear(col1, col2):
        """ Linear interpolation between data points.

        :return:
        :rtype:
        """
        items = []
        for k in range(len(col1) - 1):
            x1 = col1.ix[k]
            x2 = col1.ix[k + 1]
            y1 = col2.ix[k]
            y2 = col2.ix[k + 1]
            m = (y2 - y1) / (x2 - x1)
            formula = '{} + {}*(time-{})'.format(y1, m, x1)
            condition = 'time >= {} && time < {}'.format(x1, x2)
            s = '{}, {}'.format(formula, condition)
            items.append(s)
        # last value after last time
        s = '{}, time >= {}'.format(col2.ix[len(col1) - 1], col1.ix[len(col1) - 1])
        items.append(s)
        # otherwise
        items.append('0.0')
        return 'piecewise({})'.format(', '.join(items))

    @staticmethod
    def formula_constant(col1, col2):
        """ Constant value between data points
        piecewise x1, y1, [x2, y2, ][...][z]
        A piecewise function: if (y1), x1.Otherwise, if (y2), x2, etc.Otherwise, z.
        :return:
        :rtype:
        """
        items = []
        # first value before first time
        s = '{}, time < {}'.format(col2.ix[0], col1.ix[0])
        items.append(s)

        # intermediate vales
        for k in range(len(col1) - 1):
            condition = 'time >= {} && time < {}'.format(col1.ix[k], col1.ix[k + 1])
            formula = '{}'.format(col2.ix[k])
            s = '{}, {}'.format(formula, condition)
            items.append(s)

        # last value after last time
        s = '{}, time >= {}'.format(col2.ix[len(col1) - 1], col1.ix[len(col1) - 1])
        items.append(s)

        # otherwise
        items.append('0.0')
        return 'piecewise({})'.format(', '.join(items))


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

    def write_sbml_to_file(self, sbml_out):
        """ Write the SBML file.

        First create clean SBML file.

        :param sbml_out:
        :type sbml_out:
        :return:
        :rtype:
        """
        self._create_sbml()
        libsbml.writeSBMLToFile(self.doc, sbml_out)

    def write_sbml_to_string(self):
        """ Write the SBML file.

        First create clean SBML file.

        :param sbml_out:
        :type sbml_out:
        :return:
        :rtype:
        """
        self._create_sbml()
        return libsbml.writeSBMLToString(self.doc)

    def _create_sbml(self):
        """ Create the SBMLDocument.

        :return:
        :rtype:
        """
        self._init_sbml_model()
        self.interpolators = Interpolation.create_interpolators(self.data, self.method)
        for interpolator in self.interpolators:
            Interpolation.add_interpolator_to_model(interpolator, self.model)

        # validation of SBML document
        try:
            temp_dir = tempfile.mkdtemp()
            tmp_f = os.path.join(temp_dir, 'validated.xml')
            libsbml.writeSBMLToFile(self.doc, tmp_f)
            validation.check_sbml(tmp_f, ucheck=False)
        finally:
            shutil.rmtree(temp_dir)

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

            # TODO: add ports for connection with other model
