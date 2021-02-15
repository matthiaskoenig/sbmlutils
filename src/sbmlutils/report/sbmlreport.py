"""SBML report.

Create an SBML report from given SBML file or set of SBML files (for instance for comp
models). The model report is implemented based on a standard template language,
which uses the SBML information to render the final document.

The basic steps of template creation are
- configure the engine (jinja2)
- compile template
- render with SBML context

The final report consists of an HTML file with an overview over the SBML elements in
the model.
"""
import logging
import ntpath
import warnings
from pathlib import Path
from typing import Dict, Iterable, List

import jinja2
import libsbml
from jinja2 import TemplateNotFound

from sbmlutils import RESOURCES_DIR, utils
from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.report import formating, mathml, sbmlfilters


logger = logging.getLogger(__name__)

TEMPLATE_DIR = RESOURCES_DIR / "templates"


def create_reports(
    sbml_paths: Iterable[Path],
    output_dir: Path,
    template: str = "report.html",
    promote: bool = False,
    validate: bool = True,
    math_type: str = "cmathml",
):
    """Create individual reports and an overview file.

    :param sbml_paths: paths to SBML files
    :param output_dir: target directory where the report is written
    :param template: which template file to use for rendering
    :param promote: boolean flag to promote local parameters
    :param validate: boolean flag if SBML file be validated (warnings and errors
                     are logged)
    :param math_type: specifies the math rendering mode for the report

    :return:
    """

    # check math type
    math_types = ["cmathml", "pmathml", "latex"]
    if math_type not in math_types:
        raise ValueError(
            f"math_type '{math_type}' not in supported types: '{math_types}'"
        )

    # individual reports
    for sbml_path in sbml_paths:
        logger.info(sbml_path)
        create_report(
            sbml_path=sbml_path,
            output_dir=output_dir,
            template=template,
            promote=promote,
            validate=validate,
            math_type=math_type,
        )

    # write index html (unicode)
    html = _create_index_html(sbml_paths)
    index_path = output_dir / "index.html"
    with open(index_path, "w", encoding="utf-8") as f_index:
        f_index.write(html)


def create_report(
    sbml_path: Path,
    output_dir: Path,
    promote: bool = False,
    template: str = "report.html",
    math_type: str = "cmathml",
    validate: bool = True,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
):
    """Create HTML report for SBML file.

    The SBML file can be validated during report generation.
    Local parameters can be promoted during report generation.

    :param sbml_path: path to SBML file
    :param output_dir: target directory where the report is written
    :param promote: boolean flag to promote local parameters
    :param template: which template file to use for rendering
    :param math_type: specifies the math rendering mode for the report
    :param validate: boolean flag if SBML file be validated (warnings and errors
                     are logged)
    :param log_errors: boolean flag of errors should be logged
    :param units_consistency: boolean flag units consistency
    :param modeling_practice: boolean flag modeling practise

    :return:
    """
    if not isinstance(sbml_path, Path):
        logger.warning(
            f"All paths should be of type 'Path', "
            f"but '{type(sbml_path)}' found for: {sbml_path}"
        )
        sbml_path = Path(sbml_path)
    if not isinstance(output_dir, Path):
        logger.warning(
            f"All paths should be of type 'Path', "
            f"but '{type(output_dir)}' found for: {output_dir}"
        )
        output_dir = Path(output_dir)

    # check paths
    if not sbml_path.exists():
        raise IOError(f"'sbml_path' does not exist: '{sbml_path}'")
    if not output_dir.exists():
        raise IOError(f"'output_dir' does not exist: '{output_dir}'")
    if not output_dir.is_dir():
        raise IOError(f"'output_dir' is not a directory: '{output_dir}'")

    # check math type
    math_types = ["cmathml", "pmathml", "latex"]
    if math_type not in math_types:
        raise ValueError(
            f"math_type '{math_type}' not in supported types: '{math_types}'"
        )

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

    # write html
    html = _create_html(doc, basename, html_template=template, math_type=math_type)
    path_html = output_dir / f"{name}.html"
    with open(path_html, "w", encoding="utf-8") as f_html:
        f_html.write(html)

    logger.info(f"SBML report created: '{path_html.resolve()}'")


