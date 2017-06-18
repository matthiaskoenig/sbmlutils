"""
Helper functions and information for building DFBA models.
"""

from __future__ import print_function, absolute_import, division
import warnings
import logging

from sbmlutils import factory as fac
from sbmlutils import comp
from sbmlutils.dfba import utils

from six import iteritems
import inspect

import libsbml


#################################################
# Builder constants
#################################################
MODEL_FRAMEWORK_FBA = 'fba'
MODEL_FRAMEWORK_ODE = 'ode'
# MODEL_FRAMEWORK_STOCHASTIC = 'stochastic'
# MODEL_FRAMEWORK_LOGICAL = 'logical'


MODEL_FRAMEWORKS = {
    MODEL_FRAMEWORK_FBA: ["SBO:0000624"],
    MODEL_FRAMEWORK_ODE: ["SBO:0000293"],
    # MODEL_FRAMEWORK_STOCHASTIC,
    # MODEL_FRAMEWORK_LOGICAL,
}

# dt parameter
DT_ID = 'dt'
DT_SIM = 0.1
DT_SBO = "SBO:0000346"

# flux bounds
LOWER_BOUND_DEFAULT = -1000
UPPER_BOUND_DEFAULT = 1000
ZERO_BOUND = 0
LOWER_BOUND_PREFIX = 'lb_'
UPPER_BOUND_PREFIX = 'ub_'
FLUX_BOUND_SBO = "SBO:0000625"

# update reactions
UPDATE_REACTION_PREFIX = "update_"
UPDATE_REACTION_SBO = "SBO:0000631"
UPDATE_PARAMETER_SBO = "SBO:0000613"

# exchange reactions
EXCHANGE_REACTION_PREFIX = 'EX_'
EXCHANGE_REACTION_SBO = "SBO:0000627"
EXCHANGE = 'exchange'
EXCHANGE_IMPORT = 'import'
EXCHANGE_EXPORT = 'export'

# top
FLUX_PARAMETER_PREFIX = 'p' + EXCHANGE_REACTION_PREFIX
DUMMY_REACTION_PREFIX = EXCHANGE_REACTION_PREFIX
DUMMY_SPECIES_ID = "dummy_S"
DUMMY_SPECIES_SBO = "SBO:0000291"
DUMMY_REACTION_SBO = "SBO:0000631"
FLUX_PARAMETER_SBO = "SBO:0000612"
FLUX_ASSIGNMENTRULE_SBO = "SBO:0000391"

SBML_LEVEL = 3
SBML_VERSION = 1
SBML_FBC_NAME = libsbml.FbcExtension_getPackageName()
SBML_FBC_VERSION = 2
SBML_COMP_NAME = libsbml.CompExtension_getPackageName()
SBML_COMP_VERSION = 1

libsbml.CompExtension_getPackageName()

#################################################


def get_framework(model):
    """ Get the framework for the given model object.

    This is the sbo which is set on the respective model/modelDefinition element.

    :param model:
    :return: framework key or None if no framework information could be found.
    """

    if type(model) not in [libsbml.Model, libsbml.ModelDefinition]:
        raise ValueError("Framework must be defined on either Model/ModelDefinition, but given: {}".format(model))

    framework = None
    if model.isSetSBOTerm():

        sbo = model.getSBOTermID()
        for fw, sbos in iteritems(MODEL_FRAMEWORKS):
            if sbo in sbos:
                framework = fw
    else:
        warnings.warn("SBOTerm for modelling framework not set")
    if framework is None:
        warnings.warn("No framework set for: {}".format(model))

    return framework


