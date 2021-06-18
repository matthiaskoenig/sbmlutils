"""SBML report.

Create an SBML report from given SBML file or set of SBML files (for instance for comp
models). The model report is implemented based on a standard template language,
which uses the SBML information to render the final document.

The final report is returned as a variable containing the HTML file content with an
overview over the SBML elements in the model.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List

import libsbml

from sbmlutils.io.sbml import read_sbml, write_sbml
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo


logger = logging.getLogger(__name__)


def create_reports(
    sbml_paths: List[Path],
    output_dir: Path,
    promote: bool = False,
    validate: bool = True,
) -> List[str]:
    """Create model reports and return a list of HTML content for each model.

    Models are provided as a list of paths. By default math in the report is rendered
    using Content Mathml (cmathml).
    For all models a model report is generated. In addition an index.html is generated
    for the various models.

    :param sbml_paths: paths to SBML files
    :param output_dir: target directory where the SBML file is written
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
            promote=promote,
            validate=validate,
        )

        if html_report is not None:
            html_reports.append(html_report)

    return html_reports


def create_report(
    sbml_path: Path,
    output_dir: Path,
    promote: bool = False,
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
    :param validate: boolean flag if SBML file be validated (warnings and errors
                     are logged)
    :param log_errors: boolean flag of errors should be logged
    :param units_consistency: boolean flag units consistency
    :param modeling_practice: boolean flag modeling practise

    :return: string variable containing content of the generated HTML report
    """

    # validate and check arguments

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

    logging.error(f"No model in SBML file when creating model report: {doc}")

    # return JSON serialized model info
    return _get_serialized_model_info(doc)


def _get_serialized_model_info(
    doc: libsbml.SBMLDocument,
    math_type: str = "cmathml",
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

    model = doc.getModel()

    if model is not None:
        model_info = SBMLDocumentInfo(doc=doc, model=model, math_render=math_type)

        serialized_model_info = model_info.info

        return serialized_model_info
    else:
        # no model exists
        logging.error(f"No model in SBML file when creating model report: {doc}")