def _create_index_html(
    sbml_paths: List[Path], html_template: str = "index.html", offline: bool = True
):
    """Create index.html for given sbml_paths.

    :param sbml_paths: List of paths to SBML files
    :param html_template: which template file to use for rendering
    :param offline: to specify offline report generation for appropriate linking
                    of stylesheet and script files

    :return
    """

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

    return template.render(
        {
            "offline": offline,
            "sbml_basenames": sbml_basenames,
            "sbml_links": sbml_links,
        }
    )


def _create_html(
    doc: libsbml.SBMLDocument,
    basename: str,
    html_template: str = "report.html",
    math_type: str = "cmathml",
    offline: bool = True,
):
    """Create HTML from SBML.

    :param doc: SBML document for creating HTML report
    :param basename: basename of SBML file path
    :param html_template: which template file to use for rendering
    :param math_type: specifies the math rendering mode for the report
    :param offline: to specify offline report generation for appropriate linking of
                    stylesheet and script files

    :return: rendered HTML report template for the SBML document
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

        # context
        c = {
            "offline": offline,
            "basename": basename,
            "values": values,
            "doc": document_dict(doc),
            "modeldefs": listOfModelDefinitions_dict(doc),
            "model": model_dict(model),
            "submodels": listOfSubmodels_dict(model),
            "ports": listOfPorts_dict(model),
            "functions": listOfFunctions_dict(model, math_type),
            "units": listOfUnits_dict(model),
            "compartments": listOfCompartments_dict(model, values, math_type),
            "species": listOfSpecies_dict(model),
            "geneproducts": listOfGeneProducts_dict(model),
            "parameters": listOfParameters_dict(model, values, math_type),
            "assignments": listOfInitialAssignments_dict(model, math_type),
            "rules": listOfRules_dict(model, math_type),
            "reactions": listOfReactions_dict(model, math_type),
            "objectives": listOfObjectives_dict(model),
            "constraints": listOfConstraints_dict(model, math_type),
            "events": listOfEvents_dict(model, math_type),
        }
    else:
        # no model exists
        logging.error(f"No model in SBML file when creating model report: {doc}")
        template = env.get_template("report_no_model.html")
        c = {
            "basename": basename,
            "doc": doc,
        }
    return template.render(c)


# ------------------------
# Information Dictionaries
# ------------------------
def _create_value_dictionary(model: libsbml.Model) -> Dict:
    """Create dictionary of values for model instance.

    :param model: SBML model instance for which values dictionary is to be created
    :return: values dictionary for model
    """
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


def infoSbase(item: libsbml.SBase) -> Dict:
    """Info dictionary for SBase.

    :param item: SBase instance for which info dictionary is to be created
    :return info dictionary for item
    """

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
            ] = f"""
                <br /><i class="fa fa-arrow-circle-right" aria-hidden="true"></i>
                <code>ReplacedBy {submodel_ref}:{sbaseref(replaced_by)}</code>
                """

        # ListOfReplacedElements
        if item_comp.getNumReplacedElements() > 0:
            replaced_elements = []
            for rep_el in item_comp.getListOfReplacedElements():
                submodel_ref = rep_el.getSubmodelRef()
                replaced_elements.append(
                    f"""
                    <br /><i class="fa fa-arrow-circle-left" aria-hidden="true"></i>
                    <code>ReplacedElement {submodel_ref}:{sbaseref(rep_el)}</code>
                    """
                )
            if len(replaced_elements) == 0:
                replaced_elements = ""
            else:
                replaced_elements = "".join(replaced_elements)
            info["replaced_elements"] = replaced_elements

    return info


def document_dict(doc: libsbml.SBMLDocument) -> Dict:
    """Create Info dictonary for SBML document instance.

    :param doc: SBML document for which info dictionary is to be created
    :return: info dictionary for doc
    """

    info = infoSbase(doc)
    packages = [f'<span class="package">L{doc.getLevel()}V{doc.getVersion()}</span>']

    for k in range(doc.getNumPlugins()):
        plugin = doc.getPlugin(k)
        prefix = plugin.getPrefix()
        version = plugin.getPackageVersion()
        packages.append(f'<span class="package">{prefix}-V{version}</span>')
    info["packages"] = " ".join(packages)
    return info


def model_dict(model: libsbml.Model) -> Dict:
    """Create Info dictionary for SBML Model instance.

    :param model: SBML model for which info dictionary is to be created
    :return: info dictionary for model
    """
    info = infoSbase(model)
    info["history"] = formating.modelHistoryToString(model.getModelHistory())

    return info


def listOfModelDefinitions_dict(doc: libsbml.SBMLDocument) -> List[Dict]:
    """Information dicts for ExternalModelDefinitions and ModelDefinitions.

    :param: doc: SBML document enclosing ExternalModelDefinitions and ModelDefinitions
    :return: list of info dictionaries for ExternalModelDefinitions and ModelDefinitions
    """
    items = []
    doc_comp = doc.getPlugin("comp")
    if doc_comp:
        for item in doc_comp.getListOfModelDefinitions():
            info = infoSbase(item)
            info["type"] = type(item).__name__
            items.append(info)
        for item in doc_comp.getListOfExternalModelDefinitions():
            info = infoSbase(item)
            info["type"] = (
                type(item).__name__ + f" (<code>source={item.getSource}</code>)"
            )
            items.append(info)
    return items


def listOfSubmodels_dict(model: libsbml.Model) -> List[Dict]:
    """Information dicts for Submodels.

    :param: model: SBML model enclosing the Submodels
    :return: list of info dictionaries for Submodels within model
    """

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


def sbase_ref_dict(item: libsbml.SBaseRef) -> Dict:
    """Information dictionary of SBaseRef.

    :param item: SBaseRef instance for which information dictionary has to be created
    :return: information dictionary for item
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
    info[
        "referenced_element"
    ] = f"<code>{type(element).__name__}: {element.getId()}</code>"
    return info


