"""
Simulator for dynamic flux balance (DFBA) models in SBML.

ODE integration is performed with roadrunner,
FBA optimization via cobrapy.

Usage:
    from sbmlutils.dfba import simulate_dfba
    df, model, simulator = simulate_dfba(sbml_path, tend, dt)
"""
# FIXME: handle submodels directly defined in model
# FIXME: reset of kinetic model
# TODO: FVA, i.e. flux variability analysis with cobrapy
# TODO: store directly in numpy arrays for speed improvements
# TODO: set tolerances for the ode integration
# FIXME: easy handling of different stepsizes

# logging.basicConfig(format='%(message)s', level=logging.DEBUG)

from __future__ import print_function, division
from six import iteritems
import logging
import numpy as np
import pandas as pd
import cobra
import timeit

from sbmlutils.dfba.model import DFBAModel
from sbmlutils import fbc


def simulate_dfba(sbml_path, tstart=0.0, tend=10.0, dt=0.1, pfba=True, **kwargs):
    """ Simulates given model with DFBA.


    :return: list of result dataframe, DFBAModel, DFBASimulator
    """
    # Load model
    dfba_model = DFBAModel(sbml_path=sbml_path)

    # simulation
    dfba_simulator = DFBASimulator(dfba_model, pfba=pfba)
    dfba_simulator.simulate(tstart=tstart, tend=tend, dt=dt, **kwargs)
    df = dfba_simulator.solution

    print("\nSimulation time: {}\n".format(dfba_simulator.time))
    return df, dfba_model, dfba_simulator


