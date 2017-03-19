"""
DFBA utility and helper functions.
"""
from __future__ import print_function, absolute_import
import os
from os.path import join as pjoin
from sbmlutils import annotation
from sbmlutils import factory
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


