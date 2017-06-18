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
from sbmlutils import comp


#################################################

class DFBAModel(object):
    """ Model representation of an SBML DFBA model.

     The representation is used in the validation and also for simulation.
     """

    def __init__(self, sbml_path):
        """ Create the simulator with the top level SBML file.

        The models are resolved to their respective simulation framework.
        The top level network must be an ode network.

        :param sbml_path: path to top level SBML file
        """

        # necessary to change the working directory to the sbml file directory
        # to resolve relative links to external model definitions.
        working_dir = os.getcwd()
        sbml_path = os.path.abspath(sbml_path)
        try:
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
            self.flux_rules = {}
            self.dt = None

            self._process_top()
            self._process_models()
            self._process_dt()

            # log model information
            logging.info(self)

        finally:
            # change back the working dir
            os.chdir(working_dir)


    @property
    def fba_model(self):
        if self.fba_models is not None and len(self.fba_models) > 0:
            return self.fba_models[0]
        else:
            return None

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
        s += self.flux_rules_str() + '\n'

        # fba model information
        for fba_model in self.fba_models:
            s += '\n' + fba_model.__str__()
        s += "{}\n".format('-' * 80)

        return s

    def flux_rules_str(self):
        """ Information string of FBA rules.

        :return:
        """
        lines = []
        for key in sorted(self.flux_rules):
            value = self.flux_rules[key]
            lines.append("\t{:>10} <-> {}".format(key, value))
        return '\n'.join(lines)

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

        self.framework_top = builder.get_framework(self.model_top)
        if self.framework_top is not builder.MODEL_FRAMEWORK_ODE:
            warnings.warn("The top level model framework is not ode: {}".format(self.framework_top))

        # get frameworks for submodels
        doc_comp = self.doc_top.getPlugin(builder.SBML_COMP_NAME)
        model_comp = self.model_top.getPlugin(builder.SBML_COMP_NAME)

        # models are processed in the order they are listed in the listOfSubmodels
        for submodel in model_comp.getListOfSubmodels():
            modelRef = submodel.getModelRef()

            # check if ExternalModelDefinition
            emd = doc_comp.getExternalModelDefinition(modelRef)
            if emd:
                framework = builder.get_framework(emd.getReferencedModel())
            else:
                # Lookfor ModelDefinition
                md = doc_comp.getModelDefinition(modelRef)
                if md:
                    framework = builder.get_framework(md)
                else:
                    raise ValueError("No (External)ModelDefinition for modelRef: {}".format(modelRef))

            # store the submodel under the given framework
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
                                 model_top=self.model_top)
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

    def __init__(self, submodel, source, model_top=None):
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
        self.doc = libsbml.readSBMLFromFile(source)
        self.model = self.doc.getModel()
        self.cobra_model = cobra.io.read_sbml_model(source)

        # bounds are mappings from parameters to reactions
        #       parameter_id -> [rid1, rid2, ...]
        self.ub_parameters = defaultdict(list)
        self.lb_parameters = defaultdict(list)
        self.fba2top_bounds = None

        # reaction mapping (top <-> fba)
        self.fba2top_reactions = None
        self.top2flat_reactions = None

        # objective sense
        self._process_objective_direction()

        # bounds
        self.ub_pid2rid = None
        self.lb_pid2rid = None

        # process the top (ode) <-> fba connections (bounds & reaction replacements)
        if model_top is not None:
            self._process_bound_replacements(model_top)
            self._process_fba2top_reactions(model_top)
            self._process_top2flat_reactions(model_top)

    def __str__(self):
        """ Information string. """

        s = "{} {}\n".format(self.submodel, self.source)
        s += "{}\n".format('-' * 80)
        s += "\t{:<22}: {}\n".format('obj. direction', self.objective_direction)
        s += "\t{:<22}: {}\n".format('cobra obj. direction', self.cobra_model.objective.direction)
        s += "\t{:<22}: {}\n".format('fba2top reactions', self.fba2top_reactions)

        # s += "\t{:<22}: {}\n".format('fba2top bounds', self.fba2top_bounds)
        s += "\t{:<22}: {}\n".format('ub_pid2rid', self.ub_pid2rid)
        s += "\t{:<22}: {}\n".format('lb_pid2rid', self.lb_pid2rid)

        s += "\t{:<22}: {}\n".format('top2flat reactions', self.top2flat_reactions)

        return s

    def _process_objective_direction(self):
        """ Read the objective sense from the fba model objective.

        :return:
        """
        logging.debug('* (fba) _process_flux_rules')
        fmodel = self.model.getPlugin("fbc")
        flist = fmodel.getListOfObjectives()
        active_oid = flist.getActiveObjective()
        objective = fmodel.getObjective(active_oid)
        self.objective_direction = objective.getType()

    # def _process_bounds(self):
    #     """  Determine which parameters are upper and lower bounds for reactions.
    #
    #     The dictionaries allow simple lookup of the bound parameters for update.
    #
    #     :return:
    #     :rtype:
    #     """
    #     logging.debug('* (fba) _process_bounds')
    #     for r in self.model.getListOfReactions():
    #         fbc_r = r.getPlugin("fbc")
    #         rid = r.getId()
    #         if fbc_r.isSetUpperFluxBound():
    #             self.ub_parameters[fbc_r.getUpperFluxBound()].append(rid)
    #         if fbc_r.isSetLowerFluxBound():
    #             self.lb_parameters[fbc_r.getLowerFluxBound()].append(rid)

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
        submodel_id = self.submodel.getId()

        # find the bound parameters which are connected to ode model
        top_pid2fba_pid = {}
        for p in top_model.getListOfParameters():
            top_pid = p.getId()
            comp_p = p.getPlugin("comp")

            rep_elements = comp_p.getListOfReplacedElements()
            if rep_elements:
                for rep_element in rep_elements:
                    # the submodel of the replacement belongs to the current fba submodel
                    if rep_element.getSubmodelRef() == submodel_id:
                        element = rep_element.getReferencedElementFrom(self.model)
                        top_pid2fba_pid[top_pid] = element.getId()

        bound_pids = set(top_pid2fba_pid.values())
        # mapping of upper bounds & lower bounds
        ub_pid2rid = {}
        lb_pid2rid = {}
        for r in self.model.getListOfReactions():
            fbc_r = r.getPlugin("fbc")
            rid = r.getId()
            if fbc_r.isSetUpperFluxBound():
                pid = fbc_r.getUpperFluxBound()
                if pid in bound_pids:
                    ub_pid2rid[pid] = rid
            if fbc_r.isSetLowerFluxBound():
                pid = fbc_r.getLowerFluxBound()
                if pid in bound_pids:
                    lb_pid2rid[pid] = rid

        self.ub_pid2rid = ub_pid2rid
        self.lb_pid2rid = lb_pid2rid

    def _process_fba2top_reactions(self, model_top):
        """ Finds mapping between top reactions and fba reactions.

        Necessary for update of top reactions from FBA solution.

        :param model_top: top SBML model 
        :return: None
        """
        # find replacedBy reactions in submodel
        submodel_id = self.submodel.getId()
        fba2top = {}
        for reaction in model_top.getListOfReactions():
            rid_top = reaction.getId()
            r_comp = reaction.getPlugin("comp")

            if r_comp.isSetReplacedBy():
                rep_by = r_comp.getReplacedBy()
                if rep_by.getSubmodelRef() == submodel_id:
                    element = rep_by.getReferencedElementFrom(self.model)
                    fba2top[element.getId()] = rid_top

        self.fba2top_reactions = fba2top

    def _process_top2flat_reactions(self, model_top):
        """ Get the id mapping of the fluxes to the flattened model.

        :param model_top: top SBML model
        :return: None
        """
        submodel_id = self.submodel.getId()

        # find all elements which are replaced (only reactions of interest)
        replaced_in_fba = {}
        for reaction in model_top.getListOfReactions():
            rid_top = reaction.getId()
            r_comp = reaction.getPlugin("comp")

            # check replaced elements
            if r_comp.getNumReplacedElements() > 0:
                for rep_el in r_comp.getListOfReplacedElements():
                    # replaceElement for this submodel
                    if rep_el.getSubmodelRef() == submodel_id:
                        element = rep_el.getReferencedElementFrom(self.model)
                        replaced_in_fba[element.getId()] = rid_top

            # check replacedBy
            if r_comp.isSetReplacedBy():
                rep_by = r_comp.getReplacedBy()
                if rep_by.getSubmodelRef() == submodel_id:
                    element = rep_by.getReferencedElementFrom(self.model)
                    replaced_in_fba[element.getId()] = rid_top

        # create the mapping
        mapping = {}
        for r in self.model.getListOfReactions():
            rid = r.getId()
            if rid in replaced_in_fba:
                mapping[rid] = replaced_in_fba[rid]
            else:
                mapping[rid] = '{}__{}'.format(submodel_id, rid)

        self.top2flat_reactions = mapping
