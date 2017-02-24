"""
Simulator module to simulate SBML models with multiple modeling frameworks.
This currently supports dynamic FBA by coupling ODE models with
FBA based models.

Model composition is encoded by SBML comp with single submodels having a single
simulation framework.
ODE models are simulated with roadrunner, FBA models using cobrapy.
"""
# TODO: Fix the zero time point of the simulation, how to handle this correctly (when are fluxes calculated
#       and when are the updates written (order and timing of updates)

# TODO: handle submodels directly defined in model

from __future__ import print_function, division
import os
import logging
import warnings
import libsbml
import roadrunner
import cobra
import pandas as pd
from pandas import DataFrame
import numpy
import tempfile

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


class Simulator(object):
    """ Simulator class to simulate hybrid models.

    The simulator is initialized with the top level sbml file.
    """

    def __init__(self, sbml_top_path):
        """ Create the simulator with the top level SBML file.

        The models are resolved to their respective simulation framework.
        The top level network must be an ode network.

        Provide absolute path for the top level file.


        :param top_level_path: absolute path of top level SBML file
        :param output_directory: directory where output files are written
        """

        # necessary to change the working directory to the sbml file directory
        # to resolve relative links to external model definitions.
        working_dir = os.getcwd()
        sbml_dir = os.path.dirname(sbml_top_path)
        os.chdir(sbml_dir)

        self.sbml_top = sbml_top_path
        self.sbml_dir = os.path.dirname(sbml_top_path)

        # read top level model
        self.doc_top = None
        self.model_top = None
        self.framework_top = None
        self.submodels = defaultdict(list)
        self.rr_comp = None
        self.fba_models = []

        self._process_top()
        self._process_models()

        # log model information
        logging.info(self)

        # change back the working dir
        os.chdir(working_dir)

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
            elif sbo in [293]:
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
        s += "{} [{}]\n".format(self.model_top, self.framework_top)
        s += "{}\n".format('-' * 80)

        # sub models
        for framework in MODEL_FRAMEWORKS:
            s += "{:<10} : {}\n".format(framework, self.submodels[framework])
        # FBA rules
        s += "{:<10} :\n".format('fba rules', self.fba_rules)
        for key in sorted(self.fba_rules):
            value = self.fba_rules[key]
            s += "{:<12} {} <-> {}\n".format('', key, value)

        # FBA model information
        for fba_model in self.fba_models:
            s += '\n' + fba_model.__str__()
        s += "{}\n".format('-' * 80)

        return s

    def fba_rules_str(self):
        """ Information string of FBA rules.

        :return:
        """
        lines = ['FBA rules:']
        for key, value in self.fba_rules.iteritems():
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
        if self.framework_top is not MODEL_FRAMEWORK_ODE:
            warnings.warn("The top level model framework is not ode: {}".format(self.framework_top))

        # get submodels with frameworks
        top_plugin = self.model_top.getPlugin("comp")
        for submodel in top_plugin.getListOfSubmodels():
            # models are processed in the order they are listed in the listOfSubmodels
            framework = Simulator.get_framework(submodel)
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
        self.fba_rules = Simulator.find_fba_rules(self.model_top)

        ###########################
        # ODE model
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
        # FBA models are found based on the FBA modeling framework
        mdoc = self.doc_top.getPlugin("comp")
        for submodel in self.submodels[MODEL_FRAMEWORK_FBA]:
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

            fba_model = FBAModel(submodel=submodel, source=source, fba_rules=self.fba_rules)
            fba_model.process_replacements(self.model_top)
            fba_model.process_flat_mapping(self.rr_comp)
            self.fba_models.append(fba_model)


    @classmethod
    def find_fba_rules(cls, top_model):
        """ Find FBA rules in top model.

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


    def simulate(self, tstart=0.0, tend=10.0, steps=20):
        """
        Perform model simulation.

        The simulator figures out based on the SBO terms in the list of submodels, which
        simulation/modelling framework to use.
        The passing of information between FBA and SSA/ODE is based on the list of replacements.
        """
        # TODO: store directly in numpy arrays for speed improvements

        logging.debug('###########################')
        logging.debug('# Start Simulation')
        logging.debug('###########################')

        points = steps + 1
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
            logging.debug('* ODE integration')
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
            logging.debug('* Copy fluxes in ODE solution')
            for fba_model in self.fba_models:
                for k, v in fba_model.flat_mapping.iteritems():
                    flux = fba_model.cobra_model.solution.x_dict[k]
                    vindex = df_results.columns.get_loc(v)
                    row[vindex] = flux
            all_results.append(row)

            # store and update time
            kstep += 1
            time += step_size

            from pandas import Series
            logging.debug(Series(row, index=self.rr_comp.timeCourseSelections))

        # create result matrix
        df_results = pd.DataFrame(index=all_time, columns=self.rr_comp.timeCourseSelections,
                                  data=all_results)
        df_results.time = all_time

        logging.debug('###########################')
        logging.debug('# Stop Simulation')
        logging.debug('###########################')

        return df_results

    def plot_species(self, filepath, df, rr_comp):
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
        fig.savefig(filepath)

    def plot_reactions(self, filepath, df, rr_comp):
        """ Create reactions plots.

        :param df: solution pandas DataFrame
        :type df:
        :param filename
        :return:
        :rtype:
        """
        reaction_ids = rr_comp.model.getReactionIds()

        ax_r = df.plot(x='time', y=reaction_ids)
        fig = ax_r.get_figure()
        fig.savefig(filepath)

    def save_csv(self, filepath, df):
        """ Save results to csv. """
        df.to_csv(filepath, sep="\t", index=False)


class FBAModel(object):
    """ FBA model.

    This class provides functionality for the fba submodels.
    Handles setting of FBA bounds & optimization.
    """
    def __init__(self, submodel, source, fba_rules):
        self.source = source
        self.submodel = submodel

        # read model
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
        # s = "{}\n".format('-' * 80)
        s = "{} {}\n".format(self.submodel, self.source)
        # s += "{}\n".format('-' * 80)
        s += "\t{:<20}: {}\n".format('FBA rules', self.fba_rules)
        s += "\t{:<20}: {}\n".format('ub parameters', self.ub_parameters)
        s += "\t{:<20}: {}\n".format('lb parameters', self.lb_parameters)
        s += "\t{:<20}: {}\n".format('ub replacements', self.ub_replacements)
        s += "\t{:<20}: {}\n".format('lb replacements', self.lb_replacements)
        s += "\t{:<20}: {}\n".format('flat mapping', self.flat_mapping)
        # s += "{}\n".format('-' * 80)

        return s

    def process_fba_rules(self, fba_rules):
        """ Returns subset of fba_rules relevant for the FBA model.

        Only fba rules are relevant which if there is a reaction in the fba submodel
        which has the parameter id.

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
        Uses the global parameter replacements to replace the bounds
        of reactions with the current values in the kinetic model.

        :param model:
        :type model:
        :return:
        :rtype:
        """
        logging.debug('* FBA set bounds ')
        for pid in self.ub_replacements:
            for rid in self.ub_parameters.get(pid):
                logging.debug('\t{}: (upper) -> {}'.format(rid, pid))
                cobra_reaction = self.cobra_model.reactions.get_by_id(rid)
                cobra_reaction.upper_bound = rr_comp[pid]

        for pid in self.lb_replacements:
            for rid in self.lb_parameters.get(pid):
                logging.debug('\t{}: (lower) -> {}'.format(rid, pid))
                cobra_reaction = self.cobra_model.reactions.get_by_id(rid)
                cobra_reaction.lower_bound = rr_comp[pid]

    def optimize(self):
        """ Optimize FBA model.

        """
        # TODO: handle maximization & minimization, currently only maximization
        logging.debug("* FBA optimize")
        self.cobra_model.optimize()

        logging.debug('\tstatus: {}'.format(self.cobra_model.solution.status))
        for skey in sorted(self.cobra_model.solution.x_dict):
            flux = self.cobra_model.solution.x_dict[skey]
            logging.debug('\t{:<10}: {}'.format(skey, flux))
            # logging.debug(''.format(self.cobra_model.solution.x_dict))

    def set_ode_fluxes(self, rr_comp):
        """ Set fluxes in ODE part.

        Based on replacements the FBA fluxes are written in the kinetic flattended model.
        :param rr_comp:
        :type rr_comp:
        :return:
        :rtype:
        """
        logging.debug("* ODE set FBA fluxes")
        for rid, pid in self.fba_rules.iteritems():
            flux = self.cobra_model.solution.x_dict[rid]
            rr_comp[pid] = flux
            logging.debug('\t{}: {} = {}'.format(rid, pid, flux))
        else:
            logging.debug('\tNo flux replacements')

    def log_flux_bounds(self):
        """ Prints flux bounds for all reactions. """
        info = []
        for r in self.cobra_model.reactions:
            info.append([r.id, r.lower_bound, r.upper_bound])
        df = DataFrame(info, columns=['id', 'lb', 'ub'])
        pd.set_option('display.max_rows', len(df))
        logging.debug(df)
        pd.reset_option('display.max_rows')

########################################################################################################################
if __name__ == "__main__":
    # Run simulation of the hybrid model
    logging.getLogger().setLevel(logging.INFO)
    from toymodel import toysettings
    import timeit

    # Create simulator instance
    directory = toysettings.out_dir
    simulator = Simulator(sbml_top_path=os.path.join(toysettings.out_dir, toysettings.top_level_file))

    start_time = timeit.default_timer()
    df = simulator.simulate(tstart=0.0, tend=50.0, steps=500)
    elapsed = timeit.default_timer() - start_time
    logging.info("Simulation time: {}".format(elapsed))
    simulator.plot_reactions(filepath=os.path.join(toysettings.out_dir, "reactions.png"),
                             df=df, rr_comp=simulator.rr_comp)
    simulator.plot_species(filepath=os.path.join(toysettings.out_dir, "species.png"),
                                                 df=df, rr_comp=simulator.rr_comp)
    simulator.save_csv(filepath=os.path.join(toysettings.out_dir, "simulation.csv"),
                       df=df)
