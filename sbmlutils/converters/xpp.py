"""
xpp ode to SBML file converter.

XPP file format is described here
http://www.math.pitt.edu/~bard/bardware/tut/newstyle.html

Every ODE file consists of a series of lines that start with a keyword followed by
numbers, names, and formulas or declare a named formula such as a differential equation or auxiliary quantity.
Only the first letter of the keyword is important; e.g. the parser treats "parameter" and "punxatawney" exactly the same.
The parser can understand lines up to 256 characters. You can use line continuation by adding a backslash character.
The first line of the file cannot be a number (as this tells XPP that the file is in the old-style) but can be any
other charcter or declaration. It is standard form to make the first line a comment which has the name of the
file, but this is optional.

Initial data are optional, XPP sets them to zero by default and they can be changed within the program.

Only supports subset of features.
"""
from __future__ import print_function, absolute_import
import os
import re
import warnings
import libsbml
from sbmlutils._version import __version__
from sbmlutils import factory as fac
from sbmlutils import sbmlio
from sbmlutils.report import sbmlreport

XPP_ODE = "ode"
XPP_DE = "difference equation"  # x(t+1)=F(x,y,...)
XPP_IE = "integral equation"  # x(t) =  ...int{K(u,t,t')}...
XPP_ZIP = "zippy"  # Fixed or hidden values
XPP_FUN = "functions"  # f(x,y) = x^2/(x^2+y^2)
XPP_IDA = "initial data"
XPP_AUX = "auxiliary quantities"
XPP_MAR = "markov variables"
XPP_WIE = "wiener variables"
XPP_GLO = "global flags"
XPP_PAR = "parameter"
XPP_NUM = "number"
XPP_TAB = "table"

XPP_COMMENT_CHAR = '#'
XPP_SETTING_CHAR = '@'
XPP_END_WORD = 'done'
XPP_TYPE_CHARS = {
    XPP_PAR: 'p', # parameter
    XPP_AUX: 'a', # assignment rule
    XPP_WIE: 'w', #

}

NOTES = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>XPP model</h1>
    <p>This model was converted from XPP ode format to SBML using <code>sbmlutils-{}</code>.</p> 
    <pre>{}</pre>
    <div class="dc:publisher">This file has been produced by
      <a href="https://github.com/matthiaskoenig/sbmlutils/" title="sbmlutils" target="_blank">sbmlutils</a>.
    </div>

    <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2017 Matthias Koenig</div>
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
""".format(__version__, '{}')


def xpp2sbml(xpp_file, sbml_file):
    """ Reads given xpp_file and converts to SBML file.

    :param xpp_file: xpp input ode file
    :param sbml_file: sbml output file
    :return:
    """
    print('-' * 80)
    print('xpp2sbml')
    print('-' * 80)
    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()

    parameters = []
    rate_rules = []
    assignment_rules = []
    initial_assignments = []

    with open(xpp_file) as f:
        lines = f.readlines()

        text = "".join(lines)
        fac.set_notes(model, NOTES.format(text))

        for line in lines:
            # clean up the ends
            line = line.rstrip('\n').strip()
            # empty line
            if len(line) == 0:
                continue
            # comment line
            if line.startswith(XPP_COMMENT_CHAR):
                continue
            # xpp setting
            if line.startswith(XPP_SETTING_CHAR):
                continue
            # end word
            if line == XPP_END_WORD:
                continue

            # check for the equal sign
            tokens = line.split('=')
            tokens = [t.strip() for t in tokens]

            #####################
            # Line without '=' sign
            #####################
            # parameter, wiener
            if len(tokens) == 1:
                items = [t.strip() for t in tokens[0].split(' ')]
                # keyword, value
                if len(items) == 2:
                    xid, sid = items[0], items[1]

                    # wiener
                    if xid.startswith(XPP_TYPE_CHARS[XPP_WIE]):
                        ''' Wiener parameters are normally distributed numbers with zero mean 
                        and unit standard deviation. They are useful in stochastic simulations since 
                        they automatically scale with change in the integration time step. 
                        Their names are listed separated by commas or spaces. '''
                        # FIXME: this should be encoded using dist
                        parameters.append(
                            fac.Parameter(sid=sid, value=0.0)
                        )
                else:
                    warnings.warn("XPP line not parsed: '{}'".format(line))

            #####################
            # Line with '=' sign
            #####################
            # ode, difference equation
            elif len(tokens) == 2:
                left, right = tokens[0], tokens[1]
                # parameters


                # ode
                if left.endswith("'"):
                    sid = left[0:-1]
                    rate_rules.append(
                        fac.RateRule(sid=sid, value=right)
                    )
                else:
                    warnings.warn("XPP line not parsed: '{}'".format(line))

    sbmlio.write_sbml(doc, sbml_file, validate=False, program_name="sbmlutils", program_version=__version__)

if __name__ == "__main__":
    xpp_file = "PLoSCompBiol_Fig1.ode"
    sbml_file = "PLoSCompBiol_Fig1.xml"
    xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
    sbmlreport.create_sbml_report(sbml_file, out_dir=".")
