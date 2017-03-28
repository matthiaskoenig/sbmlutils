"""
DFBA utility and helper functions.
"""
from __future__ import print_function, absolute_import
import os
import logging
from os.path import join as pjoin
from six import iteritems

from libsbml import XMLNode
from sbmlutils import annotation
from sbmlutils import factory
from sbmlutils.validation import check

def find_exchange_reactions(model):
    """ Finds the exchange reaction in given FBA model.

    Currently the exchange rids are found via 
    prefix EX_.
    
    :param model: SBML model
    :return: list of exchange reaction ids
    """
    ex_rids = []
    for reactions in model.getListOfReactions():
        rid = reactions.getId()
        # exchange reaction by id
        if rid.startswith("EX_"):
            ex_rids.append(rid)

        # exchange reaction by SBOTerm
        # TODO: implement via exchange, source, sink SBOTerm (and number of reactants/products)

    return sorted(ex_rids)


def clip_prefixes_in_model(model, prefix_species="M_", prefix_reaction="R_", prefix_gene="G_"):
    """ Removes the unnecessary Bigg prefixes.
    R_ for reactions, M_ for metabolites and G_ for genes.
    
    :param model: 
    :type model: 
    :return: 
    :rtype: 
    """
    replace = {}

    # clip reactions
    if prefix_reaction is not None:
        for r in model.getListOfReactions():
            rid = r.getId()
            rid_clipped = clip(rid, prefix_reaction)
            if rid != rid_clipped:
                replace[rid] = rid_clipped
                r.setId(rid_clipped)

    # clip species
    if prefix_species is not None:
        for s in model.getListOfSpecies():
            sid = s.getId()
            sid_clipped = clip(sid, prefix_species)
            if sid != sid_clipped:
                replace[sid] = sid_clipped
                s.setId(sid_clipped)

    # TODO: clip genes

    # update all references to elements
    elements = model.getListOfAllElements()
    for e in elements:
        for id_old, id_new in iteritems(replace):
            e.renameSIdRefs(id_old, id_new)



def clip(string, prefix):
    """clips a prefix from the beginning of a string if it exists
    """
    return string[len(prefix):] if string.startswith(prefix) else string


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
