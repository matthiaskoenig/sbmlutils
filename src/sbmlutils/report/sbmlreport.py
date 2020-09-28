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
import codecs
import logging
import ntpath
import warnings
from pathlib import Path
from typing import Iterable, List

import jinja2
import libsbml
from jinja2 import TemplateNotFound

from sbmlutils import RESOURCES_DIR, utils
from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.report import formating, sbmlfilters


logger = logging.getLogger(__name__)

TEMPLATE_DIR = RESOURCES_DIR / "templates"  # template location


def create_reports(
    sbml_paths: Iterable[Path],
    output_dir: Path,
    template="report.html",
    promote=False,
    validate=True,
):
    """Creates individual reports and an overview file.

    :param sbml_paths: paths to SBML files
    :param output_dir:
    :param template:
    :param promote:
    :param validate:
    :return:
    """
    # individual reports
    for sbml_path in sbml_paths:
        logger.info(sbml_path)
        create_report(
            sbml_path=sbml_path,
            output_dir=output_dir,
            template=template,
            promote=promote,
            validate=validate,
        )

    # write index html (unicode)
    html = _create_index_html(sbml_paths)
    index_path = output_dir / "index.html"
    # FIXME: is this still necessary in python 3?
    f_index = codecs.open(index_path, encoding="utf-8", mode="w")
    f_index.write(html)
    f_index.close()


def create_report(
    sbml_path: Path,
    output_dir: Path,
    promote: bool = False,
    template: str = "report.html",
    validate: bool = True,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
):
    """Creates HTML report for SBML file.

    The SBML file can be validated during report generation.
    Local parameters can be promoted during report generation.

    :param sbml_path: path to SBML file
    :param output_dir: target directory where the report is written
    :param promote: boolean flag to promote local parameters
    :param template: which template file to use for rendering
    :param validate: boolean flag if SBML file be validated (warnings and errors are logged)
    :param log_errors: boolean flag of errors should be logged
    :param units_consistency: boolean flag units consistency
    :param modeling_practice: boolean flag modeling practise

    :return:
    """
    if not isinstance(sbml_path, Path):
        logger.warning(
            f"All paths should be of type 'Path', but '{type(sbml_path)}' found for: {sbml_path}"
        )
        sbml_path = Path(sbml_path)
    if not isinstance(output_dir, Path):
        logger.warning(
            f"All paths should be of type 'Path', but '{type(output_dir)}' found for: {output_dir}"
        )
        output_dir = Path(output_dir)

    # check paths
    if not sbml_path.exists():
        raise IOError(f"'sbml_path' does not exist: '{sbml_path}'")
    if not output_dir.exists():
        raise IOError(f"'output_dir' does not exist: '{output_dir}'")
    if not output_dir.is_dir():
        raise IOError(f"'output_dir' is not a directory: '{output_dir}'")

    # read sbml
    doc = read_sbml(
        source=sbml_path,
        promote=promote,
        validate=validate,
        log_errors=log_errors,
        units_consistency=units_consistency,
        modeling_practice=modeling_practice,
    )

    # write sbml to report directory
    basename = sbml_path.name
    name = ".".join(basename.split(".")[:-1])
    write_sbml(doc, filepath=output_dir / basename)

    # write html (unicode)
    html = _create_html(doc, basename, html_template=template)
    path_html = output_dir / f"{name}.html"
    # FIXME: ist this still necessary
    f_html = codecs.open(path_html, encoding="utf-8", mode="w")
    f_html.write(html)
    f_html.close()

    logger.info(f"SBML report created: '{path_html.resolve()}'")


def _create_index_html(
    sbml_paths: List[Path], html_template: str = "index.html", offline: bool = True
):
    """Create index.html for given sbml_paths."""

    # template environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
        extensions=["jinja2.ext.autoescape"],
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(html_template)

    sbml_basenames = [ntpath.basename(path) for path in sbml_paths]
    sbml_links = []
    for basename in sbml_basenames:
        tokens = basename.split(".")
        name = ".".join(tokens[:-1]) + ".html"
        sbml_links.append(name)

    # Context
    c = {
        "offline": offline,
        "sbml_basenames": sbml_basenames,
        "sbml_links": sbml_links,
    }
    return template.render(c)


