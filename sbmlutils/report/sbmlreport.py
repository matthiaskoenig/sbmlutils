# -*- coding: utf-8 -*-
"""
Create Report from given SBML file.

The model report is implemented based on a standard template language,
which uses the SBML information to render the final document.

Currently the following templates are available:
<HTML>
- in addition to the created HTML, the necessary CSS and JS files are copied.

The basic steps of template creation are
- configure an Engine (jinja2)
- compile template
- render with SBML context
"""
# TODO: implement offline version of the report
# TODO: rate rules are not displayed correctly (they need dy/dt on the left side, compared to AssignmentRules)


from __future__ import print_function, division
import warnings
import codecs
import os
import ntpath

import distutils
from distutils import dir_util
import sys

import libsbml
from jinja2 import Environment, FileSystemLoader

import sbmlfilters
from sbmlutils.validation import check_sbml


# Change default encoding to UTF-8
# We need to reload sys module first, because setdefaultencoding is available only at startup time
# reload(sys)
# sys.setdefaultencoding('utf-8')

# template location
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')


def create_sbml_reports(sbml_paths, out_dir, template='report.html', promote=False, validate=True):
    """ Creates individual reports and an overview file.

    :param sbmls:
    :param out_dir:
    :param template:
    :param promote:
    :param validate:
    :return:
    """
    # individual reports
    for sbml_path in sbml_paths:
        create_sbml_report(sbml_path, out_dir, template=template, promote=promote, validate=validate)

    # write index html (unicode)
    html = _create_index_html(sbml_paths)
    f_index = codecs.open(os.path.join(out_dir, 'index.html'), encoding='utf-8', mode='w')
    f_index.write(html)
    f_index.close()


def _create_index_html(sbml_paths, html_template='index.html'):
    """Create index for sbml_paths.
    """

    # template environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                         extensions=['jinja2.ext.autoescape'],
                         trim_blocks=True,
                         lstrip_blocks=True)

    template = env.get_template(html_template)


    sbml_basenames = [ntpath.basename(path) for path in sbml_paths]
    sbml_links = []
    for basename in sbml_basenames:
        tokens = basename.split('.')
        name = '.'.join(tokens[:-1]) + '.html'
        sbml_links.append(name)

    # Context
    c = {
        'sbml_basenames': sbml_basenames,
        'sbml_links': sbml_links,
    }
    return template.render(c)


def create_sbml_report(sbml_path, out_dir, template='report.html', promote=False, validate=True):
    """ Creates the SBML report in the out_dir

    :param doc:
    :type doc:
    :param out_dir:
    :type out_dir:
    :return:
    :rtype:
    """
    # check if sbml_file exists
    if not os.path.exists(sbml_path):
        warnings.warn('SBML file does not exist: {}'.format(sbml_path))

    # check the sbml file
    if validate:
        check_sbml(sbml_path)

    # read sbml
    doc = libsbml.readSBML(sbml_path)

    if promote:
        model = doc.getModel()
        mid = model.id
        mid = '{}_{}'.format(mid, 'promoted')
        model.setId(mid)

        # promote local parameters
        props = libsbml.ConversionProperties()
        props.addOption("promoteLocalParameters", True, "Promotes all Local Parameters to Global ones")
        if doc.convert(props) != libsbml.LIBSBML_OPERATION_SUCCESS:
            warnings.warn("SBML Conversion failed...")
        else:
            print("SBML Conversion successful")

    basename = os.path.basename(sbml_path)
    tokens = basename.split('.')
    name = '.'.join(tokens[:-1])

    f_sbml = os.path.join(out_dir, basename)
    libsbml.writeSBMLToFile(doc, f_sbml)

    # write html (unicode)
    html = _create_html(doc, basename, html_template=template)
    f_html = codecs.open(os.path.join(out_dir, '{}.html'.format(name)),
                         encoding='utf-8', mode='w')
    f_html.write(html)
    f_html.close()

    # copy the additional files
    _copy_directory(os.path.join(TEMPLATE_DIR, '_report'), os.path.join(out_dir, '_report'))


def _create_html(doc, basename, html_template='report.html'):
    """Create HTML from SBML.

    :param doc:
    :type doc:
    :param html_template:
    :type html_template:
    :return:
    :rtype:
    """
    model = doc.getModel()
    values = _create_value_dictionary(model)

    # template environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                         extensions=['jinja2.ext.autoescape'],
                         trim_blocks=True,
                         lstrip_blocks=True)
    # additional SBML filters
    for key in sbmlfilters.filters:
        env.filters[key] = getattr(sbmlfilters, key)

    template = env.get_template(html_template)

    # Context
    c = {
        'basename': basename,
        'doc': doc,
        'model': model,
        'values': values,
        'units': model.getListOfUnitDefinitions(),
        'compartments': model.getListOfCompartments(),
        'functions': model.getListOfFunctionDefinitions(),
        'parameters': model.getListOfParameters(),
        'rules': model.getListOfRules(),
        'assignments': model.getListOfInitialAssignments(),
        'species': model.getListOfSpecies(),
        'reactions': model.getListOfReactions(),
        'constraints': model.getListOfConstraints(),
        'events': model.getListOfEvents(),
    }
    return template.render(c)


def _create_value_dictionary(model):
    values = dict()

    # parse all the initial assignments
    for assignment in model.getListOfInitialAssignments():
        sid = assignment.getId()
        # math = ' = {}'.format(libsbml.formulaToString(assignment.getMath()))
        values[sid] = assignment
    # rules
    for rule in model.getListOfRules():
        sid = rule.getVariable()
        # math = ' = {}'.format(libsbml.formulaToString(rule.getMath()))
        values[sid] = rule
    return values


def _copy_directory(src, dest):
    """ Copy directory from source to destination.
    :param src:
    :type src:
    :param dest:
    :type dest:
    :return:
    :rtype:
    """

    # copy
    dir_util.copy_tree(src, dest)

#################################################################################################
# Create report
#################################################################################################

if __name__ == '__main__':
    import os
    from sbmlutils.examples import testfiles
    os.chdir(os.path.join(testfiles.test_dir, 'report'))
    create_sbml_report(sbml_path='galactose_30_annotated.xml', out_dir='.')