def template_doc_fba(model_id):
    """ create template for fba model.
    
    :param model_id: model identifier
    :return: SBMLDocument
    """
    sbmlns = libsbml.SBMLNamespaces(SBML_LEVEL, SBML_VERSION)
    sbmlns.addPackageNamespace(SBML_FBC_NAME, SBML_FBC_VERSION)
    sbmlns.addPackageNamespace(SBML_COMP_NAME, SBML_COMP_VERSION)

    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired(SBML_COMP_NAME, True)
    doc.setPackageRequired(SBML_FBC_NAME, False)
    model = doc.createModel()
    mplugin = model.getPlugin(SBML_FBC_NAME)
    mplugin.setStrict(True)

    # model
    model.setId('{}_fba'.format(model_id))
    model.setName('{} (FBA)'.format(model_id))
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)
    return doc


def template_doc_bounds(model_id, create_min_max=True):
    """ Create template bounds model.
    
    Adds min and max functions 
    
    :param model_id: model identifier
    :return: SBMLDocument
    """
    sbmlns = libsbml.SBMLNamespaces(SBML_LEVEL, SBML_VERSION, 'comp', SBML_COMP_VERSION)
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired(SBML_COMP_NAME, True)
    model = doc.createModel()
    model.setId("{}_bounds".format(model_id))
    model.setName("{} (BOUNDS)".format(model_id))
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    if create_min_max:
        objects = [
            # definition of min and max
            fac.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='min'),
            fac.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='max'),
        ]
        fac.create_objects(model, objects)

    return doc


def template_doc_update(model_id):
    """ Create template update model.
    
    :param model_id: model identifier
    :return: SBMLDocument
    """
    sbmlns = libsbml.SBMLNamespaces(SBML_LEVEL, SBML_VERSION, 'comp', SBML_COMP_VERSION)
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired(SBML_COMP_NAME, True)

    # model
    model = doc.createModel()
    model.setId("{}_update".format(model_id))
    model.setName("{} (UPDATE)".format(model_id))
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    return doc


def template_doc_top(model_id, emds):
    """ Create template top model.
    Adds the ExternalModelDefinitions and submodels for FBA, BOUNDS & UPDATE model.
    
    :param model_id: model identifier
    :return: SBMLDocument
    """
    sbmlns = libsbml.SBMLNamespaces(SBML_LEVEL, SBML_VERSION, 'comp', SBML_COMP_VERSION)
    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired(SBML_COMP_NAME, True)
    doc.setPackageRequired(SBML_FBC_NAME, False)

    # create models and submodels
    model = doc.createModel()
    model.setId("{}_top".format(model_id))
    model.setName("{} (TOP)".format(model_id))
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    # create listOfExternalModelDefinitions
    doc_comp = doc.getPlugin(SBML_COMP_NAME)
    emd_fba = comp.create_ExternalModelDefinition(doc_comp, "{}_fba".format(model_id), source=emds["{}_fba".format(model_id)])
    emd_bounds = comp.create_ExternalModelDefinition(doc_comp, "{}_bounds".format(model_id), source=emds["{}_bounds".format(model_id)])
    emd_update = comp.create_ExternalModelDefinition(doc_comp, "{}_update".format(model_id), source=emds["{}_update".format(model_id)])

    # add submodel which references the external model definition
    doc_model = model.getPlugin(SBML_COMP_NAME)
    comp.add_submodel_from_emd(doc_model, submodel_id="fba", emd=emd_fba)
    comp.add_submodel_from_emd(doc_model, submodel_id="bounds", emd=emd_bounds)
    comp.add_submodel_from_emd(doc_model, submodel_id="update", emd=emd_update)

    return doc


def create_dfba_compartment(model, compartment_id, unit_volume=None, create_port=True):
    """ Creates the main compartment for the dynamic species.
    
    :param model: 
    :param compartment_id: id
    :param unit_volume: unit
    :param create_port: flag to create port
    :return: created libsbml.Compartment
    """
    objects = [
        fac.Compartment(sid=compartment_id, value=1.0, unit=unit_volume, constant=True, name=compartment_id,
                        spatialDimensions=3),
    ]
    c = fac.create_objects(model, objects)
    if create_port:
        comp.create_ports(model, idRefs=[compartment_id])
    return c


