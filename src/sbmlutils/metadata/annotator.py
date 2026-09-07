"""Annotation of SBML models.

Handle the XML annotations and notes in SBML.
Annotate models from information in annotation csv files.
Thereby a model can be fully annotated from information
stored in a separate annotation store.

Annotation is performed via searching for ontology terms which describe the model and
model components.
A standard workflow is looking up the components for instance in things like OLS
ontology lookup service.
"""

import logging
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import libsbml
import pandas as pd
from pymetadata.core.annotation import RDFAnnotation as Annotation
from pymetadata.core.miriam import BQB, BQM

from sbmlutils import utils
from sbmlutils.console import console
from sbmlutils.io.sbml import read_sbml, write_sbml

from ..validation import check

logger = logging.getLogger(__name__)


def annotate_sbml(
    source: Path | str, annotations_path: Path, filepath: Path
) -> libsbml.SBMLDocument:
    """Annotate a given SBML file with the provided annotations.

    :param source: SBML to annotation
    :param annotations_path: external file with annotations
    :param filepath: annotated SBML file
    :return: annotated SBMLDocument
    """
    doc: libsbml.SBMLDocument = read_sbml(source=source)

    # annotate
    if not os.path.exists(str(annotations_path)):
        raise OSError(f"Annotation file does not exist: {annotations_path}")
    external_annotations = ModelAnnotator.read_annotations(
        annotations_path, file_format="*"
    )
    doc = annotate_sbml_doc(doc, external_annotations)

    # write annotated sbml
    write_sbml(doc, filepath=filepath)

    console.print(f"Model annotated: file://{filepath}", style="success")
    return doc


def annotate_sbml_doc(
    doc: libsbml.SBMLDocument, external_annotations: list["ExternalAnnotation"]
) -> libsbml.SBMLDocument:
    """Annotates given SBML document using the annotations file.

    :param doc: SBMLDocument
    :param external_annotations: ModelAnnotations
    :return: annotated SBMLDocument
    """
    annotator = ModelAnnotator(doc, external_annotations)
    annotator.annotate_model()
    return doc


class ExternalAnnotation:
    """Class for handling SBML annotations defined in external source.

    This corresponds to a single entry in the external annotation file.
    Allows to handle more complex annotation scenarios, e.g. patterns for
    identifiers.

    The columns are:
        pattern
        sbml_type
        annotation_type
        qualifier
        resource
        name
    """

    # allowed SBML types for annotation
    _sbml_types = frozenset(
        [
            "document",
            "model",
            "unit",
            "reaction",
            "transporter",
            "species",
            "compartment",
            "parameter",
            "rule",
            "fbc:geneproduct",
        ]
    )
    _annotation_types = frozenset(["rdf", "formula", "charge"])

    def __init__(self, d: dict[str, Any]):
        """Initialize ExternalAnnotation.

        Args:
            d: one row of the annotation file, `pattern`, `sbml_type`,
                `annotation_type` and `resource` are required, `qualifier` and
                `name` are optional.

        Raises:
            KeyError: if a required column is missing
            ValueError: if a value is not one of the supported choices
        """
        self.d = d
        self.pattern: str = str(d["pattern"])
        self.sbml_type: str = str(d["sbml_type"]).lower()
        self.annotation_type: str = str(d["annotation_type"]).lower()
        self.resource: str = str(d["resource"])
        self.name: str | None = d.get("name") or None

        # only an rdf annotation carries a qualifier
        self.qualifier: BQB | BQM | None = None
        if self.annotation_type == "rdf":
            qualifier = d.get("qualifier")
            self.qualifier = ExternalAnnotation._parse_qualifier_str(
                str(qualifier).upper() if qualifier else None
            )

        self.check()

    @staticmethod
    def _parse_qualifier_str(qualifier: str | None) -> BQB | BQM:
        if qualifier is None:
            raise ValueError("Qualifier must be provided.")

        if not qualifier.startswith("BQ"):
            raise ValueError(f"Qualifier must start with BQM_ or BQB_: '{qualifier}'")
        if qualifier.startswith("BQM_"):
            return BQM[qualifier[4:]]
        return BQB[qualifier[4:]]

    def check(self) -> None:
        """Check for valid choices.

        :raise: ValueError
        """
        if self.sbml_type not in self._sbml_types:
            raise ValueError(
                f"Invalid sbml_type '{self.sbml_type}'. "
                f"Supported types are '{self._sbml_types}'\n"
                f"{self.d}"
            )
        if self.annotation_type not in self._annotation_types:
            raise ValueError(
                f"Invalid annotation_type '{self.annotation_type}'. "
                f"Supported types are '{self._annotation_types}'\n"
                f"{self.d}"
            )

    def __str__(self) -> str:
        """Convert to string."""
        return str(self.d)


