"""
Simulator to simulate SBML models with multiple modeling frameworks.
The simulator supports the execution of dynamic flux balance (DFBA)
models.

The ode integration is performed with roadrunner,
the FBA using cobrapy.
"""

# FIXME: handle submodels directly defined in model
# FIXME: reset of kinetic model

from __future__ import print_function, division

import os
import warnings
import logging
import tempfile
import numpy as np
import pandas as pd

import libsbml
import roadrunner
import cobra

from collections import defaultdict

#################################################
# Logging
#################################################
logging.basicConfig(format='%(message)s', level=logging.DEBUG)

#################################################
# Simulator constants
#################################################
DT_ID = 'dt'

MODEL_FRAMEWORK_FBA = 'fba'
MODEL_FRAMEWORK_ODE = 'ode'
# MODEL_FRAMEWORK_STOCHASTIC = 'stochastic'
# MODEL_FRAMEWORK_LOGICAL = 'logical'

MODEL_FRAMEWORKS = [
    MODEL_FRAMEWORK_FBA,
    MODEL_FRAMEWORK_ODE,
    # MODEL_FRAMEWORK_STOCHASTIC,
    # MODEL_FRAMEWORK_LOGICAL,
]
#################################################


class SimulatorDFBA(object):
    """ Simulator class to dynamic flux balance models (DFBA). """

    def __init__(self, sbml_top_path):
        """ Create the simulator with the top level SBML file.

        The models are resolved to their respective simulation framework.
        The top level network must be an ode network.

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
            # elif sbo == 63:
            #    framework = MODEL_FRAMEWORK_STOCHASTIC
            # elif sbo in [234, 547]:
            #     framework = MODEL_FRAMEWORK_LOGICAL
            else:
                warnings.warn("Modelling Framework not supported: {}".format(sbo))
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
        for framework in MODEL_FRAMEWORKS:
            s += "{:<10} : {}\n".format(framework, self.submodels[framework])

        # dt
        s += "{:<10} : {}\n".format(DT_ID, self.dt)
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
        for key, value in self.flux_rules.iteritems():
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
            framework = SimulatorDFBA.get_framework(submodel)
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
        self.flux_rules = SimulatorDFBA._process_flux_rules(self.model_top)

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
        par = self.model_top.getParameter(DT_ID)
        if par is None:
            warnings.warn("No parameter with id '{}' in top model.".format(DT_ID))
        self.dt = par.getValue()


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


    def simulate(self, tstart=0.0, tend=10.0, steps=20, absTol=1E-6, relTol=1E-6):
        """
        Perform model simulation.

        The simulator figures out based on the SBO terms in the list of submodels, which
        simulation/modelling framework to use.
        The passing of information between FBA and SSA/ODE is based on the list of replacements.
        """
        # TODO: store directly in numpy arrays for speed improvements
        # TODO: set tolerances for the ode integration

        try:
            logging.debug('###########################')
            logging.debug('# Start Simulation')
            logging.debug('###########################')

            points = steps + 1
            all_time = np.linspace(start=tstart, stop=tend, num=points)
            all_results = []
            df_results = pd.DataFrame(index=all_time, columns=self.rr_comp.timeCourseSelections)

            step_size = (tend-tstart)/(points-1.0)
            if abs(step_size-self.dt)>1E-6:
                raise ValueError("Simulation timestep <{}> != dt <{}>".format(step_size, self.dt))

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
                    fba_model.set_bounds(self.rr_comp)
                    # optimize fba
                    fba_model.optimize()
                    # set ode fluxes from fba
                    fba_model.set_fluxes(self.rr_comp)

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
                logging.debug("\tsuccessful")

                # store fba fluxes
                logging.debug('* Copy fluxes in ODE solution')
                # FIXME: better copy
                for fba_model in self.fba_models:
                    for k, v in fba_model.flat_mapping.iteritems():
                        flux = fba_model.cobra_model.solution.x_dict[k]
                        vindex = df_results.columns.get_loc(v)
                        row[vindex] = flux
                        logging.debug("\t{} = {}".format(k, flux))
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

        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            # return the partial result until the error
            df_results = pd.DataFrame(columns=self.rr_comp.timeCourseSelections,
                                      data=all_results)
            df_results.time = all_time[:len(all_results)]

        return df_results



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
        """ Get the id mapping of the fluxes to the
        flattened model.

        :param top_model:
        :type top_model:
        :return:
        :rtype:
        """
        smid = self.submodel.getId()
        map = {}

        fba_rids = set()
        for rid in rr_comp.model.getReactionIds():
            # mapping relies on submodel prefix !
            if rid.startswith('{}__'.format(smid)):
                fba_rids.add(rid)

        for r in self.sbml_model.getListOfReactions():
            rid = r.getId()
            if '{}__{}'.format(smid, rid) in fba_rids:
                map[rid] = '{}__{}'.format(smid, rid)
            else:
                map[rid] = rid

        self.flat_mapping = map

    def set_bounds(self, rr_comp, absTol=1E-8):
        """ Set FBA bounds from kinetic model.

        Uses the global bound replacements to update the bounds of the FBA reactions.
        The parameters are read from the kinetic model.

        :param model:
        :type model:
        :return:
        :rtype:
        """
        logging.debug('* FBA set bounds ')
        counter = 0

        for fba_pid in sorted(self.fba2top_bounds):
            top_pid = self.fba2top_bounds[fba_pid]

            # upper bounds
            if fba_pid in self.ub_parameters:
                for rid in self.ub_parameters.get(fba_pid):
                    cobra_reaction = self.cobra_model.reactions.get_by_id(rid)
                    ub = rr_comp[top_pid]
                    # if abs(ub) <= absTol:
                    #    ub = 0.0
                    cobra_reaction.upper_bound = ub
                    logging.debug('\tupper: {:<10} = {}'.format(fba_pid, ub))
                    counter += 1

            # lower bounds
            if fba_pid in self.lb_parameters:
                for rid in self.lb_parameters.get(fba_pid):
                    cobra_reaction = self.cobra_model.reactions.get_by_id(rid)
                    lb = rr_comp[top_pid]
                    # if abs(lb) <= absTol:
                    #    lb = 0.0
                    cobra_reaction.lower_bound = lb
                    logging.debug('\tlower: {:<10} = {}'.format(fba_pid, lb))
                    counter += 1

        if counter == 0:
            logging.debug('\tNo flux bounds set')


    def set_fluxes(self, rr_comp):
        """ Set fluxes in ODE part.

        Based on replacements the FBA fluxes are written in the kinetic flattended model.
        :param rr_comp:
        :type rr_comp:
        :return:
        :rtype:
        """
        logging.debug("* ODE set FBA fluxes")
        counter = 0

        for fba_rid in sorted(self.fba2top_reactions):
            top_rid = self.fba2top_reactions[fba_rid]
            flux = self.cobra_model.solution.x_dict[fba_rid]

            # reaction rates cannot be set directly in roadrunner
            # necessary to get the parameter from the flux rules
            # rr_comp[top_rid] = flux

            top_pid = self.flux_rules[top_rid]
            rr_comp[top_pid] = flux

            logging.debug('\t{:<10}: {:<10} = {}'.format(top_rid, fba_rid, flux))
            counter += 1

        if counter == 0:
            logging.debug('\tNo flux replacements')


    def optimize(self):
        """ Optimize FBA model.
        """
        logging.debug("* FBA optimize")
        self.cobra_model.optimize(objective_sense=self.objective_sense)

        logging.debug('\tstatus: <{}>'.format(self.cobra_model.solution.status))
        for skey in sorted(self.cobra_model.solution.x_dict):
            flux = self.cobra_model.solution.x_dict[skey]
            logging.debug('\t{:<10}: {}'.format(skey, flux))




########################################################################################################################
if __name__ == "__main__":
    # Run simulation of the hybrid model
    logging.getLogger().setLevel(logging.INFO)
    from toymodel import toysettings
    import timeit

    # Create simulator instance
    directory = toysettings.out_dir
    simulator = SimulatorDFBA(sbml_top_path=os.path.join(toysettings.out_dir, toysettings.top_level_file))

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
