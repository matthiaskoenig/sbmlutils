"""
SBML model creator.

Creates SBML models from information stored in python modules.
Creates the core SBML models from given modules with python information.

The model definition modules are imported in order. From the available
model information (dictionaries and lists

Uses the importlib to import the information.
"""
import os
import shutil
import copy
import logging
import tempfile
import warnings
from sbmlutils.logutils import bcolors

import libsbml

from sbmlutils.annotation import annotator
import sbmlutils.history as history
import sbmlutils.factory as factory
import sbmlutils.sbmlio as sbmlio

from sbmlutils.factory import SBML_LEVEL, SBML_VERSION
from sbmlutils._version import PROGRAM_NAME, PROGRAM_VERSION
from sbmlutils.report import sbmlreport


class Factory(object):
    """
    Generic model factory, which should be subclassed by the individual
    ModelFactories.
    """

    def __init__(self, modules, target_dir, annotations=None, mid=None):
        self.modules = modules
        self.target_dir = target_dir
        self.annotations = annotations
        self.mid = mid

    def create(self, tmp=False):
        """ Creates SBML model in target directory.

        :param tmp: write files in temporary folder. Used for testing.
        :return: (model_dict, core_model, sbml_path)
        """
        if tmp:
            target_dir = tempfile.mkdtemp()
        else:
            target_dir = self.target_dir

        try:
            [model_dict, core_model, sbml_path] = create_model(
                modules=self.modules,
                target_dir=target_dir,
                annotations=self.annotations,
                mid=self.mid)
        finally:
            if tmp:
                shutil.rmtree(target_dir)

        return [model_dict, core_model, sbml_path]


def create_model(modules, target_dir, annotations=None, suffix=None, create_report=True, mid=None):
    """ Create SBML model from module information.

    This is the entry point for creating models.
    The model information is provided as a list of importable python modules.

    Additional model annotations can be provided.

    :param modules: iteratable of strings of python modules
    :param target_dir: directory in which to create SBML files
    :param annotations: list of annotations for SBML
    :param suffix: Suffix for SBML filename
    :param create_report: boolean switch to create SBML report
    :param mid: model id to use for saving file
    :return:
    """
    # preprocess
    logging.info(bcolors.OKBLUE + '\n\n' + '-'*120 + '\n' + str(modules) + '\n' + '-'*120 + bcolors.ENDC)
    model_dict = Preprocess.dict_from_modules(modules)

    # create SBML model
    core_model = CoreModel.from_dict(model_dict=model_dict)
    logging.debug(core_model.get_info())
    core_model.create_sbml()

    # write file
    if not os.path.exists(target_dir):
        logging.warning("Target directory does not exist and is created: {}".format(target_dir))
        os.makedirs(target_dir)

    if mid is None:
        mid = core_model.model.getId()
    if suffix is not None:
        filename = '{}{}.xml'.format(mid, suffix)
    else:
        filename = '{}.xml'.format(mid)
    sbml_path = os.path.join(target_dir, filename)

    core_model.write_sbml(sbml_path, validate=True)

    # annotate
    if annotations is not None:
        # overwrite the normal file
        annotator.annotate_sbml_file(sbml_path, annotations, sbml_path)

    # create report
    if create_report:
        logging.info("Create SBML report:'{}'".format(sbml_path))
        sbmlreport.create_sbml_report(sbml_path=sbml_path, out_dir=target_dir, validate=False)

    return [model_dict, core_model, sbml_path]


class Preprocess(object):
    """ Helper class for preprocessing model modules."""

    @staticmethod
    def dict_from_modules(modules):
        """
        Creates one information dictionary from various modules by combining the information.
        Information in earlier modules if overwritten by information in later modules.
        """
        cdict = dict()

        # add info from modules
        for module in modules:
            # single module dict
            mdict = Preprocess._createDict(module)
            # add to overall dict
            for key, value in mdict.items():

                # lists of higher modules are extended
                if type(value) in [list, tuple]:
                    # create new list
                    if key not in cdict:
                        cdict[key] = []
                    # now add elements by copy
                    cdict[key].extend(copy.deepcopy(value))

                # dictionaries of higher modules are extended
                elif type(value) is dict:
                    # create new dict
                    if key not in cdict:
                        cdict[key] = dict()
                    # now add the elements by copy
                    d = cdict[key]
                    for k, v in value.items():
                        d[k] = copy.deepcopy(v)

                # !everything else is overwritten
                else:
                    cdict[key] = value

        return cdict

    @staticmethod
    def _createDict(module_name, package=None):
        """
        A module which encodes a cell model is given and
        used to create the instance of the CellModel from
        the given global variables of the module.
        """
        # dynamically import module
        import importlib
        module = importlib.import_module(module_name, package=package)
        # reload quired so that module is evaluated at time of creation
        importlib.reload(module)

        # get attributes from class
        logging.info('Preprocess: <{}>'.format(module_name))

        d = dict()
        for key in CoreModel._keys:
            if hasattr(module, key):
                info = getattr(module, key)
                d[key] = info
            else:
                # key does not exist in module
                logging.info(" ".join(['key not defined:', key]))
        return d