def listOfPorts_dict(model: libsbml.Model) -> List[Dict]:
    """
    Information dicts for Ports within the plug-in object for packages used by model.

    :param: model: SBML model instance
    :return: list of info dictionaries for the ports found in the plug-in
    """

    items = []
    model_comp = model.getPlugin("comp")
    if model_comp:
        for item in model_comp.getListOfPorts():
            info = sbase_ref_dict(item)
            items.append(info)
    return items


def listOfFunctions_dict(model: libsbml.Model, math_type: str) -> List[Dict]:
    """Information dicts for Function definitions within the Model instance.

    :param model: SBML model instance enclosing the function definitions
    :param math_type: specifies which math rendering mode to use
    :return: list of info dictionaries for the function definitions in the model
    """

    items = []
    for item in model.getListOfFunctionDefinitions():
        info = infoSbase(item)
        info["math"] = math(item, math_type)
        items.append(info)
    return items


def listOfUnits_dict(model: libsbml.Model) -> List[Dict]:
    """Information dicts for Unit definitions within the Model instance.

    :param: model: SBML model instance enclosing the unit definitions
    :return: list of info dictionaries for the unit definitions in the model
    """

    items = []
    for item in model.getListOfUnitDefinitions():
        info = infoSbase(item)
        info["units"] = formating.formula_to_mathml(
            formating.unitDefinitionToString(item)
        )
        items.append(info)
    return items


def listOfCompartments_dict(
    model: libsbml.Model, values: Dict, math_type: str
) -> List[Dict]:
    """Information dicts for Compartments within the Model instance.

    :param model: SBML model instance containing the compartments
    :param values: dictionary of values
    :param math_type: specifies which math rendering mode to use
    :return: list of info dictionaries for the compartments in the model
    """

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
            size = math(values.get(item.id, ""), math_type)
        info["size"] = size
        items.append(info)
    return items


