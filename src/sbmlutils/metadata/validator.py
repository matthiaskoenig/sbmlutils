"""Validation of the annotations of a model against the registry."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import libsbml
from pymetadata.core.annotation import RDFAnnotation
from pymetadata.core.miriam import BQB
from rich.table import Table
from rich.text import Text

from sbmlutils.console import console, path_text
from sbmlutils.io.sbml import read_sbml
from sbmlutils.utils import all_elements

if TYPE_CHECKING:
    import pandas as pd

logger = logging.getLogger(__name__)


def validate_sbml_annotations(source: Path | str) -> "pd.DataFrame":
    """Validate annotations in a given SBML file.

    :param source: SBML to check
    :return: DataFrame of invalid annotations, which is printed as a table on
        the console of the package, see `sbmlutils.console`
    """
    doc: libsbml.SBMLDocument = read_sbml(source=source)

    element: libsbml.SBase
    invalid_annotations: list = []
    for element in all_elements(doc):
        if element.isSetAnnotation():
            cvterm: libsbml.CVTerm
            cvterms = element.getCVTerms()

            for cvterm in cvterms:
                cvterm.getQualifierType()
                for k in range(cvterm.getNumResources()):
                    resource_uri = cvterm.getResourceURI(k)
                    annotation = RDFAnnotation(
                        qualifier=BQB.IS, resource=resource_uri, validate=False
                    )
                    valid: bool = annotation.validate()
                    if not valid:
                        invalid_annotations.append(
                            {
                                "id": element.getId(),
                                "object": type(element).__name__,
                                "name": element.getName(),
                                "resource": resource_uri,
                            }
                        )
    import pandas as pd

    df = pd.DataFrame(invalid_annotations)
    _print_invalid_annotations(source, invalid_annotations)
    return df


def _print_invalid_annotations(
    source: Path | str, invalid_annotations: list[dict[str, str]]
) -> None:
    """Print the result of an annotation validation as a table.

    Args:
        source: the validated SBML, a path is printed as a link
        invalid_annotations: one row per invalid annotation
    """
    location = (
        path_text(source)
        if isinstance(source, Path) or not str(source).lstrip().startswith("<")
        else Text("SBML string")
    )
    if not invalid_annotations:
        console.print(Text.assemble(("annotations valid", "bold green"), " ", location))
        return

    table = Table(
        title=Text.assemble(
            (f"{len(invalid_annotations)} invalid annotation(s)", "bold red"),
            " in ",
            location,
        ),
        title_justify="left",
    )
    for column in ("id", "object", "name", "resource"):
        table.add_column(column, overflow="fold")
    for row in invalid_annotations:
        table.add_row(
            *(Text(row[column]) for column in ("id", "object", "name", "resource"))
        )
    console.print(table)
