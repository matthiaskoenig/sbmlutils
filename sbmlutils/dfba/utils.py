"""
DFBA utility and helper functions.
"""
from __future__ import print_function, absolute_import
import os
from os.path import join as pjoin
from sbmlutils import annotation
from sbmlutils import factory
from .builder import UPPER_BOUND_DEFAULT, LOWER_BOUND_DEFAULT

from libsbml import XMLNode


def versioned_directory(output_dir, version):
    """ Creates a versioned directory.

    :param output_dir:
    :param version:
    :return:
    :rtype:
    """
    if output_dir is None:
        raise ValueError("directory must exist")

    directory = pjoin(output_dir, 'v{}'.format(version))
    if not os.path.exists(directory):
        print('Create directory: {}'.format(directory))
        os.mkdir(directory)
    return directory


def add_generic_info(model, notes, creators, units, main_units):
    """ Adds the shared information to the models.

    :param model: SBMLModel instance
    :return:
    """

    annotation.set_model_history(model, creators)
    factory.create_objects(model, units)
    factory.set_main_units(model, main_units)
    xml_notes = XMLNode.convertStringToXMLNode(notes)
    model.setNotes(xml_notes)


def exchange_flux_bound_parameters(exchange_rids, unit):
    # exchange flux bounds
    parameters = []
    for ex_rid in exchange_rids:
        for bound_type in ['lb', 'ub']:
            if bound_type == 'lb':
                value = LOWER_BOUND_DEFAULT
            elif bound_type == 'ub':
                value = UPPER_BOUND_DEFAULT
            parameters.append(
                # lb_vGlcxt
                factory.Parameter(sid="{}_{}".format(bound_type, ex_rid), value=value, unit=unit, constant=False,
                                  sboTerm="SBO:0000625")
            )
    return parameters