def listOfSpecies_dict(model: libsbml.Model) -> List[Dict]:
    """Information dicts for Species within the compartments in the Model instance.

    :param: model: SBML model instance containing the species
    :return: list of info dictionaries for the species in the model
    """

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

            info["conversion_factor"] = f"{cf_sid}={cf_value} [{cf_units}]"
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
                    info["fbc_charge"] = f"({sfbc.getCharge()})"
            if ("fbc_formula" in info) or ("fbc_charge" in info):
                info[
                    "fbc"
                ] = f"""
                    <br />
                    <code>
                        {info.get('fbc_formula', '')}{info.get('fbc_charge', '')}
                    </code>
                    """
        items.append(info)
    return items


def listOfGeneProducts_dict(model: libsbml.Model) -> List[Dict]:
    """
    Information dicts for GeneProducts within 'fbc' plug-in object used by the model.

    :param: model: SBML model instance
    :return: list of info dictionaries for the GeneProducts found in the plug-in object
    """

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


def listOfParameters_dict(
    model: libsbml.Model, values: Dict, math_type: str
) -> List[Dict]:
    """Information dicts for Parameters defined within the Model instance.

    :param model: SBML model instance using the Parameters
    :param values: dictionary of values
    :param math_type: specifies which math rendering mode to use
    :return: list of info dictionaries for the parameters used in the model
    """

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
                    f"""No value for parameter via Value, InitialAssignment or
                    AssignmentRule: {item.id}
                    """
                )
            value = math(value_formula, math_type)
        info["value"] = value
        info["derived_units"] = derived_units(item)
        info["constant"] = boolean(item.constant)
        items.append(info)
    return items


def listOfInitialAssignments_dict(model: libsbml.Model, math_type: str) -> List[Dict]:
    """Information dicts for Initial Assignments defined within the Model instance.

    :param model: SBML model instance defining the Initial Assignments
    :param math_type: specifies which math rendering mode to use
    :return: list of info dictionaries for the initial assignments defined in the model
    """

    items = []
    for item in model.getListOfInitialAssignments():
        info = infoSbase(item)
        info["symbol"] = item.symbol
        info["assignment"] = math(item, math_type)
        info["derived_units"] = derived_units(item)
        items.append(info)
    return items


def listOfRules_dict(model: libsbml.Model, math_type: str) -> List[Dict]:
    """Information dicts for Rules defined within the Model instance.

    :param: model: SBML model instance defining the Rules
    :return: list of info dictionaries for the rules defined in the model
    """

    items = []
    for item in model.getListOfRules():
        info = infoSbase(item)
        info["variable"] = formating.ruleVariableToString(item)
        info["assignment"] = math(item, math_type)
        info["derived_units"] = derived_units(item)

        items.append(info)
    return items


def listOfConstraints_dict(model: libsbml.Model, math_type: str) -> List[Dict]:
    """Information dicts for Constraints specified within the Model instance.

    :param model: SBML model instance specified the Constraints
    :param math_type: specifies which math rendering mode to use
    :return: list of info dictionaries for the constraits specified in the model
    """

    items = []
    for item in model.getListOfConstraints():
        info = infoSbase(item)
        info["constraint"] = math(item, math_type)
        items.append(info)
    return items


def listOfReactions_dict(model: libsbml.Model, math_type: str) -> List[Dict]:
    """Information dicts for Reactions occurring in compartments within the model.

    :param model: SBML model instance
    :param math_type: specifies which math rendering mode to use
    :return: list of info dictionaries for the reactions found in the model
    """

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
        info["formula"] = math(klaw, math_type)
        info["derived_units"] = derived_units(klaw)

        # fbc
        info["fbc_bounds"] = formating.boundsStringFromReaction(item, model)
        info["fbc_gpa"] = formating.geneProductAssociationStringFromReaction(item)
        items.append(info)

    return items


