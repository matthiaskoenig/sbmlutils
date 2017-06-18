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


def _create_html(doc, basename, html_template='report.html', offline=True):
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
            'offline': offline,

            'basename': basename,
            'values': values,

            'doc': document_dict(doc),
            'modeldefs': listOfModelDefinitions_dict(doc),
            'model': model_dict(model),
            'submodels': listOfSubmodels_dict(model),
            'ports': listOfPorts_dict(model),
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
        sid = assignment.getSymbol()
        values[sid] = assignment
    # rules
    for rule in model.getListOfRules():
        sid = rule.getVariable()
        values[sid] = rule

    return values


def infoSbase(item):
    info = {
        'object': item,
        'id': item.id,
        'metaId': metaId(item),
        'sbo': sbo(item),
        'cvterm': cvterm(item),
        'notes': notes(item),
        'annotation': annotation(item)
    }

    if item.isSetName():
        name = item.name
    else:
        name = empty_html()
    info['name'] = name
    info['id_html'] = id_html(item)

    # comp
    item_comp = item.getPlugin('comp')
    if item_comp and type(item_comp) == libsbml.CompSBasePlugin:
        # ReplacedBy
        if item_comp.isSetReplacedBy():
            replaced_by = item_comp.getReplacedBy()
            submodel_ref = replaced_by.getSubmodelRef()
            info['replaced_by'] = '<br /><i class="fa fa-arrow-circle-right" aria-hidden="true"></i><code>ReplacedBy {}:{}</code>'.format(submodel_ref, sbaseref(replaced_by))

        # ListOfReplacedElements
        libsbml.CompSBasePlugin
        if item_comp.getNumReplacedElements() > 0:
            replaced_elements = []
            for rep_el in item_comp.getListOfReplacedElements():
                submodel_ref = rep_el.getSubmodelRef()
                replaced_elements.append('<br /><i class="fa fa-arrow-circle-left" aria-hidden="true"></i><code>ReplacedElement {}:{}</code>'.format(submodel_ref, sbaseref(rep_el)))
            if len(replaced_elements) == 0:
                replaced_elements = ''
            else:
                replaced_elements = ''.join(replaced_elements)
            info['replaced_elements'] = replaced_elements

    return info

def document_dict(doc):
    info = infoSbase(doc)
    packages = ['<span class="package">L{}V{}</span>'.format(doc.getLevel(), doc.getVersion())]

    for k in range(doc.getNumPlugins()):
        plugin = doc.getPlugin(k)
        prefix = plugin.getPrefix()
        version = plugin.getPackageVersion()
        packages.append('<span class="package">{}-V{}</span>'.format(prefix, version))
    info['packages'] = " ".join(packages)
    return info


def model_dict(model):
    info = infoSbase(model)
    info['history'] = formating.modelHistoryToString(model.getModelHistory())

    return info


def listOfModelDefinitions_dict(doc):
    """ Information dicts for ExternalModelDefinitions and ModelDefinitions"""
    items = []
    doc_comp = doc.getPlugin('comp')
    if doc_comp:
        for item in doc_comp.getListOfModelDefinitions():
            info = infoSbase(item)
            info['type'] = type(item).__name__
            items.append(info)
        for item in doc_comp.getListOfExternalModelDefinitions():
            info = infoSbase(item)
            info['type'] = type(item).__name__ + " (<code>source={}</code>)".format(item.getSource())
            items.append(info)
    return items


def listOfSubmodels_dict(model):
    items = []
    model_comp = model.getPlugin('comp')
    if model_comp:
        for item in model_comp.getListOfSubmodels():
            info = infoSbase(item)
            info['model_ref'] = item.getModelRef()

            deletions = []
            for deletion in item.getListOfDeletions():
                deletions.append(sbaseref(deletion))
            if len(deletions) == 0:
                deletions = empty_html()
            else:
                deletions = "<br />".join(deletions)
            info['deletions'] = deletions

            time_conversion = empty_html()
            if item.isSetTimeConversionFactor():
                time_conversion = item.getTimeConversionFactor()
            info['time_conversion'] = time_conversion
            extent_conversion = empty_html()
            if item.isSetExtentConversionFactor():
                extent_conversion = item.getExtentConversionFactor()
            info['extent_conversion'] = extent_conversion
            items.append(info)
    return items


