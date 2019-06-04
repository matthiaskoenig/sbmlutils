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
import re
import pyexcel
import csv
import logging
import libsbml

from sbmlutils import utils
from .miriam import IDENTIFIERS_ORG_PREFIX


class SBaseAnnotation(object):
    """ Class for annotation of SBase objects."""

    def __init__(self, qualifier, collection, term):
        return SBaseAnnotation(qualifier, "{}/{}".format(collection, term))

    def __init__(self, qualifier, resource):
        """ Create new annotation information.

        :param qualifier:
        :param resource:
        """
        if not resource.startswith("http"):
            tokens = resource.split("/")
            if len(tokens) < 2:
                # check that consisting of collection and term
                logging.error(
                    "Annotation resources have to be of the form"
                    "'collection/term' or 'http[s]://resourceurl': "
                    "{}".format(resource))

                resource = "{}/{}".format(IDENTIFIERS_ORG_PREFIX, resource)

        # TODO: check qualifier from allowed qualifiers
        # if not isinstance(qualifer,)

        # TODO: check if collection and term that the collection is supported
        # TODO: check annotations against the MIRIAM info (load miriam info) analoque to the java version
        # and the term is according to the miriam patterns

        self.qualifier = qualifier
        self.resource = resource

    @staticmethod
    def from_tuple(tuple):
        qualifier, resource = tuple[0], tuple[1]
        return SBaseAnnotation(qualifier, resource)

    @staticmethod
    def annotate_from_tuples(sbase, tuples):
        if not tuples:
            return

        for item in tuples:
            sbase_annotation = SBaseAnnotation.from_tuple(item)
            sbase_annotation.annotate_sbase(sbase)

    def annotate_sbase(self, sbase):
        """ Annotate SBase based on given annotation data

        :param sbase:
        :param annotation_data:
        :return:
        """
        qualifier, resource = self.qualifier.value, self.resource
        print(qualifier, resource)
        cv = libsbml.CVTerm()

        # set correct type of qualifier
        if qualifier.startswith("BQB"):
            cv.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
            sbml_qualifier = ModelAnnotator.get_SBMLQualifier(qualifier)
            cv.setBiologicalQualifierType(sbml_qualifier)
        elif qualifier.startswith('BQM'):
            cv.setQualifierType(libsbml.MODEL_QUALIFIER)
            sbml_qualifier = ModelAnnotator.get_SBMLQualifier(qualifier)
            cv.setModelQualifierType(sbml_qualifier)
        else:
            logging.error('Unsupported qualifier: {}'.format(qualifier))

        cv.addResource(resource)

        # meta id has to be set
        if not sbase.isSetMetaId():
            sbase.setMetaId(utils.create_metaid(sbase))

        success = sbase.addCVTerm(cv)

        if success != 0:
            logging.error("RDF not written: ", success)
            logging.error(libsbml.OperationReturnValue_toString(success))
            logging.error("{}, {}, {}".format(object, qualifier, resource))


# ----------------------------------------------------------
# External annotation files
# ----------------------------------------------------------
def annotate_sbml_file(f_sbml, f_annotations, f_sbml_annotated):
    """
    Annotate a given SBML file with the provided annotations.

    :param f_sbml: SBML to annotation
    :param f_annotations: external file with annotations
    :param f_sbml_annotated: annotated file
    """
    # read SBML model
    doc = libsbml.readSBML(f_sbml)

    # read annotations
    external_annotations = ModelAnnotator.annotations_from_file(f_annotations)
    doc = annotate_sbml_doc(doc, external_annotations)

    # save
    libsbml.writeSBMLToFile(doc, f_sbml_annotated)


def annotate_sbml_doc(doc, external_annotations):
    """ Annotates given SBML document using the annotations file.

    :param doc: SBMLDocument
    :param external_annotations: ModelAnnotations
    :return: libsbml.SBMLDocument
    """
    annotator = ModelAnnotator(doc, external_annotations)
    annotator.annotate_model()
    return doc


class ExternalAnnotation(object):
    """
        Class for handling SBML annotations defined in external source.
        This corresponds to a single entry in the external annotation file.
    """
    # possible columns in annotation file
    _keys = [
        'pattern',
        'sbml_type',
        'annotation_type',
        'qualifier',
        'collection',
        'entity',
        'name'
    ]
    # allowed SBML types for annotation
    _sbml_types = frozenset([
        "document",
        "model",
        "unit",
        "reaction",
        "transporter",
        "species",
        "compartment",
        "parameter",
        "rule"
    ])
    _annotation_types = frozenset([
        "RDF",
        "Formula",
        "Charge"
    ])

    def __init__(self, d):

        self.d = d
        # print(d)
        for key in self._keys:
            # optional fields
            if key in ['qualifier', 'collection', 'name']:
                value = d.get(key, '')
            # required fields
            else:
                value = d[key]
            setattr(self, key, value)

        self.check()

    def check(self):
        """ Checks if the annotation is valid. """
        if self.sbml_type not in self._sbml_types:
            logging.warning("sbml_type not supported: {}, {}".format(self.sbml_type, self.d))

    def __str__(self):
        return str(self.d)