def listOfObjectives_dict(model: libsbml.Model) -> List[Dict]:
    """Information dicts for Objective instances defined within the Model instance.

    :param: model: SBML model instance defining the Objectives
    :return: list of info dictionaries for the objectives defined in the model
    """

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
                part = f"{sign}{abs(coefficient)}*{f_obj.getReaction()}"
                flux_objectives.append(part)
            info["flux_objectives"] = " ".join(flux_objectives)
            items.append(info)
    return items


def listOfEvents_dict(model: libsbml.Model, math_type: str) -> List[Dict]:
    """Information dicts for Events defined within the Model instance.

    :param model: SBML model instance defining the Events
    :param math_type: specifies which math rendering mode to use
    :return: list of info dictionaries for the events defined in the model
    """

    items = []
    for item in model.getListOfEvents():
        info = infoSbase(item)

        trigger = item.getTrigger()
        info[
            "trigger"
        ] = f"""
            {math(trigger, math_type)}
            <br />initialValue = {trigger.initial_value}
            <br /> persistent = {trigger.persistent}
            """

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
            assignments += f"{eva.getId()} = {math(eva, math_type)}<br />"
        if len(assignments) == 0:
            assignments = empty_html()
        info["assignments"] = assignments
        items.append(info)
    return items


# -------
# Helpers
# -------
def notes(item: libsbml.SBase) -> str:
    """Convert the SBML object's notes subelement to formatted string.

    :param item: SBML object containing the notes subelement
    :return: formatted string for the notes subelement of the item
    """
    if item.isSetNotes():
        return formating.notes_to_string(item)
    return ""


def cvterm(item: libsbml.SBase) -> str:
    """Create HTML code fragment enclosing cvterm data for the item.

    :param item: SBML object for which cvterm data has to be displayed
    :return: HTML code fragment enclosing cvterm data for the item
    """
    if item.isSetAnnotation():
        return f'<div class="cvterm">{formating.annotation_to_html(item)}</div>'
    return ""


def sbo(item: libsbml.SBase) -> str:
    """Create HTML code fragment enclosing SBOTerm data for the item.

    :param item: SBML object for which SBOTerm data has to be displayed
    :return: HTML code fragment enclosing SBOTerm data for the item
    """

    if item.getSBOTerm() != -1:
        return f"""<div class="cvterm">
                        <a href="{item.getSBOTermAsURL()}" target="_blank">
                            {item.getSBOTermID()}
                        </a>
                    </div>
                """
    return ""


def sbaseref(sref: libsbml.SBaseRef) -> str:
    """Format the SBaseRef instance.

    :param sref: SBaseRef instance
    :return: string containging formatted SBaseRef instance's data
    """

    if sref.isSetPortRef():
        return f"portRef={sref.getPortRef()}"
    elif sref.isSetIdRef():
        return f"idRef={sref.getIdRef()}"
    elif sref.isSetUnitRef():
        return f"unitRef={sref.getUnitRef()}"
    elif sref.isSetMetaIdRef():
        return f"metaIdRef={sref.getMetaIdRef()}"
    return ""


def empty_html() -> str:
    """Create a blank HTML code fragment."""

    return '<i class="fa fa-ban gray"></i>'


def metaid_html(item: libsbml.SBase) -> str:
    """Create metaid data for the item.

    :param item: SBML object for which metaid data has to be generated
    :return: HTML code fragment enclosing metaid data for item
    """
    if item.isSetMetaId():
        return f"<code>{item.getMetaId()}</code>"
    return ""


def id_html(item: libsbml.SBase) -> str:
    """Create info from id and metaid.

    :param item: SBML object for which info is to be generated
    :return: HTML code fragment enclosing info for item
    """

    sid = item.getId()
    meta = metaid_html(item)

    if sid:
        display_sid = sid
        if isinstance(item, libsbml.RateRule) and item.isSetVariable():
            display_sid = "d {}/dt".format(item.getVariable())
        info = f"""
                <td id="{sid}" class="active">
                <span class="package">{display_sid}</span> {meta}
            """
    else:
        if meta:
            info = f'<td class="active">{meta}'
        else:
            info = f'<td class="active">{empty_html()}'

    # create modal information
    info += xml_modal(item)

    return info


