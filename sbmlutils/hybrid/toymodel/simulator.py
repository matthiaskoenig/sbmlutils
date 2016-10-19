"""
Simulator to run the models consisting of multiple
modeling frameworks.

Simulation of the combined toy model consisting of FBA and kinetic submodels.
Using FBA simulator & kinetic simulator to simulate submodels with
synchronization between the partial simulations.
"""
# TODO: Fix the zero time point of the simulation, how to handle this correctly (when are fluxes calculated
#       and when are the updates written (order and timing of updates)

from __future__ import print_function, division
import libsbml
import roadrunner
import cobra
import pandas as pd
from pandas import DataFrame
import numpy
import logging
import warnings
from collections import defaultdict

logging.basicConfig(format='%(message)s', level=logging.DEBUG)

#################################################

MODEL_FRAMEWORK_FBA = 'fba'
MODEL_FRAMEWORK_ODE = 'ode'
MODEL_FRAMEWORK_STOCHASTIC = 'stochastic'
MODEL_FRAMEWORK_LOGICAL = 'logical'

MODEL_FRAMEWORKS = [
    MODEL_FRAMEWORK_FBA,
    MODEL_FRAMEWORK_ODE,
    MODEL_FRAMEWORK_STOCHASTIC,
    MODEL_FRAMEWORK_LOGICAL,
]
#################################################


