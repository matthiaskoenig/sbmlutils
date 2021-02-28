"""SBML model creator.

Creates SBML models from information stored in python modules.
Creates the core SBML models from given modules with python information.

The model definition modules are imported in order. From the available
model information (dictionaries and lists

Uses the importlib to import the information.
"""
import copy
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, NamedTuple, Optional, Union

import libsbml
import xmltodict  # type: ignore

import sbmlutils.factory as factory
import sbmlutils.history as history
from sbmlutils.factory import SBML_LEVEL, SBML_VERSION
from sbmlutils.io import write_sbml
from sbmlutils.metadata import annotator
from sbmlutils.report import sbmlreport
from sbmlutils.utils import bcolors
from sbmlutils.validation import check


logger = logging.getLogger(__name__)


class Preprocess:
    """Helper class for preprocessing model modules."""

    @staticmethod
    def dict_from_modules(modules: List[str], keys: Iterable[str]) -> Dict:
        """Create single information dictionary from various modules.

        Information in earlier modules is either
        extended or overwritten depending on data type.
        """
        cdict: Dict[Any, Any] = dict()

        # add info from modules
        for module in modules:
            # single module dict
            mdict = Preprocess._create_module_dict(module, keys=keys)
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
    def _create_module_dict(
        module_name: str, keys: Iterable[str], package: str = None
    ) -> Dict[str, Any]:
        """Create information dictionary from given module.

        Uses a dynamical import to figure out the content of the model.
        """
        # dynamically import module
        import importlib

        module = importlib.import_module(module_name, package=package)
        # reload quired so that module is evaluated at time of creation
        importlib.reload(module)

        # get attributes from class
        logger.info(f"preprocess: '{module_name}'")

        d = dict()
        for key in keys:
            if hasattr(module, key):
                info = getattr(module, key)
                d[key] = info
            else:
                # key does not exist in module
                logger.debug(f"key not defined: '{key}'")
        return d


class CoreModel(object):
    """Core model definition.

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

    def __init__(self) -> None:
        """Initialize core model.

        Initialize with the tissue information dictionary and
        the respective cell model used for creation.
        """
        for key, value in self._keys.items():
            # necessary to init the lists for every instance,
            # to not share them between instances
            if value is not None:
                if value == list:
                    value = []  # type: ignore
                elif value == dict:
                    value = {}  # type: ignore

            setattr(self, key, value)

        self.doc: libsbml.SBMLDocument = None
        self.model: libsbml.Model = None
        self.mid: str
        self.version = None
        self.packages: List[str] = []
        self.notes = None
        self.creators: List[factory.Creator] = []
        self.model_units: Optional[factory.ModelUnits] = None

        if "main_units" in self._keys and self._keys["main_units"]:
            logger.error("'main_units' is deprecated, use 'model_units' instead.")

    @property
    def model_id(self) -> str:
        """Model id with version string."""
        if self.version:
            return f"{self.mid}_{self.version}"
        else:
            return self.mid

    @classmethod
    def from_dict(cls, model_dict: Dict) -> "CoreModel":
        """Create the CoreModel instance from given dictionary.

        Only the references to the dictionary are stored.
        """
        m = CoreModel()
        # add info from model_dict to instance
        for key, value in model_dict.items():
            if key in cls._keys:
                setattr(m, key, value)
            else:
                logger.warning(
                    f"Unsupported key for {cls.__name__}: '{key}'. "
                    f"Supported keys are: {cls._keys}"
                )
        return m

    def get_info(self) -> str:
        """Return information of model dictionary.

        :return:
        :rtype:
        """
        # FIXME: return string, which can be logged or printed
        info = "\n" + "-" * 80 + "\n"
        info += "{}".format(self) + "\n"
        info += "-" * 80 + "\n"
        for key in sorted(self._keys):
            # string representation
            obj_str = getattr(self, key)
            if isinstance(obj_str, (list, tuple)):
                # probably tuple or list
                obj_str = [str(obj) for obj in obj_str]
            info += "{:<15}: {}\n".format(key, obj_str)
        return info

    def info(self) -> None:
        """Print information string."""
        print(self.get_info())

    def create_sbml(
        self, sbml_level: int = SBML_LEVEL, sbml_version: int = SBML_VERSION
    ) -> libsbml.SBMLDocument:
        """Create the SBML model.

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
            factory.ModelUnits.set_model_units(self.model, self.model_units)  # type: ignore

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
        return libsbml.writeSBMLToString(self.doc)  # type: ignore

    def get_json(self) -> str:
        """Get JSON representation."""
        o = xmltodict.parse(self.get_sbml())
        return json.dumps(o, indent=2)