def create_dfba_species(model, model_fba, compartment_id, hasOnlySubstanceUnits=False, unit=None, create_port=True):
    """ Add DFBA species and compartments from fba model to model. 
    Creates the dynamic species and respetive compartments with
    the necessary ports.
    This is used in the bounds submodel, update submodel and the
    and top model.
    
    :param model: 
    :param model_fba: 
    :return: 
    """
    objects = []
    port_sids = []
    ex_rids = utils.find_exchange_reactions(model_fba)
    for ex_rid in ex_rids:
        r = model_fba.getReaction(ex_rid)
        sid = r.getReactant(0).getSpecies()
        s = model_fba.getSpecies(sid)

        # exchange species to create
        objects.append(
            fac.Species(sid=sid, name=s.getName(), value=1.0, unit=unit,
                        hasOnlySubstanceUnits=hasOnlySubstanceUnits, compartment=compartment_id)
        )
        # port of exchange species
        port_sids.append(sid)

    fac.create_objects(model, objects)
    if create_port:
        comp.create_ports(model, idRefs=port_sids)


def create_dfba_dt(model, step_size=DT_SIM, time_unit=None, create_port=True):
    """ Creates the dt parameter in the model.

    :param step_size:
    :type step_size:
    :param time_unit:
    :type time_unit:
    :return:
    :rtype:
    """
    objects = [
        fac.Parameter(sid=DT_ID, value=step_size, unit=time_unit, constant=True, sboTerm=DT_SBO)
    ]
    fac.create_objects(model, objects)
    if create_port:
        comp.create_ports(model, idRefs=[DT_ID])


def check_exchange_reaction(model, reaction_id):
    """ Checks that the exchange reactions fullfills the necessary specification.

    :param model: SBML model
    :param reaction_id: id of exchange reaction
    :return: boolean true or false 
    """
    valid = True
    sid = None
    r = model.getReaction(reaction_id)
    if len(r.getListOfModifiers()) > 0:
        warnings.warn("modfiers set on exchange reaction:".format(r))
        valid = False
    if len(r.getListOfProducts()) > 0:
        warnings.warn("products set on exchange reaction:".format(r))
        valid = False
    if len(r.getListOfReactants()) == 0:
        warnings.warn("no reactant set on exchange reaction:".format(r))
        valid = False
    elif len(r.getListOfReactants()) > 1:
        warnings.warn("more than one reactant set on exchange reaction:".format(r))
        valid = False
    else:
        sref = r.getReactant(0)
        if abs(sref.getStoichiometry() - 1.0) > 1E-6:
            warnings.warn("stoichiometry of reactant not 1.0 on exchange reaction:".format(r))
            valid = False
        sid = sref.getSpecies()
    if sid is not None:
        if reaction_id != EXCHANGE_REACTION_PREFIX + sid:
            warnings.warn("exchange reaction id does not follow EX_sid: {} != {}".format(reaction_id,
                                                                                         EXCHANGE_REACTION_PREFIX + sid))
    if not r.isSetSBOTerm():
        warnings.warn("no SBOTerm set on exchange reaction".format(r))
    else:
        if r.getSBOTermID() != EXCHANGE_REACTION_SBO:
            warnings.warn("exchange reaction id {} != {}:".format(r.getSBOTermId(), EXCHANGE_REACTION_SBO))
    if not r.getReversible():
        warnings.warn("exchange reaction is not reversible: {}".format(r))
    return valid


