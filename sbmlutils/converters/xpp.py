# -*- coding: utf-8 -*-
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

! Variables have to be case sensitive !. These issues can easily be fixed based on validator output.

Only supports subset of features.
Not supported:
- table
- sum,
- shift
- set
- boundary
- ran
- arrays

 shift(var,expr) This operator evaluates the expression expr converts it to an integer and then uses this to
 indirectly address a variable whose address is that of var plus the integer value of the expression. This is a way
 to imitate arrays in XPP. For example if you defined the sequence of 5 variables, u0,u1,u2,u3,u4 one right after
 another, then shift(u0,2) would return the value of u2.

 sum(ex1,ex2)of(ex3) is a way of summing up things. The expressions ex1>, are evaluated and their integer parts are
 used as the lower and upper limits of the sum. The index of the sum is i' so that you cannot have double sums since
 there is only one index. ex3 is the expression to be summed and will generally involve i' For example sum(1,10)of(i')
 will be evaluated to 55. Another example combines the sum with the shift operator. sum(0,4)of(shift(u0,i')) will
 sum up u0 and the next four variables that were defined after it.
"""
# FIXME: recursive if than else not supported
# TODO: rnd via dist (also normal)
# TODO: rewrite using a proper parser like PLY Lex-Yacc (especially the function replacements are very cumbersome)

from __future__ import print_function, absolute_import
import warnings
import re
from pprint import pprint
import libsbml

from sbmlutils._version import __version__
from sbmlutils import factory as fac
from sbmlutils import sbmlio
from sbmlutils import validation
from sbmlutils.converters import xpp_helpers

XPP_ODE = "ode"
XPP_DE = "difference equation"  # x(t+1)=F(x,y,...)
XPP_IE = "integral equation"  # x(t) =  ...int{K(u,t,t')}...
XPP_FUN = "functions"  # f(x,y) = x^2/(x^2+y^2)
XPP_INIT = "initial data"
XPP_AUX = "auxiliary quantities"
XPP_MAR = "markov variables"
XPP_WIE = "wiener variables"
XPP_GLO = "global flags"
XPP_PAR = "parameter"
XPP_NUM = "number"
XPP_TAB = "table"

XPP_COMMENT_CHARS = ['#', '%', '"']
XPP_CONTINUATION_CHAR = '\\'
XPP_SETTING_CHAR = '@'
XPP_END_WORD = 'done'
XPP_TYPE_CHARS = {
    XPP_PAR: 'p',
    XPP_AUX: 'a',
    XPP_WIE: 'w',
    XPP_INIT: 'i',
    XPP_NUM: 'n',
    # not supported
    XPP_GLO: 'g',
    XPP_TAB: 't',
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


def escape_string(info):
    info = info.replace("<", "&lt;")
    info = info.replace(">", "&gt;")
    info = info.replace("&", "&amp;")
    return info


def parse_keyword(xpp_id):
    """ Parses the keyword and returns the xpp keyword type.
    :param xpp_id:
    :return:
    """
    xpp_id = xpp_id.lower()
    for xpp_key, c in XPP_TYPE_CHARS.items():
        if xpp_id.startswith(c):
            return xpp_key
    warnings.warn("Keyword not supported: {}".format(xpp_id))
    return None


def parts_from_expression(expression):
    """ Returns the parts of given expression.
    The parts can be whitespace or comma separated.

    V1=-0.75  R1=0.26  CA1=0.1 H1=0.1
    V1=-0.75,  R1=0.26,  CA1=0.1, H1=0.1

    but there can also be commas in function definitions
    vex=vex(t,freq,vext)

    :return: list of cleaned parts
    """
    # replace all separators with comma
    # groups = re.findall('(.+?=.+?)[,\s]+', expression)
    # print('groups', groups)
    # return groups

    tokens = expression.split('=')
    if len(tokens) == 2:
        return [expression]
    else:
        # get the individual parts, i.e. all the assignments
        # FIXME: bad hack which will break with function definitions
        expression = expression.replace(' ', ',')
        expression = expression.replace('\t', ',')
        parts = [t.strip() for t in expression.split(',')]
        parts = [p for p in parts if len(p) > 0]
    return parts


def sid_value_from_part(part):
    """ Get sid, value tuple from given part of expression.

    :param part:
    :return:
    """
    sid, value = [t.strip() for t in part.split('=')]
    return sid, value


##################################
# Converter
##################################
def xpp2sbml(xpp_file, sbml_file, force_lower=False, validate=validation.VALIDATION_NO_UNITS, debug=False):
    """ Reads given xpp_file and converts to SBML file.

    :param xpp_file: xpp input ode file
    :param sbml_file: sbml output file
    :param force_lower: force lower case for all lines
    :param validate: perform validation on the generated SBML file
    :return:
    """
    print('-' * 80)
    print('xpp2sbml: ', xpp_file, '->', sbml_file)
    print('-' * 80)
    doc = libsbml.SBMLDocument(3, 1)
    model = doc.createModel()

    parameters = []
    initial_assignments = []
    rate_rules = []
    assignment_rules = []
    functions = [
        # definition of min and max
        fac.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='minimum'),
        fac.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='maximum'),
        # heav (heavyside)
        fac.Function('heav', 'lambda(x, piecewise(0,lt(x,0), 0.5, eq(x, 0), 1,gt(x,0), 0))', name='heavyside'),
        # mod (modulo)
        fac.Function('mod', 'lambda(x,y, x % y)', name='modulo'),
    ]
    function_definitions = []
    events = []

    def replace_fdef():
        """ Replace all arguments within the formula definitions."""
        changes = False
        for k, fdata in enumerate(function_definitions):
            for i in range(len(function_definitions)):
                if i != k:
                    # replace i with k
                    formula = function_definitions[i]['formula']
                    new_formula = xpp_helpers.replace_formula(
                        formula,
                        fid=function_definitions[k]['fid'],
                        old_args=function_definitions[k]['old_args'],
                        new_args=function_definitions[k]['new_args']
                    )
                    if new_formula != formula:
                        function_definitions[i]['formula'] = new_formula
                        function_definitions[i]['new_args'] = list(sorted(set(function_definitions[i]['new_args'] + \
                                                              function_definitions[k]['new_args'])))
                        changes = True

        return changes

    def create_initial_assignment(sid, value):
        """ Helper for creating initial assignments """
        # check if valid identifier
        if '(' in sid:
            warnings.warn("sid is not valid: {}. Initial assignment is not generated".format(sid))
            return

        try:
            f_value = float(value)
            parameters.append(
                fac.Parameter(sid=sid, value=f_value, name="{} = {}".format(sid, value), constant=False)
            )
        except ValueError:
            '''
            Initial data are optional, XPP sets them to zero by default (many xpp model don't write the p(0)=0.
            '''
            parameters.append(
                fac.Parameter(sid=sid, value=0.0, name=sid, constant=False)
            )
            initial_assignments.append(
                fac.InitialAssignment(sid=sid, value=value, name="{} = {}".format(sid, value))
            )

    ###########################################################################
    # First iteration to parse relevant lines and get the replacement patterns
    ###########################################################################
    parsed_lines = []
    # with open(xpp_file, encoding="utf-8") as f:
    with open(xpp_file) as f:
        lines = f.readlines()

        # add info to sbml
        text = escape_string("".join(lines))
        fac.set_notes(model, NOTES.format(text))

        old_line = None
        for line in lines:
            if force_lower:
                line = line.lower()

            # clean up the ends
            line = line.rstrip('\n').strip()
            # handle douple continuation characters in some models
            line = line.replace('\\\\', '\\')
            # handle semicolons
            line = line.rstrip(';')

            # join continuation
            if old_line:
                line = old_line + line
                old_line = None

            # empty line
            if len(line) == 0:
                continue
            # comment line
            if line[0] in XPP_COMMENT_CHARS:
                continue
            # xpp setting
            if line.startswith(XPP_SETTING_CHAR):
                continue
            # end word
            if line == XPP_END_WORD:
                continue
            # line continuation
            if line.endswith(XPP_CONTINUATION_CHAR):
                old_line = line.rstrip(XPP_CONTINUATION_CHAR)
                continue

            # handle the power function
            line = line.replace('**', '^')

            # handle if(...)then(...)else()
            pattern_ite = re.compile('if\s*\((.*)\)\s*then\s*\((.*)\)\s*else\s*\((.*)\)')
            pattern_ite_sub = re.compile("if\s*\(.*\)\s*then\s*\(.*\)\s*else\s*\(.*\)")
            groups = re.findall(pattern_ite, line)
            for group in groups:
                condition = group[0]
                assignment = group[1]
                otherwise = group[2]
                f_piecewise = "piecewise({}, {}, {})".format(assignment, condition, otherwise)
                line = re.sub(pattern_ite_sub, f_piecewise, line)

            ################################
            # Function definitions
            ################################
            ''' Functions are defined in xpp via fid(arguments) = formula
            f(x,y) = x^2/(x^2+y^2)
            They can have up to 9 arguments.
            The difference to SBML functions is that xpp functions have access to the global parameter values
            '''
            f_pattern = re.compile('(.*)\s*\((.*)\)\s*=\s*(.*)')
            groups = re.findall(f_pattern, line)
            if groups:
                # function definitions found
                fid, args, formula = groups[0]
                # handles the initial assignments which look like function definitions
                if args == '0':
                    parsed_lines.append(line)
                    continue

                # necessary to find the additional arguments from the ast_node
                ast = libsbml.parseL3Formula(formula)
                names = set(xpp_helpers.find_names_in_ast(ast))
                old_args = [t.strip() for t in args.split(',')]
                new_args = [a for a in names if a not in old_args]

                # handle special functions
                if fid == 'power':
                    warnings.warn("power function cannot be added to model, rename function.")
                else:
                    # store functions with additional arguments
                    function_definitions.append(
                        {'fid': fid,
                         'old_args': old_args,
                         'new_args': new_args,
                         'formula': formula}
                    )
                # don't append line, function definition has been handeled
                continue

            parsed_lines.append(line)
    if debug:
        print('\n\nFUNCTION_DEFINITIONS')
        pprint(function_definitions)

    # functions can use functions so this also must be replaced
    changes = True
    while changes:
        changes = replace_fdef()

    # clean the new arguments
    for fdata in function_definitions:
        fdata['new_args'] = list(sorted(set(fdata['new_args'])))

    if debug:
        print('\nREPLACED FUNCTION_DEFINITIONS')
        pprint(function_definitions)

    # Create function definitions
    for k, fdata in enumerate(function_definitions):
        fid = fdata['fid']
        formula = fdata['formula']
        arguments = ','.join(fdata['old_args'] + fdata['new_args'])
        functions.append(
            fac.Function(fid, 'lambda({}, {})'.format(arguments, formula)),
        )

    ###########################################################################
    # Second iteration
    ###########################################################################
    if debug:
        print('\nPARSED LINES')
        pprint(parsed_lines)
        print('\n\n')
    for line in parsed_lines:

        # replace function definitions in lines
        new_line = line
        for fdata in function_definitions:
            new_line = xpp_helpers.replace_formula(new_line, fdata['fid'], fdata['old_args'], fdata['new_args'])

        if new_line != line:
            if False:
                print('\nReplaced FD', fdata['fid'], ':', new_line)
                print('->', new_line, '\n')
            line = new_line

        if debug:
            # line after function replacements
            print('*'*3, line, '*'*3)

        ################################
        # Start parsing the given line
        ################################
        # check for the equal sign
        tokens = line.split('=')
        tokens = [t.strip() for t in tokens]

        #######################
        # Line without '=' sign
        #######################
        # wiener
        if len(tokens) == 1:
            items = [t.strip() for t in tokens[0].split(' ') if len(t) > 0]
            # keyword, value
            if len(items) == 2:
                xid, sid = items[0], items[1]
                xpp_type = parse_keyword(xid)

                # wiener
                if xpp_type == XPP_WIE:
                    ''' Wiener parameters are normally distributed numbers with zero mean 
                    and unit standard deviation. They are useful in stochastic simulations since 
                    they automatically scale with change in the integration time step. 
                    Their names are listed separated by commas or spaces. '''
                    # FIXME: this should be encoded using dist
                    parameters.append(
                        fac.Parameter(sid=sid, value=0.0)
                    )
                    continue  # line finished
            else:
                warnings.warn("XPP line not parsed: '{}'".format(line))

        #####################
        # Line with '=' sign
        #####################
        # parameter, aux, ode, initial assignments
        elif len(tokens) >= 2:
            left = tokens[0]
            items = [t.strip() for t in left.split(' ') if len(t) > 0]
            # keyword based information, i.e 2 items are on the left of the first '=' sign
            if len(items) == 2:
                xid = items[0]  # xpp keyword
                xpp_type = parse_keyword(xid)
                expression = ' '.join(items[1:]) + "=" + "=".join(tokens[1:])  # full expression after keyword
                parts = parts_from_expression(expression)
                if False:
                    print('xid:', xid)
                    print('expression:', expression)
                    print('parts:', parts)

                # parameter & numbers
                if xpp_type in [XPP_PAR, XPP_NUM]:
                    ''' Parameter values are optional; if not they are set to zero. 
                    Number declarations are like parameter declarations, except that they cannot be 
                    changed within the program and do not appear in the parameter window. '''
                    for part in parts:
                        sid, value = sid_value_from_part(part)
                        create_initial_assignment(sid, value)

                # aux
                elif xpp_type == XPP_AUX:
                    '''Auxiliary quantities are expressions that depend on all of your dynamic 
                    variables which you want to keep track of. Energy is one such example. They are declared
                    like fixed quantities, but are prefaced by aux .'''
                    for part in parts:
                        sid, value = sid_value_from_part(part)
                        if sid == value:
                            # avoid circular dependencies (no information in statement)
                            pass
                        else:
                            assignment_rules.append(
                                fac.AssignmentRule(sid=sid, value=value)
                            )

                # init
                elif xpp_type == XPP_INIT:
                    for part in parts:
                        sid, value = sid_value_from_part(part)
                        create_initial_assignment(sid, value)

                # table
                elif xpp_type == XPP_TAB:
                    ''' The Table declaration allows the user to specify a function of 1 variable in terms 
                    of a lookup table which uses linear interpolation. The name of the function follows the 
                    declaration and this is followed by (i) a filename (ii) or a function of "t".'''
                    warnings.warn("XPP_TAB not supported: XPP line not parsed: '{}'".format(line))

                else:
                    warnings.warn("XPP line not parsed: '{}'".format(line))

            elif len(items) >= 2:
                xid = items[0]
                xpp_type = parse_keyword(xid)
                # global
                if xpp_type == XPP_GLO:
                    '''Global flags are expressions that signal events when they change sign, from less than 
                    to greater than zero if sign=1 , greater than to less than if sign=-1 or either way 
                    if sign=0. The condition should be delimited by braces {} The events are of the form 
                    variable=expression, are delimited by braces, and separated by semicolons. When the 
                    condition occurs all the variables in the event set are changed possibly discontinuously.
                    '''

                    # global sign {condition} {name1 = form1; ...}
                    pattern_global = re.compile('([+,-]{0,1}\d{1})\s+\{{0,1}(.*)\{{0,1}\s+\{(.*)\}')
                    groups = re.findall(pattern_global, line)
                    if groups:
                        g = groups[0]
                        sign = int(g[0])
                        trigger = g[1]
                        # FIXME: handle sign=-1, sign=0, sign=+1
                        if sign == -1:
                            trigger = g[1] + ">= 0"
                        elif sign == 1:
                            trigger = g[1] + ">= 0"
                        elif sign == 0:
                            trigger = g[1] + ">= 0"

                        assignment_parts = [t.strip() for t in g[2].split(';')]
                        assignments = {}
                        for p in assignment_parts:
                            key, value = p.split("=")
                            assignments[key] = value

                        events.append(
                            fac.Event(sid="e{}".format(len(events)), trigger=trigger, assignments=assignments)
                        )

                    else:
                        warnings.warn("global expression could not be parsed: {}".format(line))
                else:
                    warnings.warn("XPP line not parsed: '{}'".format(line))

            # direct assignments
            elif len(items) == 1:
                right = tokens[1]

                # init
                if left.endswith('(0)'):
                    sid, value = left[0:-3], right
                    create_initial_assignment(sid, value)

                # difference equations
                elif left.endswith('(t+1)'):
                    warnings.warn("Difference Equations not supported: XPP line not parsed: '{}'".format(line))

                # ode
                elif left.endswith("'"):
                    sid = left[0:-1]
                    rate_rules.append(
                        fac.RateRule(sid=sid, value=right)
                    )
                elif left.endswith("/dt"):
                    sid = left[1:-3]
                    rate_rules.append(
                        fac.RateRule(sid=sid, value=right)
                    )
                # assignment rules
                else:
                    assignment_rules.append(
                        fac.AssignmentRule(sid=left, value=right)
                    )
            else:
                warnings.warn("XPP line not parsed: '{}'".format(line))

    # add time
    assignment_rules.append(
        fac.AssignmentRule(sid="t", value="time", name="model time")
    )

    # create SBML objects
    objects = parameters + initial_assignments + functions + rate_rules + assignment_rules + events
    fac.create_objects(model, objects, debug=False)

    '''
    Parameter values are optional; if not they are set to zero in xpp.
    Many models do not encode the initial zeros.
    '''
    for p in doc.getModel().getListOfParameters():
        if not p.isSetValue():
            p.setValue(0.0)

    sbmlio.write_sbml(doc, sbml_file, validate=validate, program_name="sbmlutils", program_version=__version__)
