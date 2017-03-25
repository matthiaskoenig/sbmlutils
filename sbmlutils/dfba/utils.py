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


def clip_prefixes_in_model(model):
    """ Removes the unnecessary Bigg prefixes.
    R_ for reactions, M_ for metabolites and G_ for genes.
    
    :param model: 
    :type model: 
    :return: 
    :rtype: 
    """

    # clip reactions
    rdict = {}
    for r in model.getListOfReactions():
        rid = r.getId()
        rid_clipped = clip(rid, "R_")
        if rid != rid_clipped:
            rdict[rid] = rid_clipped
            r.setId(rid_clipped)

    # clip metabolites
    sdict = {}
    for s in model.getListOfSpecies():
        sid = s.getId()
        sid_clipped = clip(sid, "M_")
        if sid != sid_clipped:
            sdict[sid] = sid_clipped
            s.setId(sid_clipped)

    def replace_sref(sref_list):
        for s_ref in sref_list:
            # print(s_ref, type(s_ref))
            sref_id = s_ref.getSpecies()
            if sref_id in sdict:
                s_ref.setSpecies(sdict[sref_id])

    # clip reactants, products and modifiers of reactions
    for r in model.getListOfReactions():
        replace_sref(r.getListOfReactants())
        replace_sref(r.getListOfProducts())
        replace_sref(r.getListOfModifiers())

    # fbc reactions
    fbc_model = model.getPlugin("fbc")
    for obj in fbc_model.getListOfObjectives():
        for flux_obj in obj.getListOfFluxObjectives():
            fo_rid = flux_obj.getReaction()
            if fo_rid in rdict:
                flux_obj.setReaction(rdict[fo_rid])

    # group member ids
    groups_model = model.getPlugin("groups")
    for group in groups_model.getListOfGroups():
        for member in group.getListOfMembers():
            id_ref = member.getIdRef()
            if id_ref in rdict:
                member.setIdRef(rdict[id_ref])
            if id_ref in sdict:
                member.setIdRef(sdict[id_ref])


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