def create_exchange_reaction(model, species_id, exchange_type=EXCHANGE, flux_unit=None):
    """ Factory method to create exchange reactions for species in the FBA model.

    Creates the exchange reaction, the upper and lower bounds,
    and the ports.

    :param model:
    :param species:
    :param reversible:
    :param flux_unit:
    :return:
    :rtype:
    """
    if exchange_type not in [EXCHANGE, EXCHANGE_IMPORT, EXCHANGE_EXPORT]:
        raise ValueError("Wrong exchange_type: {}".format(exchange_type))

    # id (e.g. EX_A)
    ex_rid = EXCHANGE_REACTION_PREFIX + species_id
    lb_id = LOWER_BOUND_PREFIX + ex_rid
    ub_id = UPPER_BOUND_PREFIX + ex_rid

    lb_value = LOWER_BOUND_DEFAULT
    ub_value = UPPER_BOUND_DEFAULT
    if exchange_type == EXCHANGE_IMPORT:
        # negative flux through exchange reaction
        ub_value = ZERO_BOUND
    if exchange_type == EXCHANGE_EXPORT:
        lb_value = ZERO_BOUND

    parameters = [
        fac.Parameter(sid=lb_id,
                      value=lb_value,
                      unit=flux_unit, constant=True, sboTerm=FLUX_BOUND_SBO),
        fac.Parameter(sid=ub_id,
                      value=ub_value,
                      unit=flux_unit, constant=True, sboTerm=FLUX_BOUND_SBO),
    ]
    fac.create_objects(model, parameters)

    # exchange reactions are all reversible (it depends on the bounds in which direction they operate)
    ex_r = fac.create_reaction(model, rid=ex_rid, reversible=True,
                               reactants={species_id: 1}, sboTerm=EXCHANGE_REACTION_SBO)

    # exchange bounds
    fac.set_flux_bounds(ex_r, lb=lb_id, ub=ub_id)

    # create ports
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=[ex_rid, lb_id, ub_id])

    return ex_r


def update_exchange_reactions(model, flux_unit):
    """ Updates existing exchange reaction in FBA model.
    
    Sets all the necessary information and checks that correct.
    This is mainly used to prepare the exchange reactions of metabolites.
    
    :param model: 
    :param ex_rids: 
    :return: 
    """

    # mapping of bounds to reactions
    bounds_dict = dict()

    ex_rids = utils.find_exchange_reactions(model)
    for ex_rid in ex_rids:
        r = model.getReaction(ex_rid)

        # make reversible
        if not r.getReversible():
            r.setReversible(True)
            logging.info("Exchange reaction set reversible: {}".format(r.getId()))

        # fix ids for exchange reactions
        sref = r.getReactant(0)
        sid = sref.getSpecies()
        rid = r.getId()
        if rid != EXCHANGE_REACTION_PREFIX + sid:
            r.setId(EXCHANGE_REACTION_PREFIX + sid)
            logging.warning("Exchange reaction fixd id: {} -> {}".format(rid, EXCHANGE_REACTION_PREFIX + sid))

    # new lookup necessary, due to possible changed ids
    ex_rids = utils.find_exchange_reactions(model)
    for ex_rid in ex_rids:
        r = model.getReaction(ex_rid)
        fbc_r = r.getPlugin(SBML_FBC_NAME)
        # store bounds in dictionary for value lookup
        for f_bound in ["getLowerFluxBound", "getUpperFluxBound"]:
            bound_id = getattr(fbc_r, f_bound).__call__()
            bound = model.getParameter(bound_id)
            bounds_dict[bound_id] = bound.getValue()

    # create unique bounds for exchange reactions
    for ex_rid in ex_rids:
        r = model.getReaction(ex_rid)
        fbc_r = r.getPlugin(SBML_FBC_NAME)
        lb_value = model.getParameter(fbc_r.getLowerFluxBound()).getValue()
        ub_value = model.getParameter(fbc_r.getUpperFluxBound()).getValue()

        lb_id = LOWER_BOUND_PREFIX + ex_rid
        ub_id = UPPER_BOUND_PREFIX + ex_rid

        parameters = [
            fac.Parameter(sid=lb_id,
                          value=lb_value,
                          unit=flux_unit, constant=True, sboTerm=FLUX_BOUND_SBO),
            fac.Parameter(sid=ub_id,
                          value=ub_value,
                          unit=flux_unit, constant=True, sboTerm=FLUX_BOUND_SBO),
        ]
        fac.create_objects(model, parameters)

        # set bounds
        fac.set_flux_bounds(r, lb=lb_id, ub=ub_id)

        # create ports for bounds and reaction
        comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=[ex_rid, lb_id, ub_id])

    # check all the exchange reactions
    for ex_rid in ex_rids:
        check_exchange_reaction(model, ex_rid)

    # FIXME: remove unused bounds
    # There could be unused bounds in the model which can be removed


