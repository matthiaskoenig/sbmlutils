"""
Factory methods for the creation of flow and diffusion reactions.
"""
# TODO: update the Reaction factories to reflext the common standard for
#   defining rules and parameters

from sbmlutils.modelcreator import *
import ReactionTemplate

def createFlowReaction(model, sid, c_from, c_to, flow):
    """ Creates the convection reaction of sid between c_from -> c_to."""
    sid_from = createLocalizedId(c_from, sid)
    sid_to = createLocalizedId(c_to, sid)
    rid = createFlowId(c_from, c_to, sid)
    rname = createFlowName(c_from, c_to, sid)
    
    # reaction
    r = model.createReaction()
    r.setId(rid)
    r.setName(rname)
    r.setReversible(False)
    r.setFast(False)
    
    # equation
    sref = r.createReactant()
    sref.setSpecies(sid_from)
    sref.setStoichiometry(1.0)
    sref.setConstant(True)
    if c_to != NONE_ID:
        sref = r.createProduct()
        sref.setSpecies(sid_to)
        sref.setStoichiometry(1.0)
        sref.setConstant(True)
    
    # kinetics
    formula = '{} * {}'.format(flow, sid_from)  # in [mole/s]
    ReactionTemplate.setKineticLaw(model, r, formula)

    return r


def createDiffusionReaction(model, sid, c_from, c_to, D):
    """ Creates the diffusion reaction of sid between c_from <-> c_to. """
    sid_from = createLocalizedId(c_from, sid)
    sid_to = createLocalizedId(c_to, sid)
    rid = createDiffusionId(c_from, c_to, sid)
    name = createDiffusionName(c_from, c_to, sid)
    
    # reaction
    r = model.createReaction()
    r.setId(rid)
    r.setName(name)
    r.setReversible(True)
    r.setFast(False)
    
    # equation
    sref = r.createReactant()
    sref.setSpecies(sid_from)
    sref.setStoichiometry(1.0)
    sref.setConstant(True)
    if c_to != NONE_ID:
        sref = r.createProduct()
        sref.setSpecies(sid_to)
        sref.setStoichiometry(1.0)
        sref.setConstant(True)

    # kinetics
    if c_to:
        formula = "{} * ({} - {})".format(D, sid_from, sid_to)  # in [mole/s]
    else:
        formula = "{} * ({})".format(D, sid_from)
    ReactionTemplate.setKineticLaw(model, r, formula)

    return r
