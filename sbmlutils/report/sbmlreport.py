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
from sbmlutils import formating
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

        # Context
        c = {
            'basename': basename,
            'values': values,

            'doc': document_dict(doc),
            'model': model_dict(model),
            'functions': listOfFunctions_dict(model),
            'units': listOfUnits_dict(model),
            'compartments': listOfCompartments_dict(model, values),
            'species': listOfSpecies_dict(model),
            'geneproducts': listOfGeneProducts_dict(model),
            'parameters': listOfParameters_dict(model, values),
            'assignments': listOfInitialAssignments_dict(model),
            'rules': listOfRules_dict(model),
            'reactions': listOfReactions_dict(model),
            'objectives': listOfObjectives_dict(model),
            'constraints': listOfConstraints_dict(model),
            'events': listOfEvents_dict(model),
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


##############################
# Information Dictionaries
##############################

def _create_value_dictionary(model):
    values = dict()

    # parse all the initial assignments
    for assignment in model.getListOfInitialAssignments():
        # sid = assignment.getId()
        sid = assignment.getSymbol()

        # math = ' = {}'.format(libsbml.formulaToString(assignment.getMath()))
        values[sid] = assignment
    # rules
    for rule in model.getListOfRules():
        sid = rule.getVariable()
        # math = ' = {}'.format(libsbml.formulaToString(rule.getMath()))
        values[sid] = rule

    return values


def infoSbase(item):
    info = {
            'object': item,
            'id': item.id,
            'metaId': metaId(item),
            'name': item.name,
            'sbo': sbo(item),
            'cvterm': cvterm(item),
            'notes': notes(item),
            'annotation': annotation(item)
    }

    return info

def document_dict(document):
    info = infoSbase(document)

    return info


def model_dict(model):
    info = infoSbase(model)
    info['history'] = formating.modelHistoryToString(model.getModelHistory())
    return info


def listOfFunctions_dict(model):
    items = []
    for item in model.model.getListOfFunctionDefinitions():
        info = infoSbase(item)
        info['math'] = math(item)
        items.append(info)
    return items

def listOfUnits_dict(model):
    items = []
    for item in model.getListOfUnitDefinitions():
        info = infoSbase(item)
        info['units'] = formating.stringToMathML(formating.unitDefinitionToString(item))
        items.append(info)
    return items

def listOfCompartments_dict(model, values):
    items = []
    for item in model.getListOfCompartments():
        info = infoSbase(item)
        info['units'] = item.units
        if item.isSetSpatialDimensions():
            spatial_dimensions = item.spatial_dimensions
        else:
            spatial_dimensions = ''
        info['spatial_dimensions'] = spatial_dimensions
        info['constant'] = boolean(item.constant)
        info['derived_units'] = derived_units(item)
        if item.isSetSize():
            size = item.size
        else:
            size = math(values.get(item.id, ''))

        info['size'] = size
        items.append(info)
    return items

def listOfSpecies_dict(model):
    items = []
    for item in model.getListOfSpecies():
        info = infoSbase(item)
        info['compartment'] = item.compartment
        info['boundary_condition'] = boolean(item.boundary_condition)
        info['constant'] = boolean(item.constant)
        if item.isSetInitialAmount():
            info['initial_amount'] = item.initial_amount
        if item.isSetInitialConcentration():
            info['initial_concentration'] = item.initial_concentration
        info['substance_units'] = item.substance_units
        info['derived_units'] = derived_units(item)
        info['xml'] = xml(item)

        # fbc
        sfbc = item.getPlugin("fbc")
        if sfbc:
            if sfbc.isSetChemicalFormula():
                info['fbc:formula'] = sfbc.getChemicalFormula()
            if sfbc.isSetCharge():
                c = sfbc.getCharge()
                if c is not 0:
                    info['fbc:charge'] = ' ({})'.format(sfbc.getCharge())

        items.append(info)
    return items

def listOfGeneProducts_dict(model):
    items = []
    mfbc = model.getPlugin("fbc")
    if mfbc:
        for item in mfbc.getListOfGeneProducts():
            info = infoSbase(item)
            info['label'] = item.label
            info['associated_species'] = item.associated_species
            items.append(info)
    return items


def listOfParameters_dict(model, values):
    items = []
    for item in model.getListOfParameters():
        info = infoSbase(item)
        info['units'] = item.units
        if item.isSetValue():
            value = item.value
        else:
            value = math(values[item.id])
        info['value'] = value
        info['derived_units'] = derived_units(item)
        info['constant'] = boolean(item.constant)
        items.append(info)
    return items


def listOfInitialAssignments_dict(model):
    items = []
    for item in model.getListOfInitialAssignments():
        info = infoSbase(item)
        info['symbol'] = item.symbol
        info['assignment'] = math(item)
        info['derived_units'] = derived_units(item)
        items.append(info)
    return items


def listOfRules_dict(model):
    items = []
    for item in model.getListOfRules():
        info = infoSbase(item)
        info['variable'] = formating.ruleVariableToString(item)
        info['assignment'] = math(item)
        info['derived_units'] = derived_units(item)

        items.append(info)
    return items


def listOfConstraints_dict(model):
    items = []
    for item in model.getListOfConstraints():
        info = infoSbase(item)
        info['constraint'] = math(item)
        items.append(info)
    return items


def listOfReactions_dict(model):
    items = []
    for item in model.getListOfReactions():
        info = infoSbase(item)
        if item.reversible:
            reversible = '<td class ="success">&#8646;</td>'
        else:
            reversible = '<td class ="danger">&#10142;</td>'
        info['reversible'] = reversible
        info['equation'] = formating.equationStringFromReaction(item)
        modifiers = ''
        for mod in item.getListOfModifiers():
            modifiers += '{}< br / >'.format(mod.getSpecies())
        info['modifiers'] = modifiers
        klaw = item.getKineticLaw()
        info['formula'] = math(klaw)
        info['derived_units'] = derived_units(klaw)

        # fbc
        rfbc = item.getPlugin("fbc")
        if rfbc:
            # TODO: FIX THIS (getting the values for the bounds)
            lb_id, ub_id = rfbc.getLowerFluxBound(), rfbc.getUpperFluxBound()
            lb_p, ub_p = model.getParameter(lb_id), model.getParameter(ub_id)
            lb_value, ub_value = lb_p.getValue(), ub_p.getValue()
            bounds = '<span class="cvterm darkgray">[{}={}, {}={}]</span>'.format(lb_id, lb_value, ub_id, ub_value)
        else:
            bounds = ''
        info['bounds'] = bounds
        items.append(info)

    return items

def listOfObjectives_dict(model):
    items = []
    mfbc = model.getPlugin('fbc')
    if mfbc:
        for item in mfbc.getListOfObjectives():
            info = infoSbase(item)
            info['type'] = item.getType()
            info['flux_objectives'] = str(item.getListOfFluxObjectives())
            items.append(info)
            print(info)
    return items

def listOfEvents_dict(model):
    items = []
    for item in model.getListOfEvents():
        info = infoSbase(item)

        trigger = item.getTrigger()
        info['trigger'] = "{}<br />initialValue = {}<br />persistent = {}< br / >".format(math(trigger),
                                                                                          trigger.initial_value,
                                                                                          trigger.persistent)
        info['priority'] = item.priority
        info['delay'] = item.delay
        assignments = ''
        for eva in item.getListOfEventAssignments():
            assignments += "{} = {}<br />".format(eva.getId(), math(eva))
        info['assignments'] = assignments
        items.append(info)
    return items


##############################
# Helpers
##############################
def notes(item):
    if item.isSetNotes():
        return formating.notesToString(item)
    return ''

def cvterm(item):
    if item.isSetAnnotation():
       return '<div class="cvterm">{}</div>'.format(formating.annotation_to_html(item))
    return ''

def sbo(item):
    if item.getSBOTerm() != -1:
        return '<div class="cvterm"><a href="{}" target="_blank">{}</a></div>'.format(item.getSBOTermAsURL(), item.getSBOTermID())
    return ''

def metaId(item):
    if item.isSetMetaId():
        return "<code>{}</code>".format(item.getMetaId())
    return ''

def annotation(item):
    info = '<div class="cvterm">'
    if item.getSBOTerm() != -1:
        info += '<a href="{}" target="_blank">{}</a><br />'.format(item.getSBOTermAsURL(), item.getSBOTermID())
    if item.isSetAnnotation():
        info += formating.annotation_to_html(item)
    info += '</div>'
    return info

def math(item):
    if item:
        return formating.astnodeToMathML(item.getMath())
    return ''

def boolean(condition):
    if condition:
        return '<td class="success"><span class="glyphicon glyphicon-ok green"></span><span class="invisible">T</span></td>'
    else:
        return '<td class="danger"><span class="glyphicon glyphicon-remove red"><span class="invisible">F</span></span></td>'

def annotation_xml(item):
    if item.isSetAnnotation():
        return '<pre>{}</pre>'.format(item.getAnnotationString().decode('utf-8'))
    return ''

def xml(item):
    return '<textarea style="border:none;">{}</textarea>'.format(item.toSBML())

def derived_units(item):
    if item:
        return formating.stringToMathML(formating.unitDefinitionToString(item.getDerivedUnitDefinition()))
    return ''


########################################

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