def _create_html(doc, basename, html_template="report.html", offline=True):
    """Create HTML from SBML.

    :param doc:
    :type doc:
    :param html_template:
    :type html_template:
    :return:
    :rtype:
    """
    # template environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
        extensions=["jinja2.ext.autoescape"],
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # additional SBML filters
    for key in sbmlfilters.filters:
        env.filters[key] = getattr(sbmlfilters, key)

    model = doc.getModel()
    if model is not None:
        try:
            template = env.get_template(html_template)
        except TemplateNotFound as err:
            logger.error(f"TemplateNotFound: {TEMPLATE_DIR} / {html_template}; {err}")

        values = _create_value_dictionary(model)

        # Context
        c = {
            "offline": offline,
            "basename": basename,
            "values": values,
            "doc": document_dict(doc),
            "modeldefs": listOfModelDefinitions_dict(doc),
            "model": model_dict(model),
            "submodels": listOfSubmodels_dict(model),
            "ports": listOfPorts_dict(model),
            "functions": listOfFunctions_dict(model),
            "units": listOfUnits_dict(model),
            "compartments": listOfCompartments_dict(model, values),
            "species": listOfSpecies_dict(model),
            "geneproducts": listOfGeneProducts_dict(model),
            "parameters": listOfParameters_dict(model, values),
            "assignments": listOfInitialAssignments_dict(model),
            "rules": listOfRules_dict(model),
            "reactions": listOfReactions_dict(model),
            "objectives": listOfObjectives_dict(model),
            "constraints": listOfConstraints_dict(model),
            "events": listOfEvents_dict(model),
        }
    else:
        # no model exists
        logging.error(
            "No model in SBML file when creating model report: {}".format(doc)
        )
        template = env.get_template("report_no_model.html")
        c = {
            "basename": basename,
            "doc": doc,
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
    """ Info dictionary for SBase. """

    info = {
        "object": item,
        "id": item.getId(),
        "metaId": metaid_html(item),
        "sbo": sbo(item),
        "cvterm": cvterm(item),
        "notes": notes(item),
        "annotation": annotation_html(item),
    }

    if item.isSetName():
        name = item.name
    else:
        name = empty_html()
    info["name"] = name
    info["id_html"] = id_html(item)

    # comp
    item_comp = item.getPlugin("comp")
    if item_comp and type(item_comp) == libsbml.CompSBasePlugin:
        # ReplacedBy
        if item_comp.isSetReplacedBy():
            replaced_by = item_comp.getReplacedBy()
            submodel_ref = replaced_by.getSubmodelRef()
            info[
                "replaced_by"
            ] = '<br /><i class="fa fa-arrow-circle-right" aria-hidden="true"></i><code>ReplacedBy {}:{}</code>'.format(
                submodel_ref, sbaseref(replaced_by)
            )

        # ListOfReplacedElements
        if item_comp.getNumReplacedElements() > 0:
            replaced_elements = []
            for rep_el in item_comp.getListOfReplacedElements():
                submodel_ref = rep_el.getSubmodelRef()
                replaced_elements.append(
                    '<br /><i class="fa fa-arrow-circle-left" aria-hidden="true"></i><code>ReplacedElement {}:{}</code>'.format(
                        submodel_ref, sbaseref(rep_el)
                    )
                )
            if len(replaced_elements) == 0:
                replaced_elements = ""
            else:
                replaced_elements = "".join(replaced_elements)
            info["replaced_elements"] = replaced_elements

    return info


def document_dict(doc):
    info = infoSbase(doc)
    packages = [
        '<span class="package">L{}V{}</span>'.format(doc.getLevel(), doc.getVersion())
    ]

    for k in range(doc.getNumPlugins()):
        plugin = doc.getPlugin(k)
        prefix = plugin.getPrefix()
        version = plugin.getPackageVersion()
        packages.append('<span class="package">{}-V{}</span>'.format(prefix, version))
    info["packages"] = " ".join(packages)
    return info


def model_dict(model):
    info = infoSbase(model)
    info["history"] = formating.modelHistoryToString(model.getModelHistory())

    return info


def listOfModelDefinitions_dict(doc):
    """ Information dicts for ExternalModelDefinitions and ModelDefinitions"""
    items = []
    doc_comp = doc.getPlugin("comp")
    if doc_comp:
        for item in doc_comp.getListOfModelDefinitions():
            info = infoSbase(item)
            info["type"] = type(item).__name__
            items.append(info)
        for item in doc_comp.getListOfExternalModelDefinitions():
            info = infoSbase(item)
            info["type"] = type(item).__name__ + " (<code>source={}</code>)".format(
                item.getSource()
            )
            items.append(info)
    return items


def listOfSubmodels_dict(model):
    items = []
    model_comp = model.getPlugin("comp")
    if model_comp:
        for item in model_comp.getListOfSubmodels():
            info = infoSbase(item)
            info["model_ref"] = item.getModelRef()

            deletions = []
            for deletion in item.getListOfDeletions():
                deletions.append(sbaseref(deletion))
            if len(deletions) == 0:
                deletions = empty_html()
            else:
                deletions = "<br />".join(deletions)
            info["deletions"] = deletions

            time_conversion = empty_html()
            if item.isSetTimeConversionFactor():
                time_conversion = item.getTimeConversionFactor()
            info["time_conversion"] = time_conversion
            extent_conversion = empty_html()
            if item.isSetExtentConversionFactor():
                extent_conversion = item.getExtentConversionFactor()
            info["extent_conversion"] = extent_conversion
            items.append(info)
    return items


def sbase_ref_dict(item):
    """Information dictionary of SbaseRef

    :param sbase_ref:
    :return:
    """
    info = infoSbase(item)
    port_ref = ""
    if item.isSetPortRef():
        port_ref = item.getPortRef()
    info["port_ref"] = port_ref
    id_ref = ""
    if item.isSetIdRef():
        id_ref = item.getIdRef()
    info["id_ref"] = id_ref
    unit_ref = ""
    if item.isSetUnitRef():
        unit_ref = item.getUnitRef()
    info["unit_ref"] = unit_ref
    metaid_ref = ""
    if item.isSetMetaIdRef():
        metaid_ref = item.getMetaIdRef()
    info["metaid_ref"] = metaid_ref
    element = item.getReferencedElement()
    info["referenced_element"] = "<code>{}: {}</code>".format(
        type(element).__name__, element.getId()
    )
    return info


def listOfPorts_dict(model):
    items = []
    model_comp = model.getPlugin("comp")
    if model_comp:
        for item in model_comp.getListOfPorts():
            info = sbase_ref_dict(item)
            items.append(info)
    return items


def listOfFunctions_dict(model):
    items = []
    for item in model.getListOfFunctionDefinitions():
        info = infoSbase(item)
        info["math"] = math(item)
        items.append(info)
    return items


def listOfUnits_dict(model):
    items = []
    for item in model.getListOfUnitDefinitions():
        info = infoSbase(item)
        info["units"] = formating.formula_to_mathml(
            formating.unitDefinitionToString(item)
        )
        items.append(info)
    return items


def listOfCompartments_dict(model, values):
    items = []
    for item in model.getListOfCompartments():
        info = infoSbase(item)
        info["units"] = item.units
        if item.isSetSpatialDimensions():
            spatial_dimensions = item.spatial_dimensions
        else:
            spatial_dimensions = empty_html()
        info["spatial_dimensions"] = spatial_dimensions
        info["constant"] = boolean(item.constant)
        info["derived_units"] = derived_units(item)
        if item.isSetSize():
            size = item.size
        else:
            size = math(values.get(item.id, ""))
        info["size"] = size
        items.append(info)
    return items


def listOfSpecies_dict(model):
    items = []
    for item in model.getListOfSpecies():
        info = infoSbase(item)
        info["compartment"] = item.compartment
        info["has_only_substance_units"] = boolean(item.has_only_substance_units)
        info["boundary_condition"] = boolean(item.boundary_condition)
        info["constant"] = boolean(item.constant)
        if item.isSetInitialAmount():
            initial_amount = item.initial_amount
        else:
            initial_amount = empty_html()
        info["initial_amount"] = initial_amount
        if item.isSetInitialConcentration():
            initial_concentration = item.initial_concentration
        else:
            initial_concentration = empty_html()
        info["initial_concentration"] = initial_concentration
        info["units"] = item.getUnits()
        info["substance_units"] = item.substance_units
        info["derived_units"] = derived_units(item)

        if item.isSetConversionFactor():
            cf_sid = item.getConversionFactor()
            cf_p = model.getParameter(cf_sid)
            cf_value = cf_p.getValue()
            cf_units = cf_p.getUnits()

            info["conversion_factor"] = "{}={} [{}]".format(cf_sid, cf_value, cf_units)
        else:
            info["conversion_factor"] = empty_html()

        # fbc
        sfbc = item.getPlugin("fbc")
        if sfbc:
            if sfbc.isSetChemicalFormula():
                info["fbc_formula"] = sfbc.getChemicalFormula()
            if sfbc.isSetCharge():
                c = sfbc.getCharge()
                if c != 0:
                    info["fbc_charge"] = "({})".format(sfbc.getCharge())
            if ("fbc_formula" in info) or ("fbc_charge" in info):
                info["fbc"] = "<br /><code>{} {}</code>".format(
                    info.get("fbc_formula", ""), info.get("fbc_charge", "")
                )
        items.append(info)
    return items


def listOfGeneProducts_dict(model: libsbml.Model):
    items = []
    mfbc = model.getPlugin("fbc")
    if mfbc:
        for item in mfbc.getListOfGeneProducts():
            info = infoSbase(item)
            info["label"] = item.label
            associated_species = empty_html()
            if item.isSetAssociatedSpecies():
                associated_species = item.associated_species
            info["associated_species"] = associated_species
            items.append(info)
    return items


def listOfParameters_dict(model, values):
    items = []
    for item in model.getListOfParameters():
        info = infoSbase(item)
        info["units"] = item.units
        if item.isSetValue():
            value = item.value
        else:
            value_formula = values.get(item.id, None)
            if value_formula is None:
                warnings.warn(
                    "No value for parameter via Value, InitialAssignment or AssignmentRule: {}".format(
                        item.id
                    )
                )
            value = math(value_formula)
        info["value"] = value
        info["derived_units"] = derived_units(item)
        info["constant"] = boolean(item.constant)
        items.append(info)
    return items


def listOfInitialAssignments_dict(model):
    items = []
    for item in model.getListOfInitialAssignments():
        info = infoSbase(item)
        info["symbol"] = item.symbol
        info["assignment"] = math(item)
        info["derived_units"] = derived_units(item)
        items.append(info)
    return items


def listOfRules_dict(model):
    items = []
    for item in model.getListOfRules():
        info = infoSbase(item)
        info["variable"] = formating.ruleVariableToString(item)
        info["assignment"] = math(item)
        info["derived_units"] = derived_units(item)

        items.append(info)
    return items


def listOfConstraints_dict(model):
    items = []
    for item in model.getListOfConstraints():
        info = infoSbase(item)
        info["constraint"] = math(item)
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
        info["reversible"] = reversible
        info["equation"] = formating.equationStringFromReaction(item)
        modifiers = []
        for mod in item.getListOfModifiers():
            modifiers.append(mod.getSpecies())
        if len(modifiers) == 0:
            modifiers = empty_html()
        else:
            modifiers = "<br />".join(modifiers)
        info["modifiers"] = modifiers
        klaw = item.getKineticLaw()
        info["formula"] = math(klaw)
        info["derived_units"] = derived_units(klaw)

        # fbc
        info["fbc_bounds"] = formating.boundsStringFromReaction(item, model)
        info["fbc_gpa"] = formating.geneProductAssociationStringFromReaction(item)
        items.append(info)

    return items


def listOfObjectives_dict(model):
    items = []
    mfbc = model.getPlugin("fbc")
    if mfbc:
        for item in mfbc.getListOfObjectives():
            info = infoSbase(item)
            info["type"] = item.getType()

            flux_objectives = []
            for f_obj in item.getListOfFluxObjectives():
                coefficient = f_obj.getCoefficient()
                if coefficient < 0.0:
                    sign = "-"
                else:
                    sign = "+"
                part = "{}{}*{}".format(sign, abs(coefficient), f_obj.getReaction())
                flux_objectives.append(part)
            info["flux_objectives"] = " ".join(flux_objectives)
            items.append(info)
    return items


def listOfEvents_dict(model):
    items = []
    for item in model.getListOfEvents():
        info = infoSbase(item)

        trigger = item.getTrigger()
        info["trigger"] = "{}<br />initialValue = {}<br />persistent = {}".format(
            math(trigger), trigger.initial_value, trigger.persistent
        )

        priority = empty_html()
        if item.isSetPriority():
            priority = item.getPriority()
        info["priority"] = priority

        delay = empty_html()
        if item.isSetDelay():
            delay = item.getDelay()
        info["delay"] = delay
        assignments = ""
        for eva in item.getListOfEventAssignments():
            assignments += "{} = {}<br />".format(eva.getId(), math(eva))
        if len(assignments) == 0:
            assignments = empty_html()
        info["assignments"] = assignments
        items.append(info)
    return items


##############################
# Helpers
##############################
def notes(item):
    if item.isSetNotes():
        return formating.notes_to_string(item)
    return ""


def cvterm(item):
    if item.isSetAnnotation():
        return '<div class="cvterm">{}</div>'.format(formating.annotation_to_html(item))
    return ""


def sbo(item):
    if item.getSBOTerm() != -1:
        return '<div class="cvterm"><a href="{}" target="_blank">{}</a></div>'.format(
            item.getSBOTermAsURL(), item.getSBOTermID()
        )
    return ""


def sbaseref(sref):
    """Formats the SBaseRef

    :param sref:
    :return:
    """
    if sref.isSetPortRef():
        return "portRef={}".format(sref.getPortRef())
    elif sref.isSetIdRef():
        return "idRef={}".format(sref.getIdRef())
    elif sref.isSetUnitRef():
        return "unitRef={}".format(sref.getUnitRef())
    elif sref.isSetMetaIdRef():
        return "metaIdRef={}".format(sref.getMetaIdRef())
    return ""


def empty_html():
    return '<i class="fa fa-ban gray"></i>'


def metaid_html(item):
    if item.isSetMetaId():
        return "<code>{}</code>".format(item.getMetaId())
    return ""


def id_html(item):
    """Create info from id and metaid

    :param item:
    :return:
    """
    sid = item.getId()
    meta = metaid_html(item)

    if sid:
        display_sid = sid
        if isinstance(item, libsbml.RateRule) and item.isSetVariable():
            display_sid = "d {}/dt".format(item.getVariable())
        info = '<td id="{}" class="active"><span class="package">{}</span> {}'.format(
            sid, display_sid, meta
        )
    else:
        if meta:
            info = '<td class="active">{}'.format(meta)
        else:
            info = '<td class="active">{}'.format(empty_html())

    # create modal information
    info += xml_modal(item)

    return info


def annotation_html(item):
    info = '<div class="cvterm">'
    if item.getSBOTerm() != -1:
        info += '<a href="{}" target="_blank">{}</a><br />'.format(
            item.getSBOTermAsURL(), item.getSBOTermID()
        )
    if item.isSetAnnotation():
        info += formating.annotation_to_html(item)
    info += "</div>"
    return info


def math(item):
    if item:
        return formating.astnode_to_mathml(item.getMath())
    return empty_html()


def boolean(condition):
    if condition:
        return '<td><span class="fas fa-check-circle green"></span><span class="invisible">T</span></td>'
    else:
        return '<td><span class=""><span class="invisible">F</span></span></td>'


def annotation_xml(item):
    if item.isSetAnnotation():
        return "<pre>{}</pre>".format(item.getAnnotationString().decode("utf-8"))
    return ""


def xml_modal(item):
    """Creates modal information for a given sbase.

    This provides some popup which allows to inspect the xml content of the element.

    :param item:
    :return:
    """
    # filter sbases
    if type(item) is libsbml.Model:
        return ""

    hash_id = utils._create_hash_id(item)

    info = """
      <button type="button" class="btn btn-default btn-xs" data-toggle="modal" data-target="#model-{}"><i class="fa fa-code"></i></button>
      <div class="modal fade" id="model-{}" role="dialog">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header"><h4 class="modal-title">{}</h4></div>
            <div class="modal-body"><textarea rows="20" class="form-control" style="min-width: 100%; font-family: 'Courier New'">{}</textarea></div>
          </div>
        </div>
      </div>
    """.format(
        hash_id, hash_id, hash_id, xml(item)
    )
    return info


def xml(item):
    html = "{}".format(item.toSBML())

    return html
    # return '<textarea style="border:none;">{}</textarea>'.format(item.toSBML())


def derived_units(item):
    if item:
        return formating.formula_to_mathml(
            formating.unitDefinitionToString(item.getDerivedUnitDefinition())
        )
    return ""
