"""
SBML model creator.

Creates SBML models from information stored in python modules.
Creates the core SBML models from given modules with python information.

The model definition modules are imported in order. From the available
model information (dictionaries and lists

Uses the importlib to import the information.
"""
import copy
import json
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List

import libsbml
import xmltodict

import sbmlutils.factory as factory
import sbmlutils.history as history
from sbmlutils.factory import SBML_LEVEL, SBML_VERSION
from sbmlutils.io import write_sbml
from sbmlutils.metadata import annotator
from sbmlutils.report import sbmlreport
from sbmlutils.utils import bcolors
from sbmlutils.validation import check


logger = logging.getLogger(__name__)


class Factory:
    """
    Generic model factory, which should be subclassed by the individual
    ModelFactories.
    """

    def __init__(
        self, modules: Iterable[str], output_dir: Path, annotations=None, mid=None
    ):
        """

        :param modules: iterable of module strings; should be importable as is
        :param output_dir: path to output directory
        :param annotations:
        :param mid:
        """
        self.modules = modules
        self.target_dir = output_dir
        self.annotations = annotations
        self.mid = mid

    def create(self, tmp=False):
        """Creates SBML model in target directory.

        :param tmp: write files in temporary folder. Used for testing.
        :return: (model_dict, core_model, sbml_path)
        """
        if tmp:
            output_dir = tempfile.mkdtemp()
        else:
            output_dir = self.target_dir

        try:
            [model_dict, core_model, sbml_path] = create_model(
                modules=self.modules,
                output_dir=output_dir,
                annotations=self.annotations,
                mid=self.mid,
            )
        finally:
            if tmp:
                shutil.rmtree(output_dir)

        return [model_dict, core_model, sbml_path]


def create_model(
    modules: List[str],
    output_dir: Path,
    filename: str = None,
    mid: str = None,
    suffix: str = None,
    annotations=None,
    create_report: bool = True,
    validate: bool = True,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
):
    """Create SBML model from module information.

    This is the entry point for creating models.
    The model information is provided as a list of importable python modules.
    If no filename is provided the filename is created from the id and suffix.
    Additional model annotations can be provided.

    :param modules: iteratable of strings of python modules
    :param output_dir: directory in which to create SBML file
    :param filename: filename to write to with suffix, if not provided mid and suffix are used
    :param mid: model id to use for filename
    :param suffix: suffix for SBML filename
    :param annotations: list of annotations for SBML
    :param create_report: boolean switch to create SBML report
    :param validate: validates the SBML file
    :return:
    """
    # preprocess
    logger.info(
        bcolors.OKBLUE
        + "\n\n"
        + "-" * 120
        + "\n"
        + str(modules)
        + "\n"
        + "-" * 120
        + bcolors.ENDC
    )
    model_dict = Preprocess.dict_from_modules(modules)

    # create SBML model
    core_model = CoreModel.from_dict(model_dict=model_dict)

    logger.debug(core_model.get_info())
    core_model.create_sbml()

    # write file
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)
        logger.warning(f"'output_dir' should be a Path: {output_dir}")

    if not output_dir.exists():
        logger.warning(f"'output_dir' does not exist and is created: {output_dir}")
        output_dir.mkdir(parents=True)

    if not filename:
        # create filename
        if mid is None:
            mid = core_model.model.getId()
        if suffix is None:
            suffix = ""
        filename = f"{mid}{suffix}.xml"

    # write sbml
    sbml_path = output_dir / filename
    if core_model.doc is None:
        core_model.create_sbml()
    write_sbml(
        doc=core_model.doc,
        filepath=sbml_path,
        validate=validate,
        log_errors=log_errors,
        units_consistency=units_consistency,
        modeling_practice=modeling_practice,
        internal_consistency=internal_consistency,
    )

    # annotate
    if annotations is not None:
        # overwrite the normal file
        annotator.annotate_sbml(
            source=sbml_path, annotations_path=annotations, filepath=sbml_path
        )

    # create report
    if create_report:
        # file is already validated, no validation on report needed
        sbmlreport.create_report(
            sbml_path=sbml_path, output_dir=output_dir, validate=False
        )

    return [model_dict, core_model, sbml_path]


