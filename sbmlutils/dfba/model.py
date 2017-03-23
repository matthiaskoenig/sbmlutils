"""
DFBA model structure.
"""
from __future__ import print_function, absolute_import, division
import os
import logging
import warnings
import tempfile
from collections import defaultdict
from six import iteritems

import libsbml
import roadrunner
import cobra

from sbmlutils.dfba import builder


#################################################

class DFBAModel(object):
    """ Model representation of an SBML DFBA model.

     The representation is used in the validation and also for simulation.
     """

    def __init__(self, sbml_path):
        """ Create the simulator with the top level SBML file.

        The models are resolved to their respective simulation framework.
        The top level network must be an ode network.

        :param sbml_path: absolute path of top level SBML file
        """

        # necessary to change the working directory to the sbml file directory
        # to resolve relative links to external model definitions.
        working_dir = os.getcwd()
        sbml_dir = os.path.dirname(sbml_path)
        os.chdir(sbml_dir)

        self.sbml_top = sbml_path
        self.sbml_dir = os.path.dirname(sbml_path)

        # read top level model
        self.doc_top = None
        self.model_top = None
        self.framework_top = None
        self.submodels = defaultdict(list)
        self.rr_comp = None
        self.fba_models = []
        self.flux_rules = []
        self.dt = None

        self._process_top()
        self._process_models()
        self._process_dt()
        # TODO: dummy species, dummy reactions
        # TODO: update and bounds

        # log model information
        logging.info(self)

        # change back the working dir
        os.chdir(working_dir)

    @property
    def fba_model(self):
        if self.fba_models is not None and len(self.fba_models) > 0:
            return self.fba_models[0]
        else:
            return None

    @staticmethod
    def get_framework(model):
        """ Get the framework for the given model/submodel object.
        Terms from the SBO modelling framework.

        This is the sbo which is set on the respective model/submodel element

        :param model:
        :return:
        """
        framework = None
        if model.isSetSBOTerm():

            # FIXME: better check for model framework
            sbo = model.getSBOTerm()
            if sbo == 624:
                framework = builder.MODEL_FRAMEWORK_FBA
            elif sbo in [293]:
                framework = builder.MODEL_FRAMEWORK_ODE
            # elif sbo == 63:
            #    framework = MODEL_FRAMEWORK_STOCHASTIC
            # elif sbo in [234, 547]:
            #     framework = MODEL_FRAMEWORK_LOGICAL
            else:
                warnings.warn("Modelling Framework not supported: {}".format(sbo))
        else:
            warnings.warn("SBOTerm for modelling framework not set")
            # try to find the FBA network nonetheless
            if model.getPlugin('fbc') is not None:
                warnings.warn("FBA model via fbc package")
                framework = builder.MODEL_FRAMEWORK_FBA

        return framework

    def __str__(self):
        """ Information string.

        Provides information about the initialized Simulator instance.
        """
        # top level
        s = "{}\n".format('-' * 80)
        s += "{} [{}]\n".format(self.model_top, self.framework_top)
        s += "{}\n".format('-' * 80)

        # sub models
        for framework in builder.MODEL_FRAMEWORKS:
            s += "{:<10} : {}\n".format(framework, self.submodels[framework])

        # dt
        s += "{:<10} : {}\n".format(builder.DT_ID, self.dt)
        # dummy reactions

        # flux rules
        s += "{:<10} :\n".format('flux rules', self.flux_rules)
        for key in sorted(self.flux_rules):
            value = self.flux_rules[key]
            s += "{:<12} {} <-> {}\n".format('', key, value)

        # fba model information
        for fba_model in self.fba_models:
            s += '\n' + fba_model.__str__()
        s += "{}\n".format('-' * 80)

        return s

    def flux_rules_str(self):
        """ Information string of FBA rules.

        :return:
        """
        lines = ['Flux rules:']
        for key, value in iteritems(self.flux_rules):
            lines.append('\t{} : {}'.format(key, value))
        return "\n".join(lines)

    def _process_top(self):
        """ Process the top model.

        Reads top model and submodels.

        :return:
        """
        logging.debug('* _process_top')
        self.doc_top = libsbml.readSBMLFromFile(self.sbml_top)
        self.model_top = self.doc_top.getModel()
        if self.model_top is None:
            warnings.warn("No top level model found.")

        self.framework_top = self.get_framework(self.model_top)
        if self.framework_top is not builder.MODEL_FRAMEWORK_ODE:
            warnings.warn("The top level model framework is not ode: {}".format(self.framework_top))

        # get submodels with frameworks
        top_plugin = self.model_top.getPlugin("comp")
        for submodel in top_plugin.getListOfSubmodels():
            # models are processed in the order they are listed in the listOfSubmodels
            framework = DFBAModel.get_framework(submodel)
            self.submodels[framework].append(submodel)

    def _process_models(self):
        """ Process and prepare models for simulation.

        Resolves the replacements and model couplings between the
        different frameworks and creates models which can be simulated with
        the different frameworks.

        An important step is finding the fba rules in the top model.

        :return:
        :rtype:
        """
        logging.debug('* _process_models')
        ###########################
        # FBA rules
        ###########################
        # process FBA assignment rules of the top model
        self.flux_rules = DFBAModel._process_flux_rules(self.model_top)

        ###########################
        # ODE model
        ###########################
        # the roadrunner ode file is the flattened comp file.
        # FBA parts do not change any of the kinetic subparts (only connections via replaced bounds
        # and fluxes).
        # Consequently, the ODE part can be solved as is, only the iterative update between ode and fba has
        # to be performed

        # remove FBA assignment rules from the model, so they can be set via the simulator
        # not allowed to set assignment rules directly in roadrunner
        for variable in self.flux_rules.values():
            self.model_top.removeRuleByVariable(variable)

        mixed_sbml_cleaned = tempfile.NamedTemporaryFile("w", suffix=".xml")
        libsbml.writeSBMLToFile(self.doc_top, mixed_sbml_cleaned.name)
        self.rr_comp = roadrunner.RoadRunner(mixed_sbml_cleaned.name)

        ###########################
        # prepare FBA models
        ###########################
        # FBA models are found based on the FBA modeling framework
        mdoc = self.doc_top.getPlugin("comp")
        for submodel in self.submodels[builder.MODEL_FRAMEWORK_FBA]:
            mref = submodel.getModelRef()
            emd = mdoc.getExternalModelDefinition(mref)
            source = emd.getSource()
            # check if relative path
            if not os.path.exists(source):
                s2 = os.path.join(self.sbml_dir, source)
                if not os.path.exists(s2):
                    warnings.warn('FBA source cannot be resolved:' + source)
                else:
                    source = s2

            # Create FBA model and process
            fba_model = FBAModel(submodel=submodel,
                                 source=source,
                                 flux_rules=self.flux_rules,
                                 model_top=self.model_top,
                                 rr_model=self.rr_comp)
            self.fba_models.append(fba_model)

    def _process_dt(self):
        """ Read the dt parameter for the DFBA.

        :return:
        """
        logging.debug('* _process_dt')
        p = self.model_top.getParameter(builder.DT_ID)
        if p is None:
            warnings.warn("No parameter with id '{}' in top model.".format(builder.DT_ID))
        self.dt = p.getValue()

    def set_dt(self, value):
        """ Sets the dt parameter in the DFBA model.
        Necessary when the model should be simulated with different dt values.
        """
        p = self.model_top.getParameter(builder.DT_ID)
        if p is None:
            warnings.warn("No parameter with id '{}' in top model.".format(builder.DT_ID))
        old_value = p.getValue()
        p.setValue(value)
        logging.info("dt set from old value <{}> to new value: dt={}".format(old_value, value))
        # update value in DFBA model
        self._process_dt()

    @classmethod
    def _process_flux_rules(cls, top_model):
        """ Find Flux AssignmentRules in top model.

        Find the flux assignment rules which assign a reaction rate to a parameter.
        This are the assignment rules synchronizing between FBA and ODE models.

        These are Assignment rules of the form
            pid = rid
        i.e. a reaction rate is assigned to a parameter.
        """
        logging.debug('* _process_flux_rules')
        flux_rules = {}

        for rule in top_model.getListOfRules():
            if not rule.isAssignment():
                continue
            variable = rule.getVariable()
            formula = rule.getFormula()
            parameter = top_model.getParameter(variable)
            if not parameter:
                continue
            reaction = top_model.getReaction(formula)
            if not reaction:
                continue
            # check the SBOTerm
            if not reaction.isSetSBOTerm():
                flux_rules[reaction.getId()] = parameter.getId()
            else:
                # check for : 'pseudoreaction'
                if reaction.getSBOTerm() == 631:
                    flux_rules[reaction.getId()] = parameter.getId()
                else:
                    warnings.warn('Flux AssignmentRules should have SBOTerm: SBO:0000631')

        return flux_rules