def sbase_ref_dict(item):
    """ Information dictionary of SbaseRef
    
    :param sbase_ref: 
    :return: 
    """
    info = infoSbase(item)
    port_ref = ''
    if item.isSetPortRef():
        port_ref = item.getPortRef()
    info['port_ref'] = port_ref
    id_ref = ''
    if item.isSetIdRef():
        id_ref = item.getIdRef()
    info['id_ref'] = id_ref
    unit_ref = ''
    if item.isSetUnitRef():
        unit_ref = item.getUnitRef()
    info['unit_ref'] = unit_ref
    metaid_ref = ''
    if item.isSetMetaIdRef():
        metaid_ref = item.getMetaIdRef()
    info['metaid_ref'] = metaid_ref
    element = item.getReferencedElement()
    info['referenced_element'] = '<code>{}: {}</code>'.format(type(element).__name__, element.getId())
    return info


def listOfPorts_dict(model):
    items = []
    model_comp = model.getPlugin('comp')
    if model_comp:
        for item in model_comp.getListOfPorts():
            info = sbase_ref_dict(item)
            items.append(info)
    return items

def listOfFunctions_dict(model):
    items = []
    for item in model.getListOfFunctionDefinitions():
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
            spatial_dimensions = empty_html()
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
            initial_amount = item.initial_amount
        else:
            initial_amount = empty_html()
        info['initial_amount'] = initial_amount
        if item.isSetInitialConcentration():
            initial_concentration = item.initial_concentration
        else:
            initial_concentration = empty_html()
        info['initial_concentration'] = initial_concentration
        info['substance_units'] = item.substance_units
        info['derived_units'] = derived_units(item)
        info['xml'] = xml(item)

        # fbc
        sfbc = item.getPlugin("fbc")
        if sfbc:
            if sfbc.isSetChemicalFormula():
                info['fbc_formula'] = sfbc.getChemicalFormula()
            if sfbc.isSetCharge():
                c = sfbc.getCharge()
                if c is not 0:
                    info['fbc_charge'] = '({})'.format(sfbc.getCharge())
            if ('fbc_formula' in info) or ('fbc_charge' in info):
                info['fbc'] = "<br /><code>{} {}</code>".format(info.get('fbc_formula', ''), info.get('fbc_charge', ''))
        items.append(info)
    return items

def listOfGeneProducts_dict(model):
    items = []
    mfbc = model.getPlugin("fbc")
    if mfbc:
        for item in mfbc.getListOfGeneProducts():
            info = infoSbase(item)
            info['label'] = item.label
            associated_species = empty_html()
            if item.isSetAssociatedSpecies():
                associated_species = item.associated_species
            info['associated_species'] = associated_species
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
            from pprint import pprint
            value_formula = values.get(item.id, None)
            if value_formula is None:
                warnings.warn("No value for parameter via Value, InitialAssignment or AssignmentRule: {}".format(item.id))
            value = math(value_formula)
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
        modifiers = []
        for mod in item.getListOfModifiers():
            modifiers.append(mod.getSpecies())
        if len(modifiers) == 0:
            modifiers = empty_html()
        else:
            modifiers = '<br />'.join(modifiers)
        info['modifiers'] = modifiers
        klaw = item.getKineticLaw()
        info['formula'] = math(klaw)
        info['derived_units'] = derived_units(klaw)

        # fbc
        info['fbc_bounds'] = formating.boundsStringFromReaction(item, model)
        info['fbc_gpa'] = formating.geneProductAssociationStringFromReaction(item)
        items.append(info)

    return items