class DFBASimulator(object):
    """ Simulator class to dynamic flux balance models (DFBA). """

    def __init__(self, dfba_model, abs_tol=1E-6, rel_tol=1E-6, lp_solver='glpk', pfba=True):
        """ Create the simulator with the processed dfba model.


        :param dfba_model: DFBAModel
        :param abs_tol: absolute tolerance of integration
        :param rel_tol: relative tolerance of integration
        :param lp_solver: solver to use for the lp problem (glpk, cplex, gurobi)
        :param pfba: perform minimal flux simulation
        """
        self.dfba_model = dfba_model
        self.abs_tol = abs_tol
        self.rel_tol = rel_tol
        self.solution = None
        self.fba_solution = None  # last LP solution
        self.time = None
        # set solver
        self.cobra_model.solver = lp_solver
        self.pfba = pfba

    @property
    def dt(self):
        """ Time step of simulation.

        :return:
        """
        return self.dfba_model.dt

    @property
    def objective_sense(self):
        return self.dfba_model.fba_model.objective_sense

    @property
    def ode_model(self):
        return self.dfba_model.rr_comp

    @property
    def fba_model(self):
        return self.dfba_model.fba_model

    @property
    def cobra_model(self):
        """ Cobra model for the FBA model. """
        return self.fba_model.cobra_model

    def simulate(self, tstart=0.0, tend=10.0, dt=0.1, absTol=1E-6, relTol=1E-6, reset=True):
        """ Perform model simulation.

        The simulator figures out based on the SBO terms in the list of submodels, which
        simulation/modelling framework to use.
        The passing of information between FBA and SSA/ODE is based on the list of replacements.
        """
        # set the columns in output
        self._set_timecourse_selections()

        # reset model to initial state
        if reset:
            self.ode_model.reset()

        # number of steps
        steps = np.round(1.0 * tend / dt)
        if np.abs(steps * dt - tend) > absTol:
            raise ValueError("Stepsize dt={} not compatible to simulation time tend={}".format(dt, tend))

        # set the dt value
        self.dfba_model.set_dt(dt)

        # Check that the FBA model simulates with given FBA model bounds
        df_fbc = fbc.cobra_reaction_info(self.cobra_model)
        logging.info(df_fbc)
        self.cobra_model.optimize(objective_sense=self.objective_sense)
        # self.cobra_model.summary()

        try:
            logging.debug('###########################')
            logging.debug('# Start Simulation')
            logging.debug('###########################')
            start_time = timeit.default_timer()

            points = steps + 1
            all_time = np.linspace(start=tstart, stop=tend, num=points)
            all_results = []
            df_results = pd.DataFrame(index=all_time, columns=self.ode_model.timeCourseSelections)

            time = 0.0
            kstep = 0
            while kstep < points:
                logging.debug("-" * 80)
                logging.debug("Time: {}".format(time))
                logging.debug("* dt = {}".format(self.dt))

                # --------------------------------------
                # FBA
                # --------------------------------------
                # update fba bounds from ode
                self._set_fba_bounds()
                # optimize fba
                self._optimize_fba(pfba=self.pfba)
                # set ode fluxes from fba
                self._set_fluxes()

                # --------------------------------------
                # ODE
                # --------------------------------------
                if kstep == 0:
                    # initial values
                    row = self._ode_simulation(tstart=0.0, tend=0.0)
                else:
                    row = self._ode_simulation(tstart=time, tend=time+self.dt)

                    # set fba fluxes in results

                logging.debug('* Store fluxes in ODE solution')
                # from pprint import pprint
                # pprint(self.fba_model.flat_mapping)
                for fba_rid, flat_rid in iteritems(self.fba_model.flat_mapping):
                    flux = self.fba_solution.fluxes[fba_rid]
                    vindex = df_results.columns.get_loc(flat_rid)
                    row[vindex] = flux
                    logging.debug("\t{} = {}".format(fba_rid, flux))
                # FIXME: what about dummy_EX_A ? values


                all_results.append(row)

                # update time & step counter
                time += self.dt
                kstep += 1

                logging.debug(pd.Series(row, index=self.ode_model.timeCourseSelections))

            # create result matrix
            df_results = pd.DataFrame(index=all_time, columns=self.ode_model.timeCourseSelections,
                                      data=all_results)
            df_results.time = all_time

            self.time = timeit.default_timer() - start_time
            logging.debug('###########################')
            logging.debug('# Stop Simulation')
            logging.debug('###########################')

        except RuntimeError as e:
            import traceback
            traceback.print_exc()
            # return the partial result until the error
            df_results = pd.DataFrame(columns=self.ode_model.timeCourseSelections,
                                      data=all_results)
            df_results.time = all_time[:len(all_results)]

        self.solution = df_results
        return self.solution

    def benchmark(self, Nrepeat=10, **kwargs):
        """ Benchmark the simulate function with given settings.

        :param self:
        :param tstart:
        :param tend:
        :param steps:
        :param absTol:
        :return:
        """
        dt = kwargs['dt']
        tend = kwargs['tend']
        steps = np.round(1.0*tend/dt)
        timings = np.zeros(shape=(10, 1))
        for k in range(Nrepeat):
            self.simulate(**kwargs)
            # how long did the simulation take
            print('\t[{}/{}] {:.5f}'.format(k, Nrepeat, self.time))
            timings[k] = self.time
        print('-' * 40)
        print('N={}, mean +- SD'.format(Nrepeat))
        print('{:.3f} +- {:.3f} ({} steps)'.format(np.mean(timings), np.std(timings), steps))
        print('{:.5f} +- {:.5f} (per step)'.format(np.mean(timings) / steps, np.std(timings) / steps))
        print('-' * 40)

    def _set_fba_bounds(self):
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

        for fba_pid in sorted(self.fba_model.fba2top_bounds):
            top_pid = self.fba_model.fba2top_bounds[fba_pid]

            # upper bounds
            if fba_pid in self.fba_model.ub_parameters:
                for rid in self.fba_model.ub_parameters.get(fba_pid):
                    cobra_reaction = self.fba_model.cobra_model.reactions.get_by_id(rid)
                    ub = self.ode_model[top_pid]
                    if abs(ub) <= self.abs_tol:
                        logging.info('\tupper: {:<10} = {} set to 0.0'.format(fba_pid, ub))
                        ub = 0.0
                    cobra_reaction.upper_bound = ub
                    logging.debug('\tupper: {:<10} = {}'.format(fba_pid, ub))
                    counter += 1

            # lower bounds
            if fba_pid in self.fba_model.lb_parameters:
                for rid in self.fba_model.lb_parameters.get(fba_pid):
                    cobra_reaction = self.fba_model.cobra_model.reactions.get_by_id(rid)
                    lb = self.ode_model[top_pid]
                    if abs(lb) <= self.abs_tol:
                        logging.info('\tlower: {:<10} = {} set to 0.0'.format(fba_pid, lb))
                        lb = 0.0
                    cobra_reaction.lower_bound = lb
                    logging.debug('\tlower: {:<10} = {}'.format(fba_pid, lb))
                    counter += 1

        if counter == 0:
            logging.debug('\tNo flux bounds set')

    def _optimize_fba(self, pfba=True):
        """ Optimize FBA model.

        Uses the objective sense from the fba model.
        Runs parsimonious FBA (often written pFBA) which finds a flux distribution
        which gives the optimal growth rate, but minimizes the total sum of flux.
        """

        logging.debug("* FBA optimize")
        self.fba_solution = self.cobra_model.optimize(objective_sense=self.objective_sense)
        if pfba:
            logging.debug("running parsimonious FBA")
            self.fba_solution = cobra.flux_analysis.pfba(self.cobra_model)

        logging.debug(self.fba_solution.fluxes)

    def _set_fluxes(self):
        """ Set fluxes in ODE part.

        Based on replacements the FBA fluxes are written in the kinetic flattended model.
        :param ode_model:
        :type ode_model:
        :return:
        :rtype:
        """
        logging.debug("* ODE set FBA fluxes")
        counter = 0

        for fba_rid in sorted(self.fba_model.fba2top_reactions):
            top_rid = self.fba_model.fba2top_reactions[fba_rid]
            flux = self.fba_solution.fluxes[fba_rid]

            # reaction rates cannot be set directly in roadrunner
            # necessary to get the parameter from the flux rules
            # rr_comp[top_rid] = flux

            top_pid = self.fba_model.flux_rules[top_rid]
            self.ode_model[top_pid] = flux

            logging.debug('\t{:<10}: {:<10} = {}'.format(top_rid, fba_rid, flux))
            counter += 1

        if counter == 0:
            logging.debug('\tNo flux replacements')

    def _ode_simulation(self, tstart, tend):
        """ ODE integration for a single timestep.

        :param kstep:
        :param step_size:
        :return:
        """
        logging.debug('* ODE integration')
        result = self.ode_model.simulate(start=tstart, end=tend, steps=1)

        # store ode row, i.e. the end of the simulation
        return result[1, :]

    def _set_timecourse_selections(self):
        """ Timecourse selections for the ode model."""

        rr = self.ode_model.getModel()
        sel = ['time'] \
            + sorted(["".join(["[", item, "]"]) for item in rr.getFloatingSpeciesIds()]) \
            + sorted(["".join(["[", item, "]"]) for item in rr.getBoundarySpeciesIds()]) \
            + sorted(rr.getReactionIds()) \
            + sorted(rr.getGlobalParameterIds())

        self.ode_model.timeCourseSelections = sel