class FBAModel(object):
    """ FBA model.

    This class provides functionality for the fba submodels.
    Handles setting of FBA bounds & optimization.
    """

    def __init__(self, submodel, source, flux_rules, model_top=None, rr_model=None):
        """ Creates the FBAModel.
        Processes the bounds for all reactions.
        Reads the sbml and cobra model.
        Processes the bound replacements and updates.

        :param submodel:
        :param source:
        :param flux_rules:
        """
        self.source = source
        self.submodel = submodel

        # read sbml and cobra model
        self.sbml_doc = libsbml.readSBMLFromFile(source)
        self.sbml_model = self.sbml_doc.getModel()
        self.cobra_model = cobra.io.read_sbml_model(source)

        # bounds are mappings from parameters to reactions
        #       parameter_id -> [rid1, rid2, ...]
        self.ub_parameters = defaultdict(list)
        self.lb_parameters = defaultdict(list)
        self.fba2top_bounds = None
        self.fba2top_reactions = None
        self.flat_mapping = {}

        # flux rules
        self.flux_rules = flux_rules

        # objective sense
        self._process_objective_sense()
        # bounds
        self._process_bounds()
        if model_top is not None:
            # process the ode <-> fba connection
            self._process_bound_replacements(model_top)
            self._process_reaction_replacements(model_top)

        # id mapping
        if rr_model is not None:
            self._process_flat_mapping(rr_model)

    def __str__(self):
        """ Information string. """
        # s = "{}\n".format('-' * 80)
        s = "{} {}\n".format(self.submodel, self.source)
        # s += "{}\n".format('-' * 80)
        s += "\t{:<20}: {}\n".format('objective sense', self.objective_sense)
        s += "\t{:<20}: {}\n".format('flux rules', self.flux_rules)
        s += "\t{:<20}: {}\n".format('ub parameters', self.ub_parameters)
        s += "\t{:<20}: {}\n".format('lb parameters', self.lb_parameters)
        s += "\t{:<20}: {}\n".format('fba2top bounds', self.fba2top_bounds)
        s += "\t{:<20}: {}\n".format('fba2top reactions', self.fba2top_reactions)
        s += "\t{:<20}: {}\n".format('flat mapping', self.flat_mapping)
        # s += "{}\n".format('-' * 80)

        return s

    def _process_objective_sense(self):
        """ Read the objective sense from the fba model objective.

        :return:
        """
        logging.debug('* (fba) _process_flux_rules')
        fmodel = self.sbml_model.getPlugin("fbc")
        flist = fmodel.getListOfObjectives()
        active_oid = flist.getActiveObjective()
        objective = fmodel.getObjective(active_oid)
        self.objective_sense = objective.getType()

    def _process_bounds(self):
        """  Determine which parameters are upper and lower bounds for reactions.

        The dictionaries allow simple lookup of the bound parameters for update.

        :return:
        :rtype:
        """
        logging.debug('* (fba) _process_bounds')
        for r in self.sbml_model.getListOfReactions():
            fbc_r = r.getPlugin("fbc")
            rid = r.getId()
            if fbc_r.isSetUpperFluxBound():
                self.ub_parameters[fbc_r.getUpperFluxBound()].append(rid)
            if fbc_r.isSetLowerFluxBound():
                self.lb_parameters[fbc_r.getLowerFluxBound()].append(rid)

    def _process_bound_replacements(self, top_model):
        """ Process the top bound replacements once.

        This provides the parameters of the dynamic upper and lower flux bounds and how
        they map the the bounds of the FBA model.

        Creates dictionary of parameter
        { pid (fba) : pid (top) }
        fba parameter ids : top parameter ids

        Necessary for the update of bounds from ode solution.
        """
        logging.debug('* (fba) _process_bound_replacements')
        fba2top = {}
        comp_model = self.sbml_model.getPlugin('comp')

        for p in top_model.getListOfParameters():
            top_pid = p.getId()
            comp_p = p.getPlugin("comp")

            rep_elements = comp_p.getListOfReplacedElements()
            # only process parameters with ReplacedBy elements
            if rep_elements:
                for rep_element in rep_elements:
                    # the submodel of the replacement belongs to the current fba submodel
                    if rep_element.getSubmodelRef() == self.submodel.getId():
                        portRef = rep_element.getPortRef()
                        # get the port
                        port = comp_model.getPort(portRef)
                        # get the id of object for port
                        id_ref = port.getIdRef()
                        # store
                        fba2top[id_ref] = top_pid
        self.fba2top_bounds = fba2top

    def _process_reaction_replacements(self, top_model):
        """ Finds mapping between top reactions and fba reactions.

        Necessary for update of top reactions from FBA solution.

        :param flux_rules:
        :type flux_rules:
        :return:
        :rtype:
        """
        logging.debug('* (fba) _process_reaction_replacements')
        fba2top = {}
        comp_model = self.sbml_model.getPlugin('comp')

        for r in top_model.getListOfReactions():
            top_rid = r.getId()
            comp_r = r.getPlugin("comp")
            rep_by = comp_r.getReplacedBy()

            # only process reactions which are replaced with reactions from the
            # fba model
            if rep_by is not None:
                if rep_by.getSubmodelRef() == self.submodel.getId():
                    portRef = rep_by.getPortRef()
                    # get the port
                    port = comp_model.getPort(portRef)
                    # get the id of object for port
                    id_ref = port.getIdRef()
                    # store
                    fba2top[id_ref] = top_rid

        self.fba2top_reactions = fba2top

    def _process_flat_mapping(self, rr_comp):
        """ Get the id mapping of the fluxes to the flattened model.

        :param rr_comp
        :return:
        """
        smid = self.submodel.getId()
        mapping = {}

        # FIXME: use the replacements, replacedBy & ports for the mapping detection with the top_model
        # get all the FBA reaction ids

        fba_rids = set()
        for rid in rr_comp.model.getReactionIds():
            # mapping relies on submodel prefix !
            if rid.startswith('{}__'.format(smid)):
                fba_rids.add(rid)

        for r in self.sbml_model.getListOfReactions():
            rid = r.getId()
            if '{}__{}'.format(smid, rid) in fba_rids:
                mapping[rid] = '{}__{}'.format(smid, rid)
            else:
                # FIXME: the mapping of the dummy reactions is missing
                # This is a bad hack which relies of the naming of the dummy reactions
                mapping[rid] = 'dummy_{}'.format(rid)

        self.flat_mapping = mapping
