"""
Simulator for dynamic flux balance (DFBA) models in SBML.

ODE integration is performed with roadrunner,
FBA optimization via cobrapy.

Usage:
    from sbmlutils.dfba import simulate_dfba
    df, model, simulator = simulate_dfba(sbml_path, tend, dt)
"""

# FIXME: handle submodels directly defined in model
# TODO: setting of initial conditions, parameters and values.
# TODO: FVA, i.e. flux variability analysis with cobrapy
# TODO: store directly in numpy arrays for speed improvements
# TODO: set tolerances for the ode integration


from __future__ import print_function, division, absolute_import
from six import iteritems
import logging
import numpy as np
import pandas as pd
import cobra
import timeit

from sbmlutils.dfba.model import DFBAModel
from sbmlutils import fbc


def simulate_dfba(sbml_path, tstart=0.0, tend=10.0, dt=0.1, pfba=True,
                  abs_tol=1E-6, rel_tol=1E-6, lp_solver='glpk', **kwargs):
    """ Simulates given model with DFBA.

    Utility function which sets up the model object, a simulator and 
    executes the given simulation.

    :return: list of result DataFrame, DFBAModel, DFBASimulator
    """
    start_time = timeit.default_timer()
    # Load model
    dfba_model = DFBAModel(sbml_path=sbml_path)

    # simulation
    dfba_simulator = DFBASimulator(dfba_model, pfba=pfba,
                                   abs_tol=abs_tol, rel_tol=rel_tol, lp_solver=lp_solver)
    dfba_simulator.simulate(tstart=tstart, tend=tend, dt=dt, **kwargs)
    df = dfba_simulator.solution

    sim_time = dfba_simulator.simulation_time
    tot_time = timeit.default_timer()-start_time
    overhead_time = tot_time - sim_time
    print("\n{:<20}: {:4.3f} [s]".format('Simulation time', sim_time))
    print("{:<20}: {:4.3f} [s]".format('Total time', tot_time))
    print("{:<20}: {:4.3f} [s] ({:2.1f} %)\n".format('Overhead time', overhead_time, overhead_time/tot_time*100))
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
        self.fluxes = None  # last LP fluxes dict

        self.simulation_time = None  # duration of last simulation
        # set solver
        self.cobra_model.solver = lp_solver
        self.pfba = pfba

        # Check that the FBA model simulates with given FBA model bounds
        df_fbc = fbc.cobra_reaction_info(self.cobra_model)
        logging.info(df_fbc)

        # FIXME: add the pfba objective once
        # if self.pfba:
        #     cobra.flux_analysis.parsimonious.add_pfba(self.cobra_model)

        # flux replacements in ode model
        parameter2flux = {}
        for fba_rid, top_rid in iteritems(self.fba_model.fba2top_reactions):
            top_pid = self.dfba_model.flux_rules[top_rid]
            parameter2flux[top_pid] = top_rid
        self.parameter2flux = parameter2flux


    @property
    def dt(self):
        """ Time step of simulation.

        :return:
        """
        return self.dfba_model.dt

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

    @property
    def lp_model(self):
        """ Cobra model for the FBA model. """
        return self.fba_model.lp_solver

    def reset(self):
        """ Reset model to initial conditions. """
        self.ode_model.reset()

    def _set_timecourse_selections(self):
        """ Timecourse selections for the ode model."""

        rr = self.ode_model.getModel()
        sel = ['time'] \
            + sorted(["".join(["[", item, "]"]) for item in rr.getFloatingSpeciesIds()]) \
            + sorted(["".join(["[", item, "]"]) for item in rr.getBoundarySpeciesIds()]) \
            + sorted(rr.getReactionIds()) \
            + sorted(rr.getGlobalParameterIds())

        self.ode_model.timeCourseSelections = sel
        self.columns = dict(zip(sel, range(len(sel))))

    def simulate(self, tstart=0.0, tend=10.0, dt=0.1, absTol=1E-6, relTol=1E-6, reset=True):
        """ Perform model simulation.

        The simulator figures out based on the SBO terms in the list of submodels, which
        simulation/modelling framework to use.
        The passing of information between FBA and SSA/ODE is based on the list of replacements.
        """
        start_time = timeit.default_timer()
        # set the columns in output
        self._set_timecourse_selections()

        # reset model to initial state
        if reset:
            self.reset()

        # FIXME: set tolerances on the ode model

        # number of steps
        steps = np.round(1.0 * tend / dt)
        if np.abs(steps * dt - tend) > absTol:
            raise ValueError("Stepsize dt={} not compatible to simulation time tend={}".format(dt, tend))

        # set the dt value
        self.dfba_model.set_dt(dt)

        try:
            logging.debug('###########################')
            logging.debug('# Start Simulation')
            logging.debug('###########################')

            points = steps + 1
            all_time = np.linspace(start=tstart, stop=tend, num=points)
            all_results = []

            # initial values
            ode_res = self._simulate_ode(tstart=0.0, tend=0.0)
            row_next = ode_res[1, :]
            time = 0.0
            kstep = 0
            while kstep < points:
                logging.debug("-" * 80)
                logging.debug("Time: {}".format(time))
                logging.debug("* dt = {}".format(self.dt))
                step_time = timeit.default_timer()

                # --------------------------------------
                # FBA
                # --------------------------------------
                # update fba bounds from ode
                self._set_fba_bounds(row_next)
                # optimize fba
                self._simulate_fba()
                # set ode fluxes from fba
                self._set_fluxes()

                # --------------------------------------
                # ODE
                # --------------------------------------
                ode_res = self._simulate_ode(tstart=time, tend=time + self.dt)
                row = ode_res[0, :]
                row_next = ode_res[1, :]
                self._store_fba_fluxes(row)

                all_results.append(row)

                # update time & step counter
                time += self.dt
                kstep += 1

                logging.debug(pd.Series(row, index=self.ode_model.timeCourseSelections))
                logging.debug("Time for step: {:2.4}".format(timeit.default_timer() - step_time))


            # create result matrix
            df_results = pd.DataFrame(index=all_time, columns=self.ode_model.timeCourseSelections,
                                      data=all_results)
            df_results.time = all_time

            self.simulation_time = timeit.default_timer() - start_time
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
        self.simulation_time = timeit.default_timer() - start_time
        return self.solution

    def benchmark(self, n_repeat=10, **kwargs):
        """ Benchmark the simulate function with provided simulation parameters.
        
        See simulate arguments for available kwargs.
        
        :return: numpy array of times
        """
        dt = kwargs['dt']
        tend = kwargs['tend']
        steps = np.round(1.0*tend/dt)
        timings = np.zeros(shape=(n_repeat, 1))
        for k in range(n_repeat):
            self.reset()
            self.simulate(**kwargs)
            # how long did the simulation take
            print('\t[{}/{}] {:.5f}'.format(k, n_repeat, self.simulation_time))
            timings[k] = self.simulation_time
        print('-' * 40)
        print('N={}, mean+-SD'.format(n_repeat))
        print('\t{:.5f} +- {:.5f} [{} steps]'.format(np.mean(timings), np.std(timings), steps))
        print('\t{:.5f} +- {:.5f} [per step]'.format(np.mean(timings) / steps, np.std(timings) / steps))
        print('-' * 40)
        return timings

    def _store_fba_fluxes(self, row):
        """ Store FBA fluxes in ode solution. 
        :return: 
        """
        for fba_rid, flat_rid in iteritems(self.fba_model.top2flat_reactions):
            index = self.columns[flat_rid]
            row[index] = flux = self.fluxes[fba_rid]
            logging.debug("\t{} = {}".format(fba_rid, flux))

    def _simulate_ode(self, tstart, tend):
        """ ODE integration for a single timestep.

        :param kstep:
        :param step_size:
        :return:
        """
        logging.debug('* ODE integration')
        result = self.ode_model.simulate(start=tstart, end=tend, steps=1)

        # store ode row, i.e. the end of the simulation
        return result

    def _simulate_fba(self):
        """ Optimize FBA model.

        Uses the objective sense from the fba model.
        Runs parsimonious FBA (often written pFBA) which finds a flux distribution
        which gives the optimal growth rate, but minimizes the total sum of flux.
        """
        logging.debug("* FBA optimize")
        # self.fba_solution = self.cobra_model.optimize()
        # # FIXME
        self.fba_solution = cobra.flux_analysis.pfba(self.cobra_model)
        self.fluxes = self.fba_solution.fluxes
        logging.debug(self.fba_solution.fluxes)

        # directly call the optimization
        # self.cobra_model.solver.optimize()
        # self.fluxes = DFBASimulator.get_fluxes_vector(self.cobra_model)
        # logging.debug(self.fluxes)

    @staticmethod
    def get_fluxes_vector(model, reactions=None):
        """
        Generates fast solution representation of the current solver state.

        """
        cobra.core.model.check_solver_status(model.solver.status)
        if reactions is None:
            reactions = model.reactions

        # FIXME: calculate order once and reuse it
        rxn_index = [rxn.id for rxn in reactions]
        var_primals = dict(zip(model.solver._get_variables_names(),
                               model.solver._get_primal_values()))
        fluxes = {}
        for (i, rxn) in enumerate(reactions):
            fluxes[rxn_index[i]] = var_primals[rxn.id] - var_primals[rxn.reverse_id]

        return fluxes

    def _set_fba_bounds(self, row):
        """ Set FBA bounds from kinetic model.

        Uses the global bound replacements to update the bounds of the FBA reactions.
        The parameters are read from the kinetic model.

        :param model:
        :type model:
        :return:
        :rtype:
        """
        logging.debug('* FBA set bounds ')

        # FIXME: unify in one inline function, set upper and lower bounds at once

        # upper bounds
        for top_pid, rid in iteritems(self.fba_model.ub_pid2rid):
            reaction = self.fba_model.cobra_model.reactions.get_by_id(rid)

            # lookup from ode results
            index = self.columns[top_pid]
            ub = row[index]
            # lookup from model
            # ub = self.ode_model[top_pid]

            if abs(ub) <= self.abs_tol:
                ub = 0.0
                logging.info('\tupper: {:<10} = {} set to 0.0'.format(top_pid, ub))
            reaction.upper_bound = ub
            logging.debug('\tupper: {:<10} = {}'.format(top_pid, ub))

        # lower bounds
        for top_pid, rid in iteritems(self.fba_model.lb_pid2rid):
            reaction = self.fba_model.cobra_model.reactions.get_by_id(rid)

            # lookup from ode results
            index = self.columns[top_pid]
            lb = row[index]
            # lookup from model
            # lb = self.ode_model[top_pid]
            if abs(lb) <= self.abs_tol:
                lb = 0.0
                logging.info('\tlower: {:<10} = {} set to 0.0'.format(top_pid, lb))

            reaction.lower_bound = lb
            logging.debug('\tlower: {:<10} = {}'.format(top_pid, lb))


    def _set_fluxes(self):
        """ Set fluxes in ODE part.

        Based on replacements the FBA fluxes are written in the kinetic flattended model.
        :param ode_model:
        :type ode_model:
        :return:
        :rtype:
        """
        logging.debug("* ODE set FBA fluxes")

        for top_pid, fba_rid in iteritems(self.parameter2flux):
            # reaction rates cannot be set directly in roadrunner
            # parameters have to be set manually
            self.ode_model[top_pid] = self.fluxes[fba_rid]
            logging.debug('\t{:<10}: {:<10} = {}'.format(top_pid, fba_rid, self.fluxes[fba_rid]))