def create_update_reactions(model, model_fba, formula="-{}", unit_flux=None, modifiers=[]):
    """ Creates all update reactions with the given formula.
    
    :param model: 
    :param model_fba: 
    :param formula: 
    :param unit_flux: 
    :param modifiers: 
    :return: 
    """
    ex_rids = utils.find_exchange_reactions(model_fba)
    for ex_rid, sid in iteritems(ex_rids):
        create_update_parameter(model=model, sid=sid, unit_flux=unit_flux)
        create_update_reaction(model=model, sid=sid, modifiers=modifiers, formula=formula)


def create_update_reaction(model, sid, modifiers=[], formula="-{}"):
    """ Creates the update reaction for a given species.
    Creates the update parameter in the process.

    :param model:
    :param sid:
    :param modifiers:
    :param formula:
    :return:
    :rtype:
    """
    rid_update = UPDATE_REACTION_PREFIX + sid

    # format the formula
    formula = formula.format(FLUX_PARAMETER_PREFIX + sid)
    fac.create_reaction(model, rid=rid_update, sboTerm=UPDATE_REACTION_SBO,
                       reactants={sid: 1}, modifiers=modifiers,
                       formula=formula)


def create_update_parameter(model, sid, unit_flux):
    """ Creates the update parameter.
    The update parameter correspond to the flux parameters
    in the top model.

    :param model:
    :type model:
    :param sid:
    :type sid:
    :param unit_flux:
    :type unit_flux:
    :return:
    :rtype:
    """
    pid = FLUX_PARAMETER_PREFIX + sid
    parameter = fac.Parameter(sid=pid, value=1.0, constant=True, unit=unit_flux, sboTerm=UPDATE_PARAMETER_SBO)
    fac.create_objects(model, [parameter])
    # create port
    comp.create_ports(model, portType=comp.PORT_TYPE_PORT,
                      idRefs=[pid])
    return pid


def create_exchange_bounds(model, model_fba, unit_flux=None, create_ports=True):
    """ Creates the exchange reaction flux bounds.
    
    :param model: 
    :param model_fba: 
    :param unit_flux: 
    :param create_ports: 
    :return: 
    """
    ex_rids = utils.find_exchange_reactions(model_fba)
    objects = []
    port_sids = []
    for ex_rid, sid in iteritems(ex_rids):
        r = model_fba.getReaction(ex_rid)

        # lower & upper bound parameters
        r_fbc = r.getPlugin(SBML_FBC_NAME)
        lb_id = r_fbc.getLowerFluxBound()
        lb_value = model_fba.getParameter(lb_id).getValue()
        ub_id = r_fbc.getUpperFluxBound()
        ub_value = model_fba.getParameter(ub_id).getValue()

        objects.extend([
            # for assignments
            fac.Parameter(sid=lb_id, value=lb_value, unit=unit_flux, constant=False, sboTerm=FLUX_BOUND_SBO),
            fac.Parameter(sid=ub_id, value=ub_value, unit=unit_flux, constant=False, sboTerm=FLUX_BOUND_SBO),
        ])
        port_sids.extend([lb_id, ub_id])

    # create bounds
    fac.create_objects(model, objects)
    # create ports
    if create_ports:
        comp.create_ports(model, idRefs=port_sids)


