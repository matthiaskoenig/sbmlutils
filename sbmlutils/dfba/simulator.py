"""
Simulator for dynamic flux balance (DFBA) models in SBML.

The ode integration is performed with roadrunner, the FBA optimization via cobrapy.
"""

# FIXME: handle submodels directly defined in model
# FIXME: reset of kinetic model
# TODO: FVA, i.e. flux variability analysis with cobrapy
# TODO: store directly in numpy arrays for speed improvements
# TODO: set tolerances for the ode integration
# FIXME: easy handling of different stepsizes

from __future__ import print_function, division
import logging
import numpy as np
import pandas as pd

logging.basicConfig(format='%(message)s', level=logging.DEBUG)


class DFBASimulator(object):
    """ Simulator class to dynamic flux balance models (DFBA). """

    def __init__(self, dfba_model, abs_tol=1E-6, rel_tol=1E-6):
        """ Create the simulator with the processed dfba model.


        :param dfba_model: DFBAModel
        :param abs_tol: absolute tolerance of integration
        :param rel_tol: relative tolerance of integration
        """
        self.dfba_model = dfba_model
        self.abs_tol = abs_tol
        self.rel_tol = rel_tol
        self.solution = None

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


    def simulate(self, tstart=0.0, tend=10.0, steps=20, absTol=1E-6, relTol=1E-6):
        """ Perform model simulation.

        The simulator figures out based on the SBO terms in the list of submodels, which
        simulation/modelling framework to use.
        The passing of information between FBA and SSA/ODE is based on the list of replacements.
        """
        try:
            logging.debug('###########################')
            logging.debug('# Start Simulation')
            logging.debug('###########################')

            points = steps + 1
            all_time = np.linspace(start=tstart, stop=tend, num=points)
            all_results = []
            df_results = pd.DataFrame(index=all_time, columns=self.ode_model.timeCourseSelections)

            # check step size
            step_size = (tend-tstart)/(points-1.0)
            if abs(step_size-self.dt) > absTol:
                raise ValueError("Simulation timestep <{}> != dt <{}>".format(step_size, self.dt))

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
                self.set_fba_bounds()
                # optimize fba
                self.optimize_fba()
                # set ode fluxes from fba
                self.set_fluxes()

                # --------------------------------------
                # ODE
                # --------------------------------------
                row = self.ode_simulation(kstep, step_size=step_size)

                # store fba fluxes
                logging.debug('* Store fluxes in ODE solution')
                # FIXME: better copy, this takes a lot of time and can be done much better
                for k, v in self.fba_model.flat_mapping.iteritems():
                    flux = self.fba_model.cobra_model.solution.x_dict[k]
                    vindex = df_results.columns.get_loc(v)
                    row[vindex] = flux
                    logging.debug("\t{} = {}".format(k, flux))

                all_results.append(row)

                # store and update time
                kstep += 1
                time += step_size

                logging.debug(pd.Series(row, index=self.ode_model.timeCourseSelections))

            # create result matrix
            df_results = pd.DataFrame(index=all_time, columns=self.ode_model.timeCourseSelections,
                                      data=all_results)
            df_results.time = all_time

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

    def set_fba_bounds(self):
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

    def optimize_fba(self):
        """ Optimize FBA model.

        Uses the objective sense from the fba model.
        """
        logging.debug("* FBA optimize")
        self.cobra_model.optimize(objective_sense=self.objective_sense)

        # log solution
        if hasattr(self.cobra_model, 'solution'):
            logging.debug('\tstatus: <{}>'.format(self.cobra_model.solution.status))
            for skey in sorted(self.cobra_model.solution.x_dict):
                flux = self.cobra_model.solution.x_dict[skey]
                logging.debug('\t{:<10}: {}'.format(skey, flux))

    def set_fluxes(self):
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
            flux = self.cobra_model.solution.x_dict[fba_rid]

            # reaction rates cannot be set directly in roadrunner
            # necessary to get the parameter from the flux rules
            # rr_comp[top_rid] = flux

            top_pid = self.fba_model.flux_rules[top_rid]
            self.ode_model[top_pid] = flux

            logging.debug('\t{:<10}: {:<10} = {}'.format(top_rid, fba_rid, flux))
            counter += 1

        if counter == 0:
            logging.debug('\tNo flux replacements')

    def ode_simulation(self, kstep, step_size):
        """ ODE integration for a single timestep.

        :param kstep:
        :param step_size:
        :return:
        """
        logging.debug('* ODE integration')

        # constant step size
        if kstep == 0:
            result = self.ode_model.simulate(start=0, end=0, steps=1)
        else:
            result = self.ode_model.simulate(start=0, end=step_size, steps=1)

        # store ode row
        return result[1, :]