class Preprocess:
    """ Helper class for preprocessing model modules."""

    @staticmethod
    def dict_from_modules(modules: List[str]) -> Dict:
        """
        Creates one information dictionary from various modules by
        combining the information. Information in earlier modules is either
        extended or overwritten depending on data type.
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
        logger.info(f"preprocess: '{module_name}'")

        d = dict()
        for key in CoreModel._keys:
            if hasattr(module, key):
                info = getattr(module, key)
                d[key] = info
            else:
                # key does not exist in module
                logger.debug(f"key not defined: '{key}'")
        return d


class CoreModel(object):
    """
    Class creates the SBML models from given dictionaries and lists
    of information.
    """

    # keys of possible information in the modules.
    _keys = {
        "packages": list,
        "mid": None,
        "version": None,
        "notes": None,
        "creators": list,
        "model_units": None,
        "main_units": None,
        "externalModelDefinitions": list,
        "submodels": list,
        "units": list,
        "functions": list,
        "compartments": list,
        "species": list,
        "parameters": list,
        "assignments": list,
        "rules": list,
        "rate_rules": list,
        "reactions": list,
        "events": list,
        "constraints": list,
        "ports": list,
        "replacedElements": list,
        "deletions": list,
        "objectives": list,
        "layouts": list,
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

        if "main_units" in CoreModel._keys and CoreModel._keys["main_units"]:
            logger.error("'main_units' is deprecated, use 'model_units' instead.")

    @property
    def model_id(self) -> str:
        """Model id with version string"""
        if self.version:
            return f"{self.mid}_{self.version}"
        else:
            return self.mid

    @staticmethod
    def from_dict(model_dict: Dict):
        """Creates the CoreModel instance from given dictionary.

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
                logger.warning(
                    f"Unsupported key for CoreModel: '{key}'. "
                    f"Supported keys are: {CoreModel._keys}"
                )
        return m

    def get_info(self):
        """Return information of model dictionary.

        :return:
        :rtype:
        """
        # FIXME: return string, which can be logged or printed
        info = "\n" + "-" * 80 + "\n"
        info += "{}".format(self) + "\n"
        info += "-" * 80 + "\n"
        for key in sorted(CoreModel._keys):
            # string representation
            obj_str = getattr(self, key)
            if isinstance(obj_str, (list, tuple)):
                # probably tuple or list
                obj_str = [str(obj) for obj in obj_str]
            info += "{:<15}: {}\n".format(key, obj_str)
        return info

    def info(self):
        """ Print information string. """
        print(self.get_info())

    def create_sbml(
        self, sbml_level: int = SBML_LEVEL, sbml_version: int = SBML_VERSION
    ) -> libsbml.SBMLDocument:
        """Create the SBML model

        :return:
        :rtype:
        """

        logger.info(f"create_sbml: '{self.model_id}'")

        # create core model
        sbmlns = libsbml.SBMLNamespaces(sbml_level, sbml_version)

        # add all the packages
        # FIXME: only add packages which are required for the model
        supported_packages = {"fbc", "comp", "distrib"}
        sbmlns.addPackageNamespace("comp", 1)
        for package in self.packages:
            if package not in supported_packages:
                raise ValueError(
                    f"Supported packages are: '{supported_packages}', "
                    f"but package '{package}' found."
                )
            if package == "fbc":
                sbmlns.addPackageNamespace("fbc", 2)
            if package == "distrib":
                sbmlns.addPackageNamespace("distrib", 1)

        self.doc = libsbml.SBMLDocument(sbmlns)
        self.model = self.doc.createModel()
        self.doc.setPackageRequired("comp", True)
        if "fbc" in self.packages:
            self.doc.setPackageRequired("fbc", False)
            fbc_plugin = self.model.getPlugin("fbc")
            fbc_plugin.setStrict(False)
        if "distrib" in self.packages:
            self.doc.setPackageRequired("distrib", True)

        # name & id
        if self.model_id:
            check(self.model.setId(self.model_id), "set id")
            check(self.model.setName(self.model_id), "set name")
        else:
            logger.warning("Model id 'mid' should be set on model")
        # notes
        if hasattr(self, "notes") and self.notes is not None:
            factory.set_notes(self.model, self.notes)
        # history
        if hasattr(self, "creators"):
            history.set_model_history(self.model, self.creators)

        # model units
        if hasattr(self, "model_units"):
            factory.set_model_units(self.model, self.model_units)

        # lists ofs
        for attr in [
            "externalModelDefinitions",
            "submodels",
            "units",
            "functions",
            "parameters",
            "compartments",
            "species",
            "assignments",
            "rules",
            "rate_rules",
            "reactions",
            "events",
            "constraints",
            "ports",
            "replacedElements",
            "deletions",
            "objectives",
            "layouts",
        ]:
            # create the respective objects
            if hasattr(self, attr):
                objects = getattr(self, attr)
                if objects:
                    factory.create_objects(self.model, obj_iter=objects, key=attr)
                else:
                    logger.debug(f"Not defined: <{attr}>")

        return self.doc

    def get_sbml(self) -> str:
        """Return SBML string of the model.
        :return: SBML string
        """
        if self.doc is None:
            self.create_sbml()
        return libsbml.writeSBMLToString(self.doc)

    def get_json(self):

        o = xmltodict.parse(self.get_sbml())
        return json.dumps(o, indent=2)
