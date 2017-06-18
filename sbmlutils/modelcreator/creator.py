"""
SBML model creator.

Creates SBML models from information stored in python modules.
Creates the core SBML models from given modules with python information.

The model definition modules are imported in order. From the available
model information (dictionaries and lists

Uses the importlib to import the information.
"""

from __future__ import print_function, division

import copy
import logging
import os
import shutil
import tempfile
import warnings
from six import iteritems

import sbmlutils.annotation as annotation
import sbmlutils.history as history
import sbmlutils.factory as factory
import sbmlutils.sbmlio as sbmlio
from libsbml import SBMLDocument, SBMLNamespaces
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
        """ Create the SBML model and returns it.

        :param tmp: write files in temporary folder. Used for testing.
        :return:
        """
        if tmp:
            target_dir = tempfile.mkdtemp()
        else:
            target_dir = self.target_dir

        try:
            [model_dict, core_model] = create_model(
                modules=self.modules,
                target_dir=target_dir,
                annotations=self.annotations,
                mid=self.mid)
        finally:
            if tmp:
                shutil.rmtree(target_dir)

        return [model_dict, core_model]


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
    print("create model:", modules)
    model_dict = Preprocess.dict_from_modules(modules)

    # create SBML model
    core_model = CoreModel.from_dict(model_dict=model_dict)
    core_model.info()
    core_model.create_sbml()

    # write file
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if mid is None:
        mid = core_model.model.getId()
    if suffix is not None:
        filename = '{}{}.xml'.format(mid, suffix)
    else:
        filename = '{}.xml'.format(mid)
    sbml_path = os.path.join(target_dir, filename)

    core_model.write_sbml(sbml_path)

    # annotate
    if annotations is not None:
        # overwrite the normal file
        annotation.annotate_sbml_file(sbml_path, annotations, sbml_path)

    # create report
    if create_report:
        sbmlreport.create_sbml_report(sbml_path=sbml_path, out_dir=target_dir)

    return [model_dict, core_model]


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
            for key, value in iteritems(mdict):

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
                    print(d)
                    for k, v in iteritems(value):
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

        # get attributes from class
        print('Preprocess: <{}>'.format(module_name))

        d = dict()
        for key in CoreModel._keys:
            if hasattr(module, key):
                info = getattr(module, key)
                d[key] = info
            else:
                # key does not exist in module
                logging.warning(" ".join(['missing:', key]))
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
             'main_units': dict,

             'units': list,
             'functions': list,
             'compartments': list,
             'species': list,
             'parameters': list,
             'assignments': list,
             'rules': list,
             'rate_rules': list,
             'reactions': list,
             'events': list}

    def __init__(self):
        """
        Initialize with the tissue information dictionary and
        the respective cell model used for creation.
        """
        for key, value in iteritems(CoreModel._keys):
            # necessary to init the lists for every instance,
            # to not share them between instances
            if value is not None:
                if value == list:
                    value = []
                elif value == dict:
                    value = {}

            setattr(self, key, value)

        # SBMLDocument and Model
        self.doc = None
        self.model = None

    @property
    def model_id(self):
        return '{}_{}'.format(self.mid, self.version)

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
        for key, value in iteritems(model_dict):
            if key in CoreModel._keys:
                setattr(m, key, value)
            else:
                warnings.warn('Unsupported key for CoreModel: {}'.format(key))
        return m

    def info(self):
        """ Print information of model dictionary.

        :return:
        :rtype:
        """
        print('-'*80)
        print(self)
        print('-' * 80)
        for key in sorted(CoreModel._keys):
            # string representation
            obj_str = getattr(self, key)
            if isinstance(obj_str, (list, tuple)):
                # probably tuple or list
                obj_str = [str(obj) for obj in obj_str]
            print('{:<15}: {}'.format(key, obj_str))

    def create_sbml(self, sbml_level=3, sbml_version=1):
        """ Creats the SBML model

        :return:
        :rtype:
        """
        from sbmlutils.validation import check
        print('\n', '*' * 40, '\n', self.model_id, '\n', '*' * 40)

        # create core model
        sbmlns = SBMLNamespaces(sbml_level, sbml_version, "fbc", 2)
        self.doc = SBMLDocument(sbmlns)
        self.doc.setPackageRequired("fbc", False)
        self.model = self.doc.createModel()
        mplugin = self.model.getPlugin("fbc")
        mplugin.setStrict(False)

        # name & id
        check(self.model.setId(self.model_id), 'set id')
        check(self.model.setName(self.model_id), 'set name')
        # notes
        if hasattr(self, 'notes') and self.notes is not None:
            check(self.model.setNotes(self.notes), 'set notes')
        # history
        if hasattr(self, 'creators'):
            history.set_model_history(self.model, self.creators)

        # main units
        if hasattr(self, 'main_units'):
            factory.set_main_units(self.model, self.main_units)

        # additional units

        # lists ofs
        for attr in ['units',
                     'functions',
                     'parameters',
                     'compartments',
                     'species',
                     'assignments',
                     'rules',
                     'rate_rules',
                     'reactions',
                     'events']:
            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                if (objects):
                    factory.create_objects(self.model, objects)
                else:
                    logging.warn("Attribute <{}> missing from model.".format(attr))

    def write_sbml(self, filepath):
        """ Write sbml to file.

        :param filepath:
        :type filepath:
        :return:
        :rtype:
        """
        sbmlio.write_sbml(self.doc, filepath, validate=True,
                          program_name=PROGRAM_NAME, program_version=PROGRAM_VERSION)
