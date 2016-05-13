"""
SBML model creator.

Creates SBML models from information stored in python modules.
"""
from __future__ import print_function, division
import os
from sbmlutils.annotation import annotate_sbml_file
from sbmlutils.report import sbmlreport

from factory.model_cell import CoreModel

from collections import namedtuple


#####################################################################
# Information storage classes
#####################################################################
class Creator(object):
    def __init__(self, familyName, givenName, email, organization):
        self.familyName = familyName
        self.givenName = givenName
        self.email = email
        self.organization = organization

class Sbase(object):
    def __init__(self, sid, name=None):
        self.sid = sid
        self.name = name

class Unit(Sbase):
    def __init__(self, sid, definition, name=None):
        super(Unit, self).__init__(sid=sid, name=name)
        self.definition = definition

class Value(Sbase):
    def __init__(self, sid, value, name=None):
        super(Value, self).__init__(sid=sid, name=name)
        self.value = value


class ValueWithUnit(Value):
    def __init__(self, sid, value, unit="-", name=None):
        super(ValueWithUnit, self).__init(sid=sid, value=value, name=name)
        self.unit = unit

class Species(ValueWithUnit):
    def __init__(self, sid, value, unit, compartment, boundaryCondition, name=None):
        super(Species, self).__init__(sid=sid, value=value, unit=unit, name=name)
        self.compartment = compartment
        self.boundaryCondition = boundaryCondition

class Function(Value):
    pass


class Compartment(ValueWithUnit):
    def __init__(self, sid, value, unit, constant, spatialDimension=3, name=None):
        super(Compartment, self).__init__(sid=sid, value=value, unit=unit, name=name)
        self.constant = constant
        self.spatialDimension = spatialDimension


class Parameter(ValueWithUnit):
    def __init__(self, sid, value, unit, constant, name=None):
        super(Parameter, self).__init__(sid=sid, value=value, unit=unit, name=name)
        self.constant = constant


class Assignment(ValueWithUnit):
    pass


class Rule(ValueWithUnit):
    pass


class RateRule(ValueWithUnit):
    pass

#####################################################################


def create_model(target_dir, model_info=[], f_annotations=None, suffix=None):
    """ Create SBML model from given information.
    This is the entry point for creating models.

    The model information is provided as a list of importable python modules.

    :param target_dir: where to create the SBML files
    :param model_info: model_info strings of python modules
    :param f_annotations: csv annotation file
    :return:
    """
    print("***", model_info, "***")

    cell_dict = CoreModel.createCellDict(model_info)
    cell_model = CoreModel(cell_dict=cell_dict)
    cell_model.create_sbml()

    mid = cell_model.model.getId()
    if suffix is not None:
        fname = '{}{}.xml'.format(mid, suffix)
    else:
        fname = '{}.xml'.format(mid)
    f_sbml = os.path.join(target_dir, fname)
    cell_model.write_sbml(f_sbml)

    # annotate
    if f_annotations is not None:
        # overwrite the normal file
        annotate_sbml_file(f_sbml, f_annotations, f_sbml)

    # create report
    sbmlreport.create_sbml_report(sbml=f_sbml, out_dir=target_dir)

    return [cell_dict, cell_model]

