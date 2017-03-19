"""
Building DFBA models by providing.

FBA SBML models in combination with the variable species.


"""
from __future__ import print_function, division
import logging
import warnings
from sbmlutils import factory as fac
from sbmlutils import comp

#################################################
# Logging
#################################################
logging.basicConfig(format='%(message)s', level=logging.DEBUG)

#################################################
# Builder constants
#################################################

LOWER_BOUND_DEFAULT = -1000
UPPER_BOUND_DEFAULT = 1000
LOWER_BOUND_PREFIX = 'lb_'
UPPER_BOUND_PREFIX = 'ub_'
EXCHANGE_REACTION_PREFIX = 'EX_'

SBO_FLUX_BOUND = "SBO:0000625"
SBO_EXCHANGE_REACTION = "SBO:0000627"


def create_exchange_reaction(model, species_id, reversible=True, flux_unit=None):
    """ Factory method to create exchange reaction for species.
    Creates the exchange reaction, the upper and lower bounds,
    and the ports.

    :param model:
    :param species:
    :param reversible:
    :param flux_unit:
    :return:
    :rtype:
    """
    # id (e.g. EX_A)
    ex_rid = EXCHANGE_REACTION_PREFIX + species_id
    ub_id = UPPER_BOUND_PREFIX + ex_rid
    lb_id = LOWER_BOUND_PREFIX + ex_rid

    lb_value = LOWER_BOUND_DEFAULT
    if not reversible:
        lb_value = 0

    parameters = [
        fac.Parameter(sid=lb_id,
                      value=lb_value,
                      unit=flux_unit, constant=True, sboTerm=SBO_FLUX_BOUND),
        fac.Parameter(sid=ub_id,
                      value=UPPER_BOUND_DEFAULT,
                      unit=flux_unit, constant=True, sboTerm=SBO_FLUX_BOUND),
    ]
    fac.create_objects(model, parameters)

    # exchange reactions
    ex_r = fac.create_reaction(model, rid=ex_rid, reversible=reversible,
                               reactants={species_id: 1}, sboTerm=SBO_EXCHANGE_REACTION)

    # exchange bounds
    fac.set_flux_bounds(ex_r, lb=lb_id, ub=ub_id)

    # create ports
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=[ex_rid, lb_id, ub_id])

    return ex_r


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
                fac.Parameter(sid="{}_{}".format(bound_type, ex_rid), value=value, unit=unit, constant=False,
                                  sboTerm=SBO_FLUX_BOUND)
            )
    return parameters
