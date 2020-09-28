"""
Annotation of SBML models.

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
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Union

import libsbml
import pandas as pd

from sbmlutils import utils
from sbmlutils.io.sbml import read_sbml, write_sbml

from .miriam import *


LOGGER = logging.getLogger(__name__)


def annotate_sbml(
    source: Union[Path, str], annotations_path: Path, filepath: Path
) -> libsbml.SBMLDocument:
    """
    Annotate a given SBML file with the provided annotations.

    :param source: SBML to annotation
    :param annotations_path: external file with annotations
    :param filepath: annotated SBML file
    :return: annotated SBMLDocument
    """
    doc = read_sbml(source=source)

    # annotate
    if not os.path.exists(str(annotations_path)):
        raise IOError(f"Annotation file does not exist: {annotations_path}")
    external_annotations = ModelAnnotator.read_annotations(
        annotations_path, file_format="*"
    )
    doc = annotate_sbml_doc(doc, external_annotations)  # type: libsbml.SBMLDocument

    # write annotated sbml
    write_sbml(doc, filepath=filepath)
    return doc


def annotate_sbml_doc(
    doc: libsbml.SBMLDocument, external_annotations: List["ExternalAnnotation"]
) -> libsbml.SBMLDocument:
    """Annotates given SBML document using the annotations file.

    :param doc: SBMLDocument
    :param external_annotations: ModelAnnotations
    :return: annotated SBMLDocument
    """
    annotator = ModelAnnotator(doc, external_annotations)
    annotator.annotate_model()
    return doc


class Annotation:
    """Annotation class.

    Basic storage of annotation information. This consists of the relation
    and the the resource.
    The annotations can be attached to other objects thereby forming
    triples which can be converted to RDF.

    Resource can be either:
        - `http(s)://identifiers.org/collection/term`, i.e., a identifiers.org URI
        - `collection/term`, i.e., the combination of collection and term
        - `http(s)://arbitrary.url`, an arbitrary URL
    """

    # TODO: load the xrefs, synonyms and definitions from OLS, i.e., not
    # only checking of the annotations, but getting the full information
    # from the OLS
    def __init__(self, qualifier, resource):
        """

        :param qualifier: BQM or BQB term
        :param resource:
        """
        if not qualifier:
            raise ValueError(
                "MIRIAM qualifiers are required for annotation, but no "
                "qualifier for resource '{resource}' was provided."
            )
        if not resource:
            raise ValueError(
                f"resource is required for annotation, but resource is emtpy "
                f"'{qualifier} {resource}'."
            )
        if not isinstance(resource, str):
            raise ValueError(
                f"resource must be string, but found '{resource} {type(resource)}'."
            )

        self.qualifier = qualifier
        self.collection = None
        self.term = None

        # handle urls
        if resource.startswith("http"):
            match = IDENTIFIERS_ORG_PATTERN.match(resource)
            if match:
                # handle identifiers.org pattern
                self.collection, self.term = match.group(1), match.group(2)
            else:
                # other urls are directly stored as resources without collection
                self.collection = None
                self.term = resource
                LOGGER.warning(
                    "%s does not conform to " "http(s)://identifiers.org/collection/id",
                    resource,
                )
        else:
            # get term and collection
            tokens = resource.split("/")
            if len(tokens) < 2:
                LOGGER.error(
                    "Resource `{}` could not be split in collection and term. "
                    "A given resource must be of the form "
                    "`collection/term` or an url starting with "
                    "`http(s)://`)".format(resource)
                )
                self.collection = None
                self.term = resource
            else:
                self.collection = tokens[0]
                self.term = "/".join(tokens[1:])

        self.validate()

    @staticmethod
    def from_tuple(t):
        """Constructor from tuple."""
        qualifier, resource = t[0], t[1]
        return Annotation(qualifier=qualifier, resource=resource)

    @property
    def resource(self):
        """Resource for annotations.
        :return:
        """
        if self.collection:
            return "{}/{}/{}".format(IDENTIFIERS_ORG_PREFIX, self.collection, self.term)
        else:
            return self.term

    def to_dict(self):
        return OrderedDict(
            [
                ("qualifier", self.qualifier.value),
                ("collection", self.collection),
                ("term", self.term),
                ("resource", self.resource),
            ]
        )

    @staticmethod
    def check_term(collection, term):
        """Checks that a given term follows id pattern for existing collection.

        :param collection:
        :param term:
        :return:
        """
        entry = MIRIAM_COLLECTION.get(collection, None)
        if not entry:
            logging.error(
                "The given MIRIAM collection `{}` in annotation"
                "`{}/{}` does not exist.".format(collection, collection, term)
            )
            return False

        p = re.compile(entry["pattern"])
        m = p.match(term)
        if not m:
            logging.error(
                "Term `{}` did not match pattern "
                "`{}` for collection `{}`.".format(term, entry["pattern"], collection)
            )
            return False

        return True

    @staticmethod
    def check_qualifier(qualifier):
        """Checks that the qualifier is an allowed qualifier.

        :param qualifier:
        :return:
        """
        if not isinstance(qualifier, (BQB, BQM)):
            supported_qualifiers = [e.value for e in BQB] + [e.value for e in BQM]

            raise ValueError(
                f"qualifier '{qualifier}' is not in supported qualifiers: "
                f"{supported_qualifiers}"
            )

    def validate(self):
        self.check_qualifier(self.qualifier)
        if self.collection:
            self.check_term(collection=self.collection, term=self.term)


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

    # possible columns in annotation file
    _keys = ["pattern", "sbml_type", "annotation_type", "qualifier", "resource", "name"]
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

    def __init__(self, d):
        self.d = d
        for key in self._keys:
            # optional fields
            if key in ["qualifier", "name"]:
                value = d.get(key, "")
            else:
                # required fields
                value = d[key]
                if key in ["sbml_type", "annotation_type"]:
                    value = value.lower()
                if key in ["qualifer"]:
                    value = value.upper()

            setattr(self, key, value)

        if self.annotation_type == "rdf":
            self.qualifier = ExternalAnnotation._parse_qualifier(self.qualifier)
        else:
            self.qualifier = None

        self.check()

    @staticmethod
    def _parse_qualifier(qualifier):
        if not qualifier.startswith("BQ"):
            raise ValueError(
                "Qualifier must start with BQM_ or BQB_: `{}`".format(qualifier)
            )
        bq = None
        if qualifier.startswith("BQM_"):
            bq = BQM[qualifier[4:]]
        elif qualifier.startswith("BQB_"):
            bq = BQB[qualifier[4:]]
        if bq is None:
            raise ValueError("Qualifier could not be parsed: `{}`".format(qualifier))
        return bq

    def check(self):
        """ Checks for valid choices """
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

    def __str__(self):
        return str(self.d)


class ModelAnnotator:
    """ Helper class for annotating SBML models. """

    def __init__(
        self, doc: libsbml.SBMLDocument, annotations: Iterable[ExternalAnnotation]
    ):
        """Constructor.

        :param doc: SBMLDocument
        :param annotations: iterable of ModelAnnotation
        """
        self.doc = doc
        self.model = doc.getModel()
        self.annotations = annotations

        # prepare dictionary for lookup of ids
        self.id_dict = self._get_ids_from_model()

    def annotate_model(self):
        """
        Annotates the model with the given annotations.
        """
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
                    elements = ModelAnnotator._elements_from_ids(
                        self.model, pattern_ids, sbml_type=a.sbml_type
                    )

            self._annotate_elements(elements, a)

    def _get_ids_from_model(self):
        """Create dictionary of ids for given model for lookup.

        :return:
        """
        id_dict = dict()
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
    def _get_matching_ids(ids: Iterable[str], pattern: str) -> List[str]:
        """Ids matching the regular expression."""
        return [s for s in ids if re.match(pattern, s)]

    @staticmethod
    def _elements_from_ids(
        model: libsbml.Model, sbml_ids: Iterable[str], sbml_type: str = None
    ) -> List[libsbml.SBase]:
        """
        Get list of SBML elements from given ids.

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
                e = model.getElementBySId(sid)
            if e is None:
                if sid == model.getId():
                    e = model
                else:
                    logging.warning(f"Element not found for sid: '{sid}'.")
                    continue
            elements.append(e)
        return elements

    def _annotate_elements(self, elements, ex_a: ExternalAnnotation):
        """Annotate given elements with annotation.

        :param elements: SBase elements to annotate
        :param ex_a: annotation
        :return:
        """
        for e in elements:
            if ex_a.annotation_type == "rdf":
                annotation = Annotation(
                    qualifier=ex_a.qualifier, resource=ex_a.resource
                )
                ModelAnnotator.annotate_sbase(e, annotation)

                # write SBO terms based on the SBO RDF
                if annotation.collection == "sbo":
                    e.setSBOTerm(annotation.term)

            elif ex_a.annotation_type in ["formula", "charge"]:
                # via fbc species plugin, so check that species first
                if ex_a.sbml_type != "species":
                    LOGGER.error(
                        "Chemical formula or Charge can only be " "set on species."
                    )
                else:
                    s = self.model.getSpecies(e.getId())
                    splugin = s.getPlugin("fbc")
                    if splugin is None:
                        LOGGER.error(
                            "FBC SPlugin not found for species, " "no fbc: {}".format(s)
                        )
                    else:
                        if ex_a.annotation_type == "formula":
                            splugin.setChemicalFormula(ex_a.resource)
                        elif ex_a.annotation_type == "charge":
                            splugin.setCharge(int(ex_a.resource))
            else:
                raise ValueError(
                    "Annotation type not supported: " "{}".format(ex_a.annotation_type)
                )

    @staticmethod
    def get_SBMLQualifier(qualifier_str):
        """ Lookup of SBMLQualifier for given qualifier string. """

        # FIXME: better lookup with MIRIAM
        if qualifier_str not in libsbml.__dict__:
            raise ValueError("Qualifier not supported: {}".format(qualifier_str))
        return libsbml.__dict__.get(qualifier_str)

    @staticmethod
    def annotate_sbase(sbase: libsbml.SBase, annotation: Annotation):
        """Annotate SBase based on given annotation data

        :param sbase: libsbml.SBase
        :param annotation: Annotation
        :return:
        """
        qualifier, resource = annotation.qualifier.value, annotation.resource
        cv = libsbml.CVTerm()  # type: libsbml.CVTerm

        # set correct type of qualifier
        if qualifier.startswith("BQB"):
            cv.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
            sbml_qualifier = ModelAnnotator.get_SBMLQualifier(qualifier)
            cv.setBiologicalQualifierType(sbml_qualifier)
        elif qualifier.startswith("BQM"):
            cv.setQualifierType(libsbml.MODEL_QUALIFIER)
            sbml_qualifier = ModelAnnotator.get_SBMLQualifier(qualifier)
            cv.setModelQualifierType(sbml_qualifier)
        else:
            LOGGER.error("Unsupported qualifier: {}".format(qualifier))

        cv.addResource(resource)

        # meta id has to be set
        if not sbase.isSetMetaId():
            sbase.setMetaId(utils.create_metaid(sbase))

        success = sbase.addCVTerm(cv)

        if success != 0:
            LOGGER.error("RDF not written: ", success)
            LOGGER.error(libsbml.OperationReturnValue_toString(success))
            LOGGER.error("{}, {}, {}".format(object, qualifier, resource))

    # --- File IO ---

    @staticmethod
    def read_annotations_df(file_path: Path, file_format: str = "*"):
        """Reads annotations from given file into DataFrame.

        Supports "xlsx", "tsv", "csv", "json", "*"

        :param file_path: either path to file, or data in dict format
        :param file_format: annotation file format
        :return: pandas.DataFrame
        """
        filename, file_extension = os.path.splitext(file_path)
        if file_format == "*":
            file_format = file_extension[1:]  # remove leading dot

        formats = ["xlsx", "tsv", "csv", "json"]
        if file_format not in formats:
            raise IOError(
                "Annotation format '{}' not in supported formats: '{}'".format(
                    file_format, formats
                )
            )

        if file_extension != ("." + file_format):
            logging.warning(
                "format '{}' not matching file extension '{}' for file_path '{}'".format(
                    file_format, file_extension, file_path
                )
            )

        if file_format == "tsv":
            df = pd.read_csv(file_path, sep="\t", comment="#", skip_blank_lines=True)
        elif file_format == "csv":
            df = pd.read_csv(file_path, sep=",", comment="#", skip_blank_lines=True)
        elif file_format == "json":
            df = pd.read_json(file_path)
        elif file_format == "xlsx":
            df = pd.read_excel(file_path, comment="#")

        df.dropna(axis="index", inplace=True, how="all")
        return df

    @staticmethod
    def read_annotations(
        file_path: [Path, Dict], file_format: str = "*"
    ) -> List[ExternalAnnotation]:
        """Reads annotations from given file into DataFrame.

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
