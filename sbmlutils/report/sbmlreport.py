# -*- coding: utf-8 -*-
"""
Create an SBML Report from given SBML file or set of SBML files (for instance for comp models).

The model report is implemented based on a standard template language,
which uses the SBML information to render the final document.

The basic steps of template creation are
- configure the engine (jinja2)
- compile template
- render with SBML context

The final report consists of an HTML file with an overview over the SBML elements in the model.
"""
from __future__ import print_function, division, absolute_import
import codecs
import ntpath
import os
import warnings
from distutils import dir_util

import libsbml
from jinja2 import Environment, FileSystemLoader

from sbmlutils.report import sbmlfilters
from sbmlutils.validation import check_sbml
from sbmlutils.utils import promote_local_variables

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
        print(sbml_path)
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

    :param validate:
    :param promote:
    :param template:
    :param sbml_path:
    :param doc:
    :param out_dir:
    :return:
    :rtype:
    """
    # check if sbml_file exists
    if not os.path.exists(sbml_path):
        warnings.warn('SBML file does not exist: {}'.format(sbml_path))

    # check sbml file
    if validate:
        check_sbml(sbml_path)

    # read sbml
    doc = libsbml.readSBML(sbml_path)
    if promote:
        promote_local_variables(doc)

    # write sbml to output folder
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
    # template environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR),
                      extensions=['jinja2.ext.autoescape'],
                      trim_blocks=True,
                      lstrip_blocks=True)
    # additional SBML filters
    for key in sbmlfilters.filters:
        env.filters[key] = getattr(sbmlfilters, key)

    model = doc.getModel()
    if model is not None:
        template = env.get_template(html_template)
        values = _create_value_dictionary(model)

        # TODO: create all the objects for the templates, i.e. all the logic is performed
        # here and the template language just accesses the fields

        # Context
        c = {
            'basename': basename,
            'doc': doc,
            'model': model,
            'values': values,

            'functions': listOfFunctions(model),
            'units': listOfUnits(model),
            'compartments': listOfCompartments(model, values),

            'parameters': model.getListOfParameters(),
            'rules': model.getListOfRules(),
            'assignments': model.getListOfInitialAssignments(),
            'species': model.getListOfSpecies(),
            'reactions': model.getListOfReactions(),
            'constraints': model.getListOfConstraints(),
            'events': model.getListOfEvents(),
        }
    else:
        # no model exists
        warnings.warn("No model in SBML file when creating model report: {}".format(doc))
        template = env.get_template("report_no_model.html")
        c = {
            'basename': basename,
            'doc': doc,
        }
    return template.render(c)

from sbmlutils.report.sbmlfilters import *

##############################
# UnitDefinitions
##############################

def infoSbase(item):
    info = {
            'id': item.id,
            'metaId': item.getMetaId(),
            'name': item.name,
            'sbo': sbo(item),
            'cvterm': cvterm(item),
    }
    return info

def listOfFunctions(model):
    items = []
    for item in model.model.getListOfFunctionDefinitions():
        info = infoSbase(item)
        info['math'] = math(item)
        items.append(info)
    return items

def listOfUnits(model):
    items = []
    for item in model.getListOfUnitDefinitions():
        info = infoSbase(item)
        info['units'] = SBML_stringToMathML(SBML_unitDefinitionToString(item))
        items.append(info)
    return items

def listOfCompartments(model, values):
    items = []
    for item in model.getListOfCompartments():
        info = infoSbase(item)
        for attr in ['units', 'spatial_dimensions']:
            info[attr] = getattr(item, attr)
        info['constant'] = boolean(item)
        info['derived unit'] = derived_units(item)
        if item.isSetSize():
            size = item.size
        else:
            size = math(values[item.id])
        info['size'] = size
        items.append(info)
    return items


##############################
# Helpers
##############################
def notes(item):
    if item.isSetNotes():
        return SBML_notesToString(item)

def cvterm(item):
    if item.isSetAnnotation():
       return '<div class="cvterm">{}</div>'.format(SBML_annotationToString(item))
    return ''

def sbo(item):
    if item.getSBOTerm() != -1:
        return '<div class="cvterm"><a href="{}" target="_blank">{}</a></div>'.format(item.getSBOTermAsURL(), item.getSBOTermID())
    return ''

def annotation(item):
    info = '<div class="cvterm">'
    if item.getSBOTerm() != -1:
        info += '<a href="{}" target="_blank">{}</a><br />'.format(item.getSBOTermAsURL(), item.getSBOTermID())
    if item.isSetAnnotation():
        info += SBML_annotationToString(item)
    info += '</div>'
    return info

def math(item):
    if item:
        return SBML_astnodeToMathML(item.getMath())

def boolean(condition):
    if condition:
        return '<td class="success"><span class="glyphicon glyphicon-ok green"></span><span class="invisible">T</span></td>'
    else:
        return '<td class="danger"><span class="glyphicon glyphicon-remove red"><span class="invisible">F</span></span></td>'

def annotation_xml(item):
    if item.isSetAnnotation():
        return '<pre>{}</pre>'.format(item.getAnnotationString().decode('utf-8'))

def xml(item):
    return '<textarea style="border:none;">{}</textarea>'.format(item.toSBML())

def derived_units(item):
    if item:
        return SBML_stringToMathML(SBML_unitDefinitionToString(item.getDerivedUnitDefinition()))


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
