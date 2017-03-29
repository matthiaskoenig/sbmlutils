"""
Factory methods to create flow and diffusion reactions.
"""
from __future__ import print_function

import oven.sinusoid.sinnaming as naming
from .reaction import ReactionTemplate


def createFlowReactionTemplate(sid, c_from, c_to, flow, unit='mole_per_s'):
    """ Create ReactionTemplate for flow reaction. """
    sid_from = naming.createLocalizedId(c_from, sid)
    sid_to = naming.createLocalizedId(c_to, sid)
    rid = naming.createFlowId(c_from, c_to, sid)
    name = naming.createFlowName(c_from, c_to, sid)
    # create equation
    if c_to != naming.NONE_ID:
        equation = '{} => {} []'.format(sid_from, sid_to)
    else:
        equation = '{} => []'.format(sid_from)
    formula = '{} * {}'.format(flow, sid_from)

    rt = ReactionTemplate(
        rid=rid,
        name=name,
        equation=equation,
        formula=(formula, unit)
    )
    return rt


def createDiffusionReactionTemplate(sid, c_from, c_to, D, unit="mole_per_s"):
    """ Create ReactionTemplate for diffusion reaction. """
    sid_from = naming.createLocalizedId(c_from, sid)
    sid_to = naming.createLocalizedId(c_to, sid)
    rid = naming.createDiffusionId(c_from, c_to, sid)
    name = naming.createDiffusionName(c_from, c_to, sid)

    # create equation
    if c_to != naming.NONE_ID:
        equation = '{} <-> {} []'.format(sid_from, sid_to)
    else:
        equation = '{} => []'.format(sid_from)

    # kinetics
    if c_to:
        formula = "{} * ({} - {})".format(D, sid_from, sid_to)  # in [mole/s]
    else:
        formula = "{} * ({})".format(D, sid_from)

    rt = ReactionTemplate(
        rid=rid,
        name=name,
        equation=equation,
        formula=(formula, unit)
    )
    return rt