class ModelAnnotator:
    """Helper class for annotating SBML models."""

    def __init__(
        self, doc: libsbml.SBMLDocument, annotations: Iterable[ExternalAnnotation]
    ):
        """Initialize ModelAnnotator.

        :param doc: SBMLDocument
        :param annotations: iterable of ModelAnnotation
        """
        self.doc = doc
        self.model = doc.getModel()
        self.annotations = annotations

        # prepare dictionary for lookup of ids
        self.id_dict = self._get_ids_from_model()

    def annotate_model(self) -> None:
        """Annotate the model with the given annotations."""
        # writes all annotations
        for a in self.annotations:
            pattern = a.pattern
            if a.sbml_type == "document":
                elements = [self.doc]
            else:
                # lookup of allowed ids for given sbmlutils type
                ids = self.id_dict.get(a.sbml_type, None)
                elements = []
                if ids:
                    # find the subset of ids matching the pattern
                    pattern_ids = ModelAnnotator._get_matching_ids(ids, pattern)
                    if not pattern_ids:
                        logger.warning(
                            "No SBML objects found matching SId annotation pattern: '%s'",
                            pattern,
                        )
                    elements = ModelAnnotator._elements_from_ids(
                        self.model, pattern_ids, sbml_type=a.sbml_type
                    )

            self._annotate_elements(elements, a)

    def _get_ids_from_model(self) -> dict[str, list[str]]:
        """Create dictionary of ids for given model for lookup.

        :return:
        """
        id_dict = {}
        id_dict["model"] = [self.model.getId()]

        lof = self.model.getListOfUnitDefinitions()
        if lof:
            id_dict["unit"] = [item.getId() for item in lof]

        lof = self.model.getListOfCompartments()
        if lof:
            id_dict["compartment"] = [item.getId() for item in lof]

        lof = self.model.getListOfSpecies()
        if lof:
            id_dict["species"] = [item.getId() for item in lof]

        lof = self.model.getListOfParameters()
        if lof:
            id_dict["parameter"] = [item.getId() for item in lof]

        lof = self.model.getListOfReactions()
        if lof:
            id_dict["reaction"] = [item.getId() for item in lof]

        lof = self.model.getListOfRules()
        if lof:
            id_dict["rule"] = [item.getVariable() for item in lof]

        lof = self.model.getListOfEvents()
        if lof:
            id_dict["event"] = [item.getId() for item in lof]

        fbc_model = self.model.getPlugin("fbc")
        if fbc_model is not None:
            lof = fbc_model.getListOfGeneProducts()
            if lof:
                id_dict["fbc:geneproduct"] = [item.getId() for item in lof]

        return id_dict

    @staticmethod
    def _get_matching_ids(ids: Iterable[str], pattern: str) -> list[str]:
        """Ids matching the regular expression."""
        return [s for s in ids if re.match(pattern, s)]

    @staticmethod
    def _elements_from_ids(
        model: libsbml.Model, sbml_ids: Iterable[str], sbml_type: str | None = None
    ) -> list[libsbml.SBase]:
        """Get list of SBML elements from given ids.

        :param model: SBML model
        :param sbml_ids: SBML SIds
        :param sbml_type: type of SBML objects
        :return:
        """
        elements = []
        for sid in sbml_ids:
            if sbml_type == "rule":
                e = model.getRuleByVariable(sid)
            elif sbml_type == "unit":
                e = model.getUnitDefinition(sid)
            else:
                # returns the first element with id
                # FIXME: this is very slow in a loop, better solution required via
                e = model.getElementBySId(sid)
            if e is None:
                if sid == model.getId():
                    e = model
                else:
                    logger.warning("Element not found for sid: '%s'.", sid)
                    continue
            elements.append(e)
        return elements

    def _annotate_elements(
        self, elements: Iterable[libsbml.SBase], ex_a: ExternalAnnotation
    ) -> None:
        """Annotate given elements with annotation.

        :param elements: SBase elements to annotate
        :param ex_a: annotation
        :return:
        """
        for e in elements:
            if ex_a.annotation_type == "rdf":
                if ex_a.qualifier is None:
                    raise ValueError(f"An rdf annotation needs a qualifier: {ex_a}")
                annotation = Annotation(
                    qualifier=ex_a.qualifier,
                    resource=ex_a.resource,
                )
                ModelAnnotator.annotate_sbase(e, annotation)

                # write SBO terms based on the SBO RDF
                if annotation.collection == "sbo":
                    e.setSBOTerm(annotation.term)

            elif ex_a.annotation_type in ["formula", "charge"]:
                # via fbc species plugin, so check that species first
                if ex_a.sbml_type != "species":
                    logger.error(
                        "Chemical formula or Charge can only be set on species."
                    )
                else:
                    s = self.model.getSpecies(e.getId())
                    splugin = s.getPlugin("fbc")
                    if splugin is None:
                        logger.error(
                            "FbcSpeciesPlugin does not exist, add "
                            "`packages=['Package.FBC']` "
                            "to model definition."
                        )
                    else:
                        if ex_a.annotation_type == "formula":
                            splugin.setChemicalFormula(ex_a.resource)
                        elif ex_a.annotation_type == "charge":
                            splugin.setCharge(int(ex_a.resource))
            else:
                raise ValueError(
                    f"Annotation type not supported: '{ex_a.annotation_type}'"
                )

    @staticmethod
    def get_SBMLQualifier(qualifier_str: str, qualifier_type: str) -> str:
        """Lookup of SBMLQualifier for given qualifier string.

        :param qualifier_type: BQB or BQM
        :return: SBML qualifier string
        """
        if qualifier_str not in libsbml.__dict__:
            raise ValueError(f"Qualifier not supported: {qualifier_str}")

        qtype = libsbml.__dict__.get(qualifier_str)

        qualifier: str
        if qualifier_type == "BQB":
            qualifier = str(libsbml.BiolQualifierType_toString(qtype))
        elif qualifier_type == "BQM":
            qualifier = str(libsbml.ModelQualifierType_toString(qtype))
        return qualifier

    @staticmethod
    def annotate_sbase(sbase: libsbml.SBase, annotation: Annotation) -> None:
        """Annotate SBase based on given annotation data.

        :param sbase: libsbml.SBase
        :param annotation: Annotation
        :return:
        """
        qualifier, resource = annotation.qualifier.value, annotation.resource_normalized
        cv: libsbml.CVTerm = libsbml.CVTerm()

        # set correct type of qualifier
        if isinstance(qualifier, str):
            if qualifier.startswith("BQB"):
                cv.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)

                sbml_qualifier = ModelAnnotator.get_SBMLQualifier(qualifier, "BQB")
                success = check(
                    cv.setBiologicalQualifierType(sbml_qualifier),
                    f"Set biological qualifier: '{sbml_qualifier}'",
                )
                if not success:
                    logger.error(
                        "Could not set biological qualifier '%s' for '%s'.",
                        qualifier,
                        sbase,
                    )
            elif qualifier.startswith("BQM"):
                cv.setQualifierType(libsbml.MODEL_QUALIFIER)
                sbml_qualifier = ModelAnnotator.get_SBMLQualifier(qualifier, "BQM")
                success = check(
                    cv.setModelQualifierType(sbml_qualifier),
                    f"Set model qualifier: '{sbml_qualifier}'",
                )
                if not success:
                    logger.error(
                        "Could not set model qualifier '%s' for '%s'.", qualifier, sbase
                    )
            else:
                logger.error("Unsupported qualifier: '%s' for '%s'.", qualifier, sbase)
        else:
            msg = (
                f"qualifier is not a string, but: '{qualifier}' of type "
                f"'{type(qualifier)}' for '{sbase}'."
            )
            logger.error(msg)
            raise ValueError(msg)

        success = check(cv.addResource(resource), f"Add resource: '{resource}'.")
        if not success:
            logger.error("Could not add resource: %s for '%s'.", resource, sbase)

        # meta id has to be set
        if not sbase.isSetMetaId():
            sbase.setMetaId(utils.create_metaid(sbase))

        success = check(sbase.addCVTerm(cv), f"Add cvterm: '{cv}'.")

        if not success:
            logger.error(
                "Annotation RDF for CVTerm '%s' could not be written for '%s'.",
                cv,
                sbase,
            )
            logger.error(libsbml.OperationReturnValue_toString(success))
            logger.error("%s, %s, %s", sbase, qualifier, resource)

    # --- File IO ---

    @staticmethod
    def read_annotations_df(file_path: Path, file_format: str = "*") -> pd.DataFrame:
        """Read annotations from given file into DataFrame.

        Supports "xlsx", "tsv", "csv", "json", "*"

        :param file_path: either path to file, or data in dict format
        :param file_format: annotation file format
        :return: pandas.DataFrame
        """
        _filename, file_extension = os.path.splitext(file_path)
        if file_format == "*":
            file_format = file_extension[1:]  # remove leading dot

        formats = ["xlsx", "tsv", "csv", "json"]
        if file_format not in formats:
            raise OSError(
                f"Annotation format '{file_format}' not in supported formats: "
                f"'{formats}'"
            )

        if file_extension != ("." + file_format):
            logger.warning(
                "format '%s' not matching file extension '%s' for file_path '%s'",
                file_format,
                file_extension,
                file_path,
            )

        if file_format == "tsv":
            df = pd.read_csv(file_path, sep="\t", comment="#", skip_blank_lines=True)
        elif file_format == "csv":
            df = pd.read_csv(file_path, sep=",", comment="#", skip_blank_lines=True)
        elif file_format == "json":
            df = pd.read_json(file_path)
        elif file_format == "xlsx":
            df = pd.read_excel(file_path, comment="#", engine="openpyxl")

        df.dropna(axis="index", inplace=True, how="all")
        return df

    @staticmethod
    def read_annotations(
        file_path: Path, file_format: str = "*"
    ) -> list[ExternalAnnotation]:
        """Read annotations from given file into DataFrame.

        Supports "xlsx", "tsv", "csv", "json", "*"

        :param file_path: either path to file, or data in dict format
        :param file_format: annotation file format
        :return: list of annotation objects
        """
        df = ModelAnnotator.read_annotations_df(
            file_path=file_path, file_format=file_format
        )
        entries = df.to_dict("records")
        annotations = []
        for entry in entries:
            annotations.append(ExternalAnnotation(entry))

        return annotations