def annotation_html(item: libsbml.SBase) -> str:
    """Create annotation HTML content for the item.

    :param item: SBML object for which annotation HTML content is to be generated
    :return: HTML code fragment enclosing annotation for item
    """

    info = '<div class="cvterm">'
    if item.getSBOTerm() != -1:
        info += f"""
            <a href="{item.getSBOTermAsURL()}" target="_blank">
                {item.getSBOTermID()}
            </a><br />
            """
    if item.isSetAnnotation():
        info += formating.annotation_to_html(item)
    info += "</div>"
    return info


def math(item: libsbml.SBase, type: str = "cmathml") -> str:
    """Create MathML content for the item.

    :param item: SBML object for which MathML content is to be generated
    :param type: specifies which math rendering mode to use
    :return: formatted MathML content for the item
    """

    if item:
        math = item.getMath()
        if type == "cmathml":
            return formating.astnode_to_mathml(math)
        elif type == "pmathml":
            cmathml = formating.astnode_to_mathml(math)
            return mathml.cmathml_to_pmathml(cmathml)
        elif type == "latex":
            latex_str = mathml.astnode_to_latex(math)
            return f"$${latex_str}$$"
    return empty_html()


def boolean(condition: bool) -> str:
    """Check the truth value of condition and create corresponding HTML code fragment.

    :param condition: condition for which the truth value is to be checked
    :return: HTML code fragment
    """

    if condition:
        return """
            <td>
                <span class="fas fa-check-circle green"></span>
                <span class="invisible">T</span>
            </td>
        """
    else:
        return '<td><span class=""><span class="invisible">F</span></span></td>'


def annotation_xml(item: libsbml.SBase) -> str:
    """Create Annotation string for the item.

    :param item: SBML object for which MathML content is to be generated
    :return: Annotation string for the item
    """
    if item.isSetAnnotation():
        return f"<pre>{item.getAnnotationString().decode('utf-8')}</pre>"
    return ""


def xml_modal(item: libsbml.SBase) -> str:
    """Create modal information for a given sbase.

    This provides some popup which allows to inspect the xml content of the element.

    :param item: SBML object for which xml content is to be created
    :return: HTML code fragment enclosing the xml content for the item
    """
    # filter sbase
    if type(item) is libsbml.Model:
        return ""

    hash_id = utils._create_hash_id(item)

    info = f"""
      <button type="button" class="btn btn-default btn-xs" data-toggle="modal" data-target="#model-{hash_id}">
        <i class="fa fa-code"></i>
      </button>
      <div class="modal fade" id="model-{hash_id}" role="dialog">
        <div class="modal-dialog modal-lg">
          <div class="modal-content">
            <div class="modal-header"><h4 class="modal-title">{hash_id}</h4></div>
            <div class="modal-body">
                <textarea rows="20" class="form-control" style="min-width: 100%; font-family: 'Courier New'">
                    {xml(item)}
                </textarea>
            </div>
          </div>
        </div>
      </div>
    """
    return info


def xml(item: libsbml.SBase) -> str:
    """Create SBML specification in XML for the item and return HTML code fragment.

    :param item: SBML object for which SBML specification (in XML) has to be created
    :return: HTML code fragment enclosing the SBML specification for the item
    """

    html = f"{item.toSBML()}"

    return html
    # return '<textarea style="border:none;">{}</textarea>'.format(item.toSBML())


def derived_units(item: libsbml.SBase) -> str:
    """Create formatted string for Unit definition object.

    :param item: SBML object from which Unit Definition string is to be created
    :return: formatted string for Unit Definition derived from the item
    """

    if item:
        return formating.formula_to_mathml(
            formating.unitDefinitionToString(item.getDerivedUnitDefinition())
        )
    return ""
