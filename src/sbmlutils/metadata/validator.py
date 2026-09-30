"""Validation of the annotations of a model against the registry."""

import logging
from pathlib import Path

import libsbml
import pandas as pd
from pymetadata.core.annotation import RDFAnnotation
from pymetadata.core.miriam import BQB

from sbmlutils.io.sbml import read_sbml

logger = logging.getLogger(__name__)


def validate_sbml_annotations(source: Path | str) -> pd.DataFrame:
    """Validate annotations in a given SBML file.

    :param source: SBML to check
    :return: DataFrame of invalid annotations
    """
    doc: libsbml.SBMLDocument = read_sbml(source=source)
    logger.info("Validate annotations: %s", source)

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
                    annotation = RDFAnnotation(
                        qualifier=BQB.IS, resource=resource_uri, validate=False
                    )
                    valid: bool = annotation.validate()
                    if not valid:
                        logger.warning(
                            "id='%s' | %s | '%s' | %s",
                            element.id,
                            type(element).__name__,
                            element.name,
                            resource_uri,
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
        logger.info("All annotations valid")
    else:
        logger.error("Invalid annotations\n%s", df.to_string())
    return df