class FactoryResult(NamedTuple):
    """Results structure when creating SBML models with sbmlutils."""

    model_dict: Dict
    core_model: CoreModel
    sbml_path: Path


def create_model(
    modules: Union[Iterable[str], Dict],
    output_dir: Path = None,
    tmp: bool = False,
    filename: str = None,
    mid: str = None,
    suffix: str = None,
    annotations: Path = None,
    create_report: bool = True,
    validate: bool = True,
    log_errors: bool = True,
    units_consistency: bool = True,
    modeling_practice: bool = True,
    internal_consistency: bool = True,
    sbml_level: int = SBML_LEVEL,
    sbml_version: int = SBML_VERSION,
) -> FactoryResult:
    """Create SBML model from module information.

    This is the entry point for creating models.
    The model information is provided as a list of importable python modules.
    If no filename is provided the filename is created from the id and suffix.
    Additional model annotations can be provided.

    :param modules: iterable of strings of python modules or CoreModel instance
    :param output_dir: directory in which to create SBML file
    :param tmp: boolean flag to create files in a temporary directory (for testing)
    :param filename: filename to write to with suffix, if not provided mid and suffix are used
    :param mid: model id to use for filename
    :param suffix: suffix for SBML filename
    :param annotations: Path to annotations file
    :param create_report: boolean switch to create SBML report
    :param validate: validates the SBML file
    :param log_errors: boolean flag to log errors
    :param units_consistency: boolean flag to check units consistency
    :param modeling_practice: boolean flag to check modeling practise
    :param internal_consistency: boolean flag to check internal consistency
    :param sbml_level: set SBML level for model generation
    :param sbml_version: set SBML version for model generation

    :return: FactoryResult
    """
    if output_dir is None and tmp is False:
        raise TypeError("create_model() missing 1 required argument: 'output_dir'")

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
    if isinstance(modules, dict):
        model_dict = modules
    else:
        model_dict = Preprocess.dict_from_modules(modules, keys=CoreModel._keys)  # type: ignore

    core_model = CoreModel.from_dict(model_dict=model_dict)
    logger.debug(core_model.get_info())
    core_model.create_sbml(sbml_level=sbml_level, sbml_version=sbml_version)

    if not filename:
        # create filename
        if mid is None:
            mid = core_model.model.getId()
        if suffix is None:
            suffix = ""
        filename = f"{mid}{suffix}.xml"

    if tmp:
        output_dir = tempfile.mkdtemp()  # type: ignore
        sbml_path = os.path.join(output_dir, filename)  # type: ignore
    else:
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
            logger.warning(f"'output_dir' should be a Path: {output_dir}")

        if not output_dir.exists():  # type: ignore
            logger.warning(f"'output_dir' does not exist and is created: {output_dir}")
            output_dir.mkdir(parents=True)  # type: ignore
        sbml_path = output_dir / filename  # type: ignore

    # write sbml
    if core_model.doc is None:
        core_model.create_sbml()
    try:
        write_sbml(
            doc=core_model.doc,
            filepath=sbml_path,  # type: ignore
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
                source=sbml_path, annotations_path=annotations, filepath=sbml_path  # type: ignore
            )

        # create report
        if create_report:
            # file is already validated, no validation on report needed
            sbmlreport.create_report(
                sbml_path=sbml_path, output_dir=output_dir, validate=False  # type: ignore
            )
    finally:
        if tmp:
            shutil.rmtree(str(output_dir))

    return FactoryResult(
        model_dict=model_dict,
        core_model=core_model,
        sbml_path=sbml_path,  # type: ignore
    )
