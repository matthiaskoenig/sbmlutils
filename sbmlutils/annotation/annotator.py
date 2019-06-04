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

                resource = "https://identifiers.org/{}".format(resource)

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
    def annotate_sbase(sbase, annotation_data):
        """ Annotate SBase based on given annotation data

        :param sbase:
        :param annotation_data:
        :return:
        """
        if not annotation_data:
            return

        annotations = [
            SBaseAnnotation.from_tuple(item) for item in annotation_data
        ]

        for a in annotations:
            qualifier, resource = a.qualifier.value, a.resource
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



def annotate_sbml_doc(doc, annotations):
    """ Annotates given SBML document using the annotations file.

    :param doc: SBMLDocument
    :param annotations: ModelAnnotations
    :return:
    """

    # annotate the model
    annotator = ModelAnnotator(doc, annotations)
    annotator.annotate_model()
    return doc


def annotate_sbml_file(f_sbml, f_annotations, f_sbml_annotated):
    """
    Annotate a given SBML file with the provided annotations.

    :param f_sbml: SBML to annotation
    :param f_annotations: csv file with annotations
    :param f_sbml_annotated: annotated file
    """
    # read SBML model
    doc = libsbml.readSBML(f_sbml)

    # read annotations
    annotations = ModelAnnotator.annotations_from_file(f_annotations)
    doc = annotate_sbml_doc(doc, annotations)

    # Save
    libsbml.writeSBMLToFile(doc, f_sbml_annotated)


class AnnotationException(Exception):
    pass


class ModelAnnotation(object):
    """ Class for single annotation,
        i.e. a single annotation line from a annotation file.
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

    def __init__(self, d, check_miriam=False):

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

        if self.annotation_type == "RDF":
            # FIXME: this takes much too long, necessary to have local miriam resources for validation
            # TODO: check against pattern
            # check with miriam webservices
            if check_miriam:
                '''
                m = Miriam()
                uri = m.serv.getURI(self.collection, self.entity)
                resource = m.convertURN(uri)
                if resource is None:
                    logging.warn("resource could not be found for {} : {}".format(self.collection, self.entity))
                '''
            else:
                # create identifiers.org resource manually
                resource = ModelAnnotation.identifiers_resource(self.collection, self.entity)
            setattr(self, 'resource', resource)

        self.check()

    @staticmethod
    def identifiers_resource(collection, entity):
        """ Create identifiers.org resource from given collection and entity.

        :param collection:
        :param entity:
        :return:
        """
        return ''.join(['http://identifiers.org/', collection, '/', entity])

    def check(self):
        """ Checks if the annotation is valid. """
        if self.sbml_type not in self._sbml_types:
            logging.warning("sbml_type not supported: {}, {}".format(self.sbml_type, self.d))

    def __str__(self):
        return str(self.d)
        # print (("{:<20}"*len(self._keys)).format([getattr(self, k) for k in self._keys]))


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
        # TODO: generic generation
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

    def _annotate_elements(self, elements, a):
        """ Annotate given elements with annotation.

        :param elements: SBase elements to annotate
        :param a: annotation
        :return:
        """

        # TODO: warning if element is not found
        for e in elements:
            if a.annotation_type == 'RDF':
                ModelAnnotator._add_rdf_to_element(e, a.qualifier, a.resource)
                # write SBO terms based on the SBO RDF
                if a.collection == 'sbo':
                    e.setSBOTerm(a.entity)

            elif a.annotation_type in ['Formula', 'Charge']:
                # via fbc species plugin, so check that species first
                if a.sbml_type != 'species':
                    logging.error("Chemical formula or Charge can only be set on species.")
                else:
                    s = self.model.getSpecies(e.getId())
                    splugin = s.getPlugin("fbc")
                    if splugin is None:
                        logging.error("FBC SPlugin not found for species, no fbc: {}".format(s))
                    else:
                        if a.annotation_type == 'Formula':
                            splugin.setChemicalFormula(a.entity)
                        else:
                            splugin.setCharge(int(a.entity))
            else:
                raise AnnotationException('Annotation type not supported: {}'.format(a.annotation_type))

    @classmethod
    def _add_rdf_to_element(cls, element, qualifier, resource):
        """ Adds RDF information to given element.

        :param element:
        :param qualifier:
        :param resource
        :return:
        """
        cv = libsbml.CVTerm()

        # set correct type of qualifier
        if qualifier.startswith('BQB'):
            cv.setQualifierType(libsbml.BIOLOGICAL_QUALIFIER)
            sbml_qualifier = cls.get_SBMLQualifier(qualifier)
            cv.setBiologicalQualifierType(sbml_qualifier)
        elif qualifier.startswith('BQM'):
            cv.setQualifierType(libsbml.MODEL_QUALIFIER)
            sbml_qualifier = cls.get_SBMLQualifier(qualifier)
            cv.setModelQualifierType(sbml_qualifier)
        else:
            raise AnnotationException('Unsupported qualifier: {}'.format(qualifier))

        cv.addResource(resource)

        # meta id has to be set
        if not element.isSetMetaId():
            meta_id = utils.create_metaid(element)
            element.setMetaId(meta_id)

        success = element.addCVTerm(cv)

        if success != 0:
            logging.error("RDF not written: ", success)
            logging.error(libsbml.OperationReturnValue_toString(success))
            logging.error("{}, {}, {}".format(element, qualifier, resource))

    @staticmethod
    def get_SBMLQualifier(qualifier_str):
        """ Lookup of SBMLQualifier for given qualifier string. """
        if qualifier_str not in libsbml.__dict__:
            raise AnnotationException('Qualifier not found: {}'.format(qualifier_str))
        return libsbml.__dict__.get(qualifier_str)

    @staticmethod
    def annotations_from_file(file_path, delimiter='\t'):
        if file_path.endswith('.xlsx'):
            return ModelAnnotator.annotations_from_xlsx(file_path, delimiter=delimiter)
        else:
            return ModelAnnotator.annotations_from_csv(file_path, delimiter=delimiter)

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
            a = ModelAnnotation(entry)
            res.append(a)
            # logging.debug(str(a))

        return res

    @staticmethod
    def annotations_from_xlsx(xslxfile, delimiter='\t', rm_csv=False):
        """Read annotations from xlsx file.
        xlsx is converted to csv file and than parsed with csv reader.
        """
        csvfile = "{}.csv".format(xslxfile)
        pyexcel.save_as(file_name=xslxfile, dest_file_name=csvfile, dest_delimiter=delimiter)
        res = ModelAnnotator.annotations_from_csv(csvfile, delimiter=delimiter)

        if rm_csv:
            import os
            os.remove(csvfile)
        return res
