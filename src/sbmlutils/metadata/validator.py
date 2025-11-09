from pathlib import Path
from typing import Union

import libsbml
import pandas as pd
from pymetadata.identifiers.miriam import BQB

from sbmlutils.console import console
from sbmlutils.io.sbml import read_sbml
from sbmlutils.log import get_logger
from pymetadata.core.annotation import RDFAnnotation


logger = get_logger(__name__)


def validate_sbml_annotations(source: Union[Path, str]) -> pd.DataFrame:
    """Validate annotations in a given SBML file.

    :param source: SBML to check
    :return: DataFrame of invalid annotations
    """
    doc: libsbml.SBMLDocument = read_sbml(source=source)
    console.rule(style="white")
    console.print(f"Validate annotations: {source}", style="white bold")
    console.rule(style="white")

    elements = doc.getListOfAllElements()
    element: libsbml.SBase
    invalid_annotations: list = []
    for element in elements:
        if element.isSetAnnotation():
            cvterm: libsbml.CVTerm
            cvterms = element.getCVTerms()

            # console.rule(f"id='{element.id}' | {type(element)} | '{element.name}'", align="left", style="bold white")
            for cvterm in cvterms:
                cvterm.getQualifierType()
                for k in range(cvterm.getNumResources()):

                    resource_uri = cvterm.getResourceURI(k)
                    # console.print(f"{qualifier_type} | {resource_uri}")
                    annotation = RDFAnnotation(qualifier=BQB.IS, resource=resource_uri, validate=False)
                    valid: bool = annotation.validate()
                    if not valid:
                        console.print(
                            f"id='{element.id}' | {type(element).__name__} | '{element.name}' | {resource_uri}",
                            style="warning"
                        )
                        invalid_annotations.append(
                            {
                                "id": element.id,
                                "object": type(element).__name__,
                                "resource": resource_uri,
                            }
                        )
    df = pd.DataFrame(invalid_annotations)
    if len(invalid_annotations) == 0:
        console.print("All annotations valid", style="success")
    else:
        console.print(df.to_string())
        console.print("Invalid annotations", style="error")
    console.rule(style="white")
    return df

