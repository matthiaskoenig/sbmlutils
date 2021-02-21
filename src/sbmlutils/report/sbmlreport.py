"""SBML report.

Create an SBML report from given SBML file or set of SBML files (for instance for comp
models). The model report is implemented based on a standard template language,
which uses the SBML information to render the final document.

The basic steps of template creation are
- configure the engine (jinja2)
- compile template
- render with SBML context

The final report is returned as a variable containing the HTML file content with an
overview over the SBML elements in the model.
"""
import logging
import ntpath
from pathlib import Path
from typing import Any, Dict, List

import jinja2
import libsbml
from jinja2 import TemplateNotFound

from sbmlutils import RESOURCES_DIR
from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.report import sbmlfilters
from sbmlutils.report.sbmlinfo import SBMLModelInfo


logger = logging.getLogger(__name__)

TEMPLATE_DIR = RESOURCES_DIR / "templates"


def _check_report_math_type(math_type: str) -> None:
    """Check the math type in the report."""
    math_types = ["cmathml", "pmathml", "latex"]
    if math_type not in math_types:
        raise ValueError(
            f"math_type '{math_type}' not in supported types: '{math_types}'"
        )


def create_reports(
    sbml_paths: List[Path],
    output_dir: Path,
    template: str = "report.html",
    promote: bool = False,
    validate: bool = True,
    math_type: str = "cmathml",
) -> List[str]:
    """Create model reports and return a list of HTML content for each model.

    Models are provided as a list of paths. By default math in the report is rendered
    using Content Mathml (cmathml).
    For all models a model report is generated. In addition an index.html is generated
    for the various models.

    :param sbml_paths: paths to SBML files
    :param output_dir: target directory where the SBML file is written
    :param template: which template file to use for rendering
    :param promote: boolean flag to promote local parameters
    :param validate: boolean flag if SBML file should be validated
                     (warnings and errors are logged)
    :param math_type: specifies the math rendering mode for the report. Allowed values
                      are 'cmathml' - Content MathML, 'pmathml' - presentation MathML,
                      or 'latex' - Latex formula.

    :return: List of HTML content of reports
    """
    html_reports = []
    for sbml_path in sbml_paths:
        logger.info(f"\tab create report '{sbml_path}")
        html_report = create_report(
            sbml_path=sbml_path,
            output_dir=output_dir,
            template=template,
            promote=promote,
            validate=validate,
            math_type=math_type,
        )

        if html_report is not None:
            html_reports.append(html_report)

    return html_reports


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
) -> str:
    """Create HTML report and return the content as a variable.

    The SBML file can be validated during report generation.
    Local parameters can be promoted during report generation.

    :param sbml_path: path to SBML file
    :param output_dir: target directory where the SBML file is written
    :param promote: boolean flag to promote local parameters
    :param template: which template file to use for rendering
    :param math_type: specifies the math rendering mode for the report
    :param validate: boolean flag if SBML file be validated (warnings and errors
                     are logged)
    :param log_errors: boolean flag of errors should be logged
    :param units_consistency: boolean flag units consistency
    :param modeling_practice: boolean flag modeling practise

    :return: string variable containing content of the generated HTML report
    """
    # validate and check arguments
    _check_report_math_type(math_type)

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

    # write sbml
    basename = sbml_path.name
    write_sbml(doc, filepath=output_dir / basename)

    # write html
    html = _create_html(doc, basename, html_template=template, math_type=math_type)
    return html


def _create_index_html(
    sbml_paths: List[Path], html_template: str = "index.html", offline: bool = True
) -> str:
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
) -> str:
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
    context: Dict[str, Any] = {
        "offline": offline,
        "basename": basename,
    }
    if model is not None:
        try:
            template = env.get_template(html_template)
        except TemplateNotFound as err:
            logger.error(f"TemplateNotFound: {TEMPLATE_DIR} / {html_template}; {err}")

        model_info = SBMLModelInfo(doc=doc, model=model, math_render=math_type)
        context.update(model_info.info)
    else:
        # no model exists
        logging.error(f"No model in SBML file when creating model report: {doc}")
        template = env.get_template("report_no_model.html")
        context.update(
            {
                "doc": doc,
            }
        )
    return template.render(context)
