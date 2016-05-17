"""
SBML model creator.

Creates SBML models from information stored in python modules.
Creates the core SBML models from given modules with python information.

The model definition modules are imported in order. From the available
model information (dictionaries and lists

Uses the importlib to import the information.
"""

from __future__ import print_function, division
import os
import copy

from libsbml import SBMLDocument, SBMLNamespaces

from sbmlutils.annotation import annotate_sbml_file
from sbmlutils.report import sbmlreport
from sbmlutils.factory import *

from sbmlutils.sbmlio import check, write_sbml
from sbmlutils import annotation
from sbmlutils._version import PROGRAM_NAME, PROGRAM_VERSION


def create_model(modules, target_dir, annotations=None, suffix=None, create_report=True):
    """ Create SBML model from given information.

    This is the entry point for creating models.
    The model information is provided as a list of importable python modules.

    An annotation file can be provided.

    :param target_dir: where to create the SBML files
    :param modules: iteratable of strings of python modules
    :param f_annotations: csv annotation file
    :return:
    """
    # preprocess
    print("create model:", modules)
    model_dict = Preprocess.combine_modules(modules)

    # create SBML model
    core_model = CoreModel(model_dict=model_dict)
    core_model.create_sbml()

    # write file
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
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
        annotate_sbml_file(sbml_path, annotations, sbml_path)

    # create report
    if create_report:
        sbmlreport.create_sbml_report(sbml=sbml_path, out_dir=target_dir)

    return [model_dict, core_model]


class Preprocess(object):
    """ Helper class for preprocessing the model modules."""

    # keys of possible information in the modules.
    _keys = ['mid',
             'version',
             'notes',
             'creators',
             'main_units',

             'units',
             'functions',
             'compartments',
             'species',
             'parameters',
             'assignments',
             'rules',
             'rate_rules',
             'reactions',
             'events']

    @staticmethod
    def combine_modules(modules):
        """
        Creates one information dictionary from various modules by combining the information.
        Information in earlier modules if overwritten by information in later modules.
        """
        # TODO: defaults
        cdict = dict()

        # add info from modules
        for module in modules:
            # single module dict
            mdict = Preprocess._createDict(module)
            # add to overall dict
            for key, value in mdict.iteritems():

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
                    for k, v in value.iteritems():
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
        for key in Preprocess._keys:
            if hasattr(module, key):
                info = getattr(module, key)
                d[key] = info
            else:
                # key does not exist in module
                warnings.warn(" ".join(['missing:', key]))
        return d


class CoreModel(object):
    """
    Class creates the SBML models from given dictionaries and lists
    of information.
    """

    def __init__(self, model_dict):
        """
        Initialize with the tissue information dictionary and
        the respective cell model used for creation.
        """
        self.model_dict = model_dict

        # add all info from dict to instance
        for key, value in model_dict.iteritems():
            setattr(self, key, value)

        self.model_id = '{}_{}'.format(self.mid, self.version)
        self.doc = None
        self.model = None

    def info(self):
        """ Print information of model dictionary.

        :return:
        :rtype:
        """
        for key in self.model_dict:
            print(key, ' : ', getattr(self, key))

    def create_sbml(self, sbml_level=3, sbml_version=1):
        """ Creats the SBML model

        :return:
        :rtype:
        """
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
        if hasattr(self, 'notes'):
            check(self.model.setNotes(self.notes), 'set notes')
        # history
        annotation.set_model_history(self.model, self.creators)

        # main units
        if hasattr(self, 'main_units'):
            set_main_units(self.model, self.main_units)

        # additional units

        # lists ofs
        for attr in ['units',
                     'functions',
                     'parameters',
                     'compartments',
                     'assignments',
                     'rules',
                     'rate_rules',
                     'species',
                     'reactions',
                     'events']:
            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                create_objects(self.model, objects)

    def write_sbml(self, filepath):
        """ Write sbml to file.

        :param filepath:
        :type filepath:
        :return:
        :rtype:
        """
        write_sbml(self.doc, filepath, validate=True,
                   program_name=PROGRAM_NAME, program_version=PROGRAM_VERSION)