def listOfObjectives_dict(model):
    items = []
    mfbc = model.getPlugin('fbc')
    if mfbc:
        for item in mfbc.getListOfObjectives():
            info = infoSbase(item)
            info['type'] = item.getType()

            flux_objectives = []
            for f_obj in item.getListOfFluxObjectives():
                coefficient = f_obj.getCoefficient()
                if coefficient < 0.0:
                    sign = '-'
                else:
                    sign = '+'
                part = "{}{}*{}".format(sign, abs(coefficient), f_obj.getReaction())
                flux_objectives.append(part)
            info['flux_objectives'] = " ".join(flux_objectives)
            items.append(info)
    return items

def listOfEvents_dict(model):
    items = []
    for item in model.getListOfEvents():
        info = infoSbase(item)

        trigger = item.getTrigger()
        info['trigger'] = "{}<br />initialValue = {}<br />persistent = {}".format(math(trigger),
                                                                                  trigger.initial_value,
                                                                                  trigger.persistent)

        priority = empty_html()
        if item.isSetPriority():
            priority = item.getPriority()
        info['priority'] = priority

        delay = empty_html()
        if item.isSetDelay():
            delay = item.getDelay()
        info['delay'] = delay
        assignments = ''
        for eva in item.getListOfEventAssignments():
            assignments += "{} = {}<br />".format(eva.getId(), math(eva))
        if len(assignments) == 0:
            assignments = empty_html()
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

def sbaseref(sref):
    """ Formats the SBaseRef

    :param sref:
    :return:
    """
    if sref.isSetPortRef():
        return 'portRef={}'.format(sref.getPortRef())
    elif sref.isSetIdRef():
        return 'idRef={}'.format(sref.getIdRef())
    elif sref.isSetUnitRef():
        return 'unitRef={}'.format(sref.getUnitRef())
    elif sref.isSetMetaIdRef():
        return 'metaIdRef={}'.format(sref.getMetaIdRef())
    return ''

def empty_html():
    return '<i class="fa fa-ban gray"></i>'

def metaId(item):
    if item.isSetMetaId():
        return "<code>{}</code>".format(item.getMetaId())
    return ''


def id_html(item):
    """ Create info from id and metaid

    :param item:
    :return:
    """
    id = item.getId()
    meta = metaId(item)
    if id:
        if type(item) == libsbml.RateRule:
            full_id = 'd {}/dt'.format(id)
        else:
            full_id = id

        info = '<td id="{}" class="active"><span class="package">{}</span> {}'.format(id, full_id, meta)
        if id is not None and (type(item) is not libsbml.Model):
            info += xml_modal(item)
    else:
        if meta:
            info = '<td class="active">{}'.format(meta)
        else:
            info = '<td class="active">{}'.format(empty_html())
    return info


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
    return empty_html()

def boolean(condition):
    if condition:
        return '<td><span class="glyphicon glyphicon-ok green"></span><span class="invisible">T</span></td>'
    else:
        return '<td><span class="glyphicon glyphicon-remove red"><span class="invisible">F</span></span></td>'

def annotation_xml(item):
    if item.isSetAnnotation():
        return '<pre>{}</pre>'.format(item.getAnnotationString().decode('utf-8'))
    return ''

def xml_modal(item):
    info = '''
      <button type="button" class="btn btn-default btn-xs" data-toggle="modal" data-target="#model-{}"><i class="fa fa-code"></i></button>
      <div class="modal fade" id="model-{}" role="dialog">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header"><h4 class="modal-title">{}</h4></div>
            <div class="modal-body"><textarea rows="20" class="form-control" style="min-width: 100%; font-family: 'Courier New'">{}</textarea></div>
          </div>
        </div>
      </div>
    '''.format(item.id, item.id, item.id, xml(item))
    return info


def xml(item):
    html = '{}'.format(item.toSBML())

    return html
    # return '<textarea style="border:none;">{}</textarea>'.format(item.toSBML())

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