class FBAModel(object):
    """ Handling FBA submodels models

    """
    # TODO: handle submodels directly defined in model

    def __init__(self, submodel, source, fba_rules):
        self.source = source
        self.submodel = submodel

        # read the model
        self.fba_doc = libsbml.readSBMLFromFile(source)
        self.fba_model = self.fba_doc.getModel()
        self.cobra_model = cobra.io.read_sbml_model(source)

        # parameters to replace in top model
        self.fba_rules = self.process_fba_rules(fba_rules)

        # bounds are mappings from parameters to reactions
        #       parameter_id -> [rid1, rid2, ...]
        self.ub_parameters = defaultdict(list)
        self.lb_parameters = defaultdict(list)
        self.ub_replacements = []
        self.lb_replacements = []
        self.flat_mapping = {}
        self.process_bounds()

    def __str__(self):
        """ Information string. """
        s = "{}\n".format('-' * 80)
        s += "{} {}\n".format(self.submodel, self.source)
        s += "{}\n".format('-' * 80)
        s += "{:<20}: {}\n".format('FBA rules', self.fba_rules)
        s += "{:<20}: {}\n".format('ub parameters', self.ub_parameters)
        s += "{:<20}: {}\n".format('lb parameters', self.lb_parameters)
        s += "{:<20}: {}\n".format('ub replacements', self.ub_replacements)
        s += "{:<20}: {}\n".format('lb replacements', self.lb_replacements)
        s += "{:<20}: {}\n".format('flat mapping', self.flat_mapping)
        s += "{}\n".format('-' * 80)

        return s

    def process_fba_rules(self, fba_rules):
        """ Returns subset of fba_rules relevant for the FBA model.

        :param fba_rules:
        :type fba_rules:
        :return:
        :rtype:
        """
        rules = {}
        for rid, pid in fba_rules.iteritems():
            if self.fba_model.getReaction(rid) is not None:
                rules[rid] = pid
        return rules

    def process_bounds(self):
        """  Determine which parameters are upper or lower bounds.
        :return:
        :rtype:
        """
        for r in self.fba_model.getListOfReactions():
            mr = r.getPlugin("fbc")
            rid = r.getId()
            if mr.isSetUpperFluxBound():
                self.ub_parameters[mr.getUpperFluxBound()].append(rid)
            if mr.isSetLowerFluxBound():
                self.lb_parameters[mr.getLowerFluxBound()].append(rid)

    def process_replacements(self, top_model):
        """ Process the global replacements once. """
        for p in top_model.getListOfParameters():
            pid = p.getId()
            mp = p.getPlugin("comp")
            for rep_element in mp.getListOfReplacedElements():
                # the submodel of the replacement belongs to the current model
                if rep_element.getSubmodelRef() == self.submodel.getId():
                    # and parameter is part of the bounds
                    if pid in self.ub_parameters:
                        self.ub_replacements.append(pid)
                    if pid in self.lb_parameters:
                        self.lb_replacements.append(pid)

    def process_flat_mapping(self, rr_comp):
        """ Get the id mapping of the fluxes to the
        flattend model.

        :param top_model:
        :type top_model:
        :return:
        :rtype:
        """
        smid = self.submodel.getId()
        map = {}

        fba_rids = set()
        for rid in rr_comp.model.getReactionIds():
            if rid.startswith('{}__'.format(smid)):
                fba_rids.add(rid)

        for r in self.fba_model.getListOfReactions():
            rid = r.getId()
            if '{}__{}'.format(smid, rid) in fba_rids:
                map[rid] = '{}__{}'.format(smid, rid)
            else:
                map[rid] = rid

        self.flat_mapping = map

    def update_fba_bounds(self, rr_comp):
        """
        Uses the global parameter replacements for replacements which replace the bounds
        of reactions.

        :param model:
        :type model:
        :return:
        :rtype:
        """
        logging.debug('* update_fba_bounds *')
        for pid in self.ub_replacements:
            for rid in self.ub_parameters.get(pid):
                logging.debug('{}: (upper) -> {}'.format(rid, pid))
                cobra_reaction = self.cobra_model.reactions.get_by_id(rid)
                cobra_reaction.upper_bound = rr_comp[pid]

        for pid in self.lb_replacements:
            for rid in self.lb_parameters.get(pid):
                logging.debug('{}: (lower) -> {}'.format(rid, pid))
                cobra_reaction = self.cobra_model.reactions.get_by_id(rid)
                cobra_reaction.lower_bound = rr_comp[pid]

    def optimize(self):
        """ Optimize the model """
        # TODO: start with last solution (speed improvement)
        logging.debug("* optimize *")
        self.cobra_model.optimize()

        logging.debug('Solution status: {}'.format(self.cobra_model.solution.status))
        logging.debug('Solution fluxes: {}'.format(self.cobra_model.solution.x_dict))

    def set_ode_fluxes(self, rr_comp):
        """ Set fluxes in ODE part.

        Based on replacements the fluxes are written in the kinetic part
        :param rr_comp:
        :type rr_comp:
        :return:
        :rtype:
        """
        logging.debug("* set_ode_fluxes *")
        for rid, pid in self.fba_rules.iteritems():
            flux = self.cobra_model.solution.x_dict[rid]
            rr_comp[pid] = flux
            logging.debug('{}: {} = {}'.format(rid, pid, flux))

    def log_flux_bounds(self):
        """ Prints flux bounds for all reactions. """
        info = []
        for r in self.cobra_model.reactions:
            info.append([r.id, r.lower_bound, r.upper_bound])
        df = DataFrame(info, columns=['id', 'lb', 'ub'])
        pd.set_option('display.max_rows', len(df))
        logging.debug(df)
        pd.reset_option('display.max_rows')


