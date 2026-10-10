"""Validation of the annotations of a model against the registry."""

import logging
from pathlib import Path

import libsbml
import pandas as pd
from pymetadata.core.annotation import RDFAnnotation
from pymetadata.core.miriam import BQB

from sbmlutils.io.sbml import read_sbml
from sbmlutils.utils import all_elements

logger = logging.getLogger(__name__)


def validate_sbml_annotations(source: Path | str) -> pd.DataFrame:
    """Validate annotations in a given SBML file.

    :param source: SBML to check
    :return: DataFrame of invalid annotations
    """
    doc: libsbml.SBMLDocument = read_sbml(source=source)
    logger.info("Validate annotations: %s", source)

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
                        logger.warning(
                            "id='%s' | %s | '%s' | %s",
                            element.getId(),
                            type(element).__name__,
                            element.getName(),
                            resource_uri,
                        )
                        invalid_annotations.append(
                            {
                                "id": element.getId(),
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
