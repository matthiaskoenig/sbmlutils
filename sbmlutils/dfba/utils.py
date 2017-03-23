"""
DFBA utility and helper functions.
"""
from __future__ import print_function, absolute_import
import os
import logging
from os.path import join as pjoin
from sbmlutils import annotation
from sbmlutils import factory
from libsbml import XMLNode
from sbmlutils.validation import check

def versioned_directory(output_dir, version):
    """ Creates a versioned directory.

    :param output_dir:
    :param version:
    :return:
    :rtype:
    """
    if output_dir is None:
        raise ValueError("directory must exist")
    if not os.path.exists(output_dir):
        logging.info('Create directory: {}'.format(output_dir))
        os.mkdir(output_dir)

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

    if creators:
        annotation.set_model_history(model, creators)
    factory.create_objects(model, units)
    factory.set_main_units(model, main_units)

    xml_node = XMLNode.convertStringToXMLNode(notes)
    if xml_node is None:
        raise ValueError("XMLNode could not be generated for:\n{}".format(notes))
    check(model.setNotes(xml_node),
          message="Setting notes on model")


if __name__ == "__main__":
    # &copy;
    notes = """
    <body xmlns='http://www.w3.org/1999/xhtml'>
    Test &#169;
    </body>
    """
    xml_node = XMLNode.convertStringToXMLNode(notes)
    if xml_node is None:
        raise ValueError("XMLNode could not be generated for:\n{}".format(notes))