class Simulator(object):
    """ Simulator class to simulate hybrid models.

    The simulator is initialized with the top level sbml file.
    """

    def __init__(self, top_level_file):
        """ Create the simulator with the top level SBML file.

        The models are resolved to their respective simulation framework.
        The top level network must be an ode network.
        """
        self.sbml_top = top_level_file
        # read top level model
        self.doc_top = libsbml.readSBMLFromFile(self.sbml_top)
        self.model_top = self.doc_top.getModel()
        self.framework_top = self.get_framework(self.model_top)
        if self.framework_top is not MODEL_FRAMEWORK_ODE:
            warnings.warn("The top level model framework is not ode: {}".format(self.framework_top))

        self.submodels = defaultdict(list)
        self.rr_comp = None
        self.fba_models = []

        self._process_top_level()
        self._prepare_models()

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
            sbo = model.getSBOTerm()
            if sbo == 624:
                framework = MODEL_FRAMEWORK_FBA
            elif sbo == 62:
                framework = MODEL_FRAMEWORK_ODE
            elif sbo == 63:
                framework = MODEL_FRAMEWORK_STOCHASTIC
            elif sbo in [234, 547]:
                framework = MODEL_FRAMEWORK_LOGICAL
            else:
                warnings.warn("Modelling Framework not supported: {}".format(sbo))
        return framework

    def __str__(self):
        """ Information string. """
        # top level
        s = "{}\n".format('-' * 80)
        s += "{} {}\n".format(self.doc_top, self.framework_top)
        s += "{}\n".format('-' * 80)

        # sub models
        for framework in MODEL_FRAMEWORKS:
            s += "{:<10} : {}\n".format(framework, self.submodels[framework])
        s += "{}\n".format('-' * 80)

        return s

    def _process_top_level(self):
        """ Process the top level information.

        Reads all the submodels, creates the global data structure.
        Order for executtion

        :return:
        """
        # get list of submodels
        model = self.doc_top.getModel()
        if model is None:
            warnings.warn("No top level model found.")

        # Get submodel frameworks & store in respective list
        top_plugin = self.model_top.getPlugin("comp")
        for submodel in top_plugin.getListOfSubmodels():
            # models are processed in the order they are listed in the listOfSubmodels
            framework = Simulator.get_framework(submodel)
            self.submodels[framework].append(submodel)

        print(self)

    def _prepare_models(self):
        """ Prepare the models for simulation.

        Resolves the replacements and model couplings between the
        different frameworks and creates the respective simulatable
        models for the different frameworks.

        :return:
        :rtype:
        """
        logging.debug('_prepare_models')
        ###########################
        # find FBA rules
        ###########################
        # process FBA assignment rules of the top model
        self.fba_rules = self.find_fba_rules(self.model_top)
        logging.debug('FBA rules:', self.fba_rules)

        ###########################
        # prepare ODE model
        ###########################
        # the roadrunner ode file is the flattend comp file.
        # FBA subparts do not change change any of the kinetic subparts (only connections via replaced bounds
        # and fluxes).
        # Consequently the ode part can be solved as is, only the iterative update between ode and fba has
        # to be performed

        # remove FBA assignment rules from the model, so they can be set via the simulator
        # not allowed to set assignment rules directly in roadrunner
        for variable in self.fba_rules.values():
            self.model_top.removeRuleByVariable(variable)

        import tempfile
        mixed_sbml_cleaned = tempfile.NamedTemporaryFile("w", suffix=".xml")
        libsbml.writeSBMLToFile(self.doc_top, mixed_sbml_cleaned.name)

        rr_comp = roadrunner.RoadRunner(mixed_sbml_cleaned.name)

        sel = ['time'] \
              + sorted(["".join(["[", item, "]"]) for item in rr_comp.model.getFloatingSpeciesIds()]) \
              + sorted(["".join(["[", item, "]"]) for item in rr_comp.model.getBoundarySpeciesIds()]) \
              + sorted(rr_comp.model.getReactionIds()) \
              + sorted(rr_comp.model.getGlobalParameterIds())
              # + self.fba_rules.values()
        rr_comp.timeCourseSelections = sel
        rr_comp.reset()
        self.rr_comp = rr_comp

        ###########################
        # prepare FBA models
        ###########################
        mdoc = self.doc_top.getPlugin("comp")
        for submodel in self.submodels[MODEL_FRAMEWORK_FBA]:
            mref = submodel.getModelRef()
            emd = mdoc.getExternalModelDefinition(mref)
            source = emd.getSource()
            fba_model = FBAModel(submodel=submodel, source=source, fba_rules=self.fba_rules)
            fba_model.process_replacements(self.model_top)
            fba_model.process_flat_mapping(self.rr_comp)
            self.fba_models.append(fba_model)

            print(fba_model)


    def find_fba_rules(self, top_model):
        """ Finds FBA rules in top model.

        Find the assignment rules which assign a reaction rate to a parameter.
        This are the assignment rules synchronizing between FBA and ODE models.

        These are Assignment rules of the form
            pid = rid
        i.e. a reaction rate is assigned to a parameter.
        """
        fba_rules = {}

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
            fba_rules[reaction.getId()] = parameter.getId()
        return fba_rules

    def simulate(self, tstart=0.0, tend=10.0, points=51):
        """
        Performs model simulation.

        The simulator figures out based on the SBO terms in the list of submodels, which
        simulation/modelling framework to use.
        The passing of information between FBA and SSA/ODE is based on the list of replacements.
        """
        # TODO: store directly in numpy arrays for speed improvements

        logging.debug('###########################')
        logging.debug('# Simulation')
        logging.debug('###########################')

        all_time = numpy.linspace(start=tstart, stop=tend, num=points)
        all_results = []
        df_results = pd.DataFrame(index=all_time, columns=self.rr_comp.timeCourseSelections)

        step_size = (tend-tstart)/(points-1.0)
        result = None
        time = 0.0

        # variable step size integration
        # if not points:
        #     self.rr_comp.integrator.setValue('variable_step_size', True)

        kstep = 0
        while kstep < points:
            logging.debug("-" * 80)
            logging.debug("Time: {}".format(time))

            # --------------------------------------
            # FBA
            # --------------------------------------
            for fba_model in self.fba_models:
                # update fba bounds from ode
                fba_model.update_fba_bounds(self.rr_comp)
                # optimize fba
                fba_model.optimize()
                # set ode fluxes from fba
                fba_model.set_ode_fluxes(self.rr_comp)

            # --------------------------------------
            # ODE
            # --------------------------------------
            if points:
                # constant step size
                if kstep == 0:
                    result = self.rr_comp.simulate(start=0, end=0, steps=1)
                else:
                    result = self.rr_comp.simulate(start=0, end=step_size, steps=1)
            # else:
                # variable step size
                # result = self.rr_comp.simulate(start=0, steps=1)

            # store ode row
            row = result[1, :]

            # store fba fluxes
            for fba_model in self.fba_models:
                for k, v in fba_model.flat_mapping.iteritems():
                    flux = fba_model.cobra_model.solution.x_dict[k]
                    vindex = df_results.columns.get_loc(v)
                    row[vindex] = flux

            all_results.append(row)

            # store and update time
            kstep += 1

            logging.debug(result)

        # create result matrix
        df_results = pd.DataFrame(index=all_time, columns=self.rr_comp.timeCourseSelections,
                                  data=all_results)
        df_results.time = all_time
        return df_results

    def plot_species(self, df, rr_comp, path="species.png"):
        """ Plot species.

        :param df:
        :type df:
        :return:
        :rtype:
        """
        species_ids = ["[{}]".format(s) for s in rr_comp.model.getFloatingSpeciesIds()] \
                    + ["[{}]".format(s) for s in rr_comp.model.getBoundarySpeciesIds()]

        ax_s = df.plot(x='time', y=species_ids)
        fig = ax_s.get_figure()
        fig.savefig(path)

    def plot_reactions(self, df, rr_comp, path="reactions.png"):
        """ Plot reactions.

        :param df:
        :type df:
        :return:
        :rtype:
        """
        reaction_ids = rr_comp.model.getReactionIds()
        print(reaction_ids)

        ax_r = df.plot(x='time', y=reaction_ids)
        fig = ax_r.get_figure()
        fig.savefig(path)

    def save_csv(self, df, path="simulation.csv"):
        """ Save results to csv. """
        df.to_csv(path, sep="\t", index=False)


########################################################################################################################
if __name__ == "__main__":
    # Run simulation of the hybrid model
    logging.getLogger().setLevel(logging.INFO)
    from simsettings import top_level_file, out_dir
    import os
    os.chdir(out_dir)
    import timeit

    # Create simulator instance
    simulator = Simulator(top_level_file=top_level_file)

    start_time = timeit.default_timer()
    df = simulator.simulate(tstart=0.0, tend=50.0, points=501)
    elapsed = timeit.default_timer() - start_time
    logging.info("Simulation time: {}".format(elapsed))
    simulator.plot_reactions(df, rr_comp=simulator.rr_comp)
    simulator.plot_species(df, rr_comp=simulator.rr_comp)
    simulator.save_csv(df)

    # print(df)