class ModelAnnotator(object):
    """ Helper class for annotating SBML models. """

    def __init__(self, doc, annotations):
        """ Constructor.

        :param doc: SBMLDocument
        :param annotations: iterateable of ModelAnnotation
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
                    elements = ModelAnnotator._elements_from_ids(self.model, pattern_ids, sbml_type=a.sbml_type)

            self._annotate_elements(elements, a)

    def _get_ids_from_model(self):
        """ Create dictionary of ids for given model for lookup.

        :return:
        """
        id_dict = dict()
        id_dict['model'] = [self.model.getId()]

        lof = self.model.getListOfUnitDefinitions()
        if lof:
            id_dict['unit'] = [item.getId() for item in lof]

        lof = self.model.getListOfCompartments()
        if lof:
            id_dict['compartment'] = [item.getId() for item in lof]

        lof = self.model.getListOfSpecies()
        if lof:
            id_dict['species'] = [item.getId() for item in lof]

        lof = self.model.getListOfParameters()
        if lof:
            id_dict['parameter'] = [item.getId() for item in lof]

        lof = self.model.getListOfReactions()
        if lof:
            id_dict['reaction'] = [item.getId() for item in lof]

        lof = self.model.getListOfRules()
        if lof:
            id_dict['rule'] = [item.getVariable() for item in lof]

        lof = self.model.getListOfEvents()
        if lof:
            id_dict['event'] = [item.getId() for item in lof]

        return id_dict

    @staticmethod
    def _get_matching_ids(ids, pattern):
        """
        Finds the model ids based on the regular expression pattern.
        """
        match_ids = []
        for string in ids:
            match = re.match(pattern, string)
            if match:
                # print 'Match: ', pattern, '<->', string
                match_ids.append(string)
        return match_ids

    @staticmethod
    def _elements_from_ids(model, sbml_ids, sbml_type=None):
        """
        Get list of SBML elements from given ids.

        :param model:
        :param sbml_ids:
        :param sbml_type:
        :return:
        """
        elements = []
        for sid in sbml_ids:
            if sbml_type == 'rule':
                e = model.getRuleByVariable(sid)
            elif sbml_type == 'unit':
                e = model.getUnitDefinition(sid)
            else:
                # returns the first element with id
                e = model.getElementBySId(sid)
            if e is None:
                if sid == model.getId():
                    e = model
                else:
                    logging.warning('Element could not be found: {}'.format(sid))
                    continue
            elements.append(e)
        return elements

    def _annotate_elements(self, elements, ex_a: ExternalAnnotation):
        """ Annotate given elements with annotation.

        :param elements: SBase elements to annotate
        :param a: annotation
        :return:
        """
        for e in elements:
            if ex_a.annotation_type == 'RDF':
                sbase_annotation = SBaseAnnotation(
                    qualifier=ex_a.qualifier,
                    collection=ex_a.collection,
                    term=ex_a.entity
                )
                sbase_annotation.annotate_sbase(e)

                # write SBO terms based on the SBO RDF
                if ex_a.collection == 'sbo':
                    e.setSBOTerm(ex_a.entity)

            elif ex_a.annotation_type in ['Formula', 'Charge']:
                # via fbc species plugin, so check that species first
                if ex_a.sbml_type != 'species':
                    logging.error("Chemical formula or Charge can only be set on species.")
                else:
                    s = self.model.getSpecies(e.getId())
                    splugin = s.getPlugin("fbc")
                    if splugin is None:
                        logging.error("FBC SPlugin not found for species, no fbc: {}".format(s))
                    else:
                        if ex_a.annotation_type == 'Formula':
                            splugin.setChemicalFormula(ex_a.entity)
                        else:
                            splugin.setCharge(int(ex_a.entity))
            else:
                raise ValueError(
                    'Annotation type not supported: '
                    '{}'.format(ex_a.annotation_type)
                )

    @staticmethod
    def get_SBMLQualifier(qualifier_str):
        """ Lookup of SBMLQualifier for given qualifier string. """

        # FIXME: better lookup with MIRIAM
        if qualifier_str not in libsbml.__dict__:
            raise ValueError(
                'Qualifier not supported: {}'.format(qualifier_str)
            )
        return libsbml.__dict__.get(qualifier_str)

    @staticmethod
    def annotations_from_file(file_path, delimiter='\t'):
        """ Reads annotations from given file.

        Supports either excel files or CSV.

        :param file_path:
        :param delimiter:
        :return:
        """
        if file_path.endswith('.xlsx'):
            return ModelAnnotator.annotations_from_xlsx(
                file_path, delimiter=delimiter
            )
        else:
            return ModelAnnotator.annotations_from_csv(
                file_path, delimiter=delimiter
            )

    @staticmethod
    def annotations_from_csv(csvfile, delimiter='\t'):
        """ Read annotations from csv in annotation data structure. """
        res = []
        f = open(csvfile, 'rt')
        reader = csv.reader(f, delimiter=delimiter, quoting=csv.QUOTE_NONE)

        # first line is headers line
        headers = next(reader)
        logging.debug('Headers: {}'.format(headers))

        # read entries
        for row in reader:
            # skip empty lines
            if not ''.join(row).strip():
                continue
            # skip comments
            if row[0].startswith('#'):
                continue

            entry = dict(zip(headers, [item.strip() for item in row]))
            a = ExternalAnnotation(entry)
            res.append(a)
            # logging.debug(str(a))

        return res

    @staticmethod
    def annotations_from_xlsx(xslxfile, delimiter='\t', rm_csv=False):
        """Read annotations from xlsx file.
        xlsx is converted to csv file and than parsed with csv reader.
        """
        csvfile = "{}.csv".format(xslxfile)
        pyexcel.save_as(file_name=xslxfile, dest_file_name=csvfile,
                        dest_delimiter=delimiter)
        res = ModelAnnotator.annotations_from_csv(csvfile, delimiter=delimiter)

        if rm_csv:
            import os
            os.remove(csvfile)
        return res