class CoreModel(object):
    """
    Class creates the SBML models from given dictionaries and lists
    of information.
    """
    # keys of possible information in the modules.
    _keys = {'mid': None,
             'version': None,
             'notes': None,
             'creators': list,
             'model_units': None,
             'main_units': None,

             'externalModelDefinitions': list,
             'submodels': list,

             'units': list,
             'functions': list,
             'compartments': list,
             'species': list,
             'parameters': list,
             'assignments': list,
             'rules': list,
             'rate_rules': list,
             'reactions': list,
             'events': list,
             'constraints': list,
             'ports': list,
             'replacedElements': list,
             'deletions': list,

             'objectives': list,

             'layouts': list,
             }

    def __init__(self):
        """
        Initialize with the tissue information dictionary and
        the respective cell model used for creation.
        """
        for key, value in CoreModel._keys.items():
            # necessary to init the lists for every instance,
            # to not share them between instances
            if value is not None:
                if value == list:
                    value = []
                elif value == dict:
                    value = {}

            setattr(self, key, value)

        self.doc = None  # SBMLDocument
        self.model = None  # SBMLModel

        if 'main_units' in CoreModel._keys and CoreModel._keys['main_units']:
            logging.error("'main_units' is deprecated, use 'model_units' instead.")

    @property
    def model_id(self):
        if self.version:
            return '{}_{}'.format(self.mid, self.version)
        else:
            return self.mid


    @staticmethod
    def from_dict(model_dict):
        """ Creates the CoreModel instance from given dictionary.

        Only the references to the dictionary are stored.

        :param self:
        :type self:
        :param model_dict:
        :type model_dict:
        :return:
        :rtype:
        """
        m = CoreModel()
        # add info from model_dict to instance
        for key, value in model_dict.items():
            if key in CoreModel._keys:
                setattr(m, key, value)
            else:
                warnings.warn('Unsupported key for CoreModel: {}'.format(key))
        return m

    def get_info(self):
        """ Return information of model dictionary.

        :return:
        :rtype:
        """
        # FIXME: return string, which can be logged or printed
        info = '\n' + '-'*80 + '\n'
        info += '{}'.format(self) + '\n'
        info += '-' * 80 + '\n'
        for key in sorted(CoreModel._keys):
            # string representation
            obj_str = getattr(self, key)
            if isinstance(obj_str, (list, tuple)):
                # probably tuple or list
                obj_str = [str(obj) for obj in obj_str]
            info += '{:<15}: {}\n'.format(key, obj_str)
        return info

    def info(self):
        """ Print information string. """
        print(self.get_info())

    def create_sbml(self, sbml_level=SBML_LEVEL, sbml_version=SBML_VERSION):
        """ Create the SBML model

        :return:
        :rtype:
        """
        from sbmlutils.validation import check

        logging.info('*'*40)
        logging.info(self.model_id)
        logging.info('*' * 40)

        # create core model
        sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)

        # add all the packages
        # FIXME: only add packages which are required for the model

        sbmlns.addPackageNamespace("fbc", 2)
        sbmlns.addPackageNamespace("comp", 1)
        # sbmlns.addPackageNamespace("distrib", 1)

        self.doc = libsbml.SBMLDocument(sbmlns)
        self.doc.setPackageRequired("comp", True)
        self.doc.setPackageRequired("fbc", False)
        # self.doc.setPackageRequired("distrib", True)

        self.model = self.doc.createModel()
        fbc_plugin = self.model.getPlugin("fbc")
        fbc_plugin.setStrict(False)

        # name & id
        check(self.model.setId(self.model_id), 'set id')
        check(self.model.setName(self.model_id), 'set name')
        # notes
        if hasattr(self, 'notes') and self.notes is not None:
            factory.set_notes(self.model, self.notes)
        # history
        if hasattr(self, 'creators'):
            history.set_model_history(self.model, self.creators)

        # model units
        if hasattr(self, 'model_units'):
            factory.set_model_units(self.model, self.model_units)

        # lists ofs
        for attr in [
            'externalModelDefinitions',
            'submodels',
            'units',
            'functions',
            'parameters',
            'compartments',
            'species',
            'assignments',
            'rules',
            'rate_rules',
            'reactions',
            'events',
            'constraints',
            'ports',
            'replacedElements',
            'deletions',
            'objectives',
            'layouts'
        ]:
            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                if objects:
                    factory.create_objects(self.model, obj_iter=objects, key=attr)
                else:
                    logging.info("Not defined: <{}> ".format(attr))

    def write_sbml(self, filepath, validate=True):
        """ Write sbml to file.

        :param filepath:
        :type filepath:
        :return:
        :rtype:
        """
        sbmlio.write_sbml(self.doc, filepath, validate=validate,
                          program_name=PROGRAM_NAME, program_version=PROGRAM_VERSION)