def create_dummy_species(model, compartment_id, unit=None, hasOnlySubstanceUnits=False):
    """ Creates the dummy species in the top model.
    Adds a deletion in the top model which removes the object again.

    :param model: SBML model
    :param compartment_id: compartment
    :param unit: unit
    :param hasOnlySubstanceUnits: switch if amount or concentration
    :return: 
    """
    # dummy species for dummy reactions (empty set)
    fac.create_objects(model,
                       [fac.Species(sid=DUMMY_SPECIES_ID, name=DUMMY_SPECIES_ID, value=0, unit=unit,
                                    hasOnlySubstanceUnits=hasOnlySubstanceUnits,
                                    compartment=compartment_id, sboTerm=DUMMY_SPECIES_SBO),
                        ])


def create_dummy_reactions(model, model_fba, unit_flux=None):
    """ Creates the dummy reactions.
    This also creates the corresponding flux parameters and flux assignments.
    
    :param model: 
    :param dfba_model: 
    :return: 
    """
    ex_rids = utils.find_exchange_reactions(model_fba)
    objects = []
    for ex_rid, sid in iteritems(ex_rids):

        pid_flux = FLUX_PARAMETER_PREFIX + sid
        rid_flux = DUMMY_REACTION_PREFIX + sid

        objects.append(
            # flux parameter: fluxe from fba (rate of reaction)
            fac.Parameter(sid=pid_flux, value=1.0, constant=True, unit=unit_flux, sboTerm=FLUX_PARAMETER_SBO),
        )

        # dummy reaction (pseudoreaction)
        fac.create_reaction(model, rid=rid_flux, reversible=False,
                            products={DUMMY_SPECIES_ID: 1}, sboTerm=DUMMY_REACTION_SBO,
                            formula='0 {}'.format(unit_flux))

        # flux assignment rule
        objects.append(
            fac.AssignmentRule(pid_flux, value=rid_flux, sboTerm=FLUX_ASSIGNMENTRULE_SBO),
        )
    fac.create_objects(model, objects)


def create_top_replacedBy(model, model_fba):
    """ Creates the replacedBy Elements in the top model.
    
    :param model: 
    :param model_fba: 
    :return: 
    """

    ex_rids = utils.find_exchange_reactions(model_fba)
    for ex_rid, sid in iteritems(ex_rids):
        comp.replaced_by(model, DUMMY_REACTION_PREFIX + sid, ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="{}_port".format(EXCHANGE_REACTION_PREFIX + sid))


def create_top_replacements(model, model_fba, compartment_id):
    """ Create all the replacements in the top model.
    
    :param model: 
    :param model_fba: 
    :return: 
    """

    # compartment
    comp.replace_elements(model, compartment_id, ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={
                              'update': ['{}_port'.format(compartment_id)],
                              'bounds': ['{}_port'.format(compartment_id)]})

    # dt
    comp.replace_elements(model, 'dt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['dt_port']})

    # species dependent replacements
    ex_rids = utils.find_exchange_reactions(model_fba)
    for ex_rid, sid in iteritems(ex_rids):

        # flux parameters
        comp.replace_elements(model, FLUX_PARAMETER_PREFIX + sid, ref_type=comp.SBASE_REF_TYPE_PORT,
                              replaced_elements={'update': ['{}_port'.format(FLUX_PARAMETER_PREFIX + sid)]})

        # dynamic species
        comp.replace_elements(model, sid, ref_type=comp.SBASE_REF_TYPE_PORT,
                              replaced_elements={
                                  'bounds': ['{}_port'.format(sid)],
                                  'update': ['{}_port'.format(sid)]})

        # bounds of exchange reactions
        for replace_id in [
                           UPPER_BOUND_PREFIX + EXCHANGE_REACTION_PREFIX + sid,
                           LOWER_BOUND_PREFIX + EXCHANGE_REACTION_PREFIX + sid]:

            comp.replace_elements(model, replace_id, ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={
                              'bounds': ['{}_port'.format(replace_id)],
                              'fba': ['{}_port'.format(replace_id)]})

    # replace units
    for unit in model.getListOfUnitDefinitions():
        uid = unit.getId()
        comp.replace_element_in_submodels(model, uid, ref_type=comp.SBASE_REF_TYPE_UNIT,
                                          submodels=['bounds', 'fba', 'update'])
