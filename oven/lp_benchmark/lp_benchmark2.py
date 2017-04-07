from __future__ import print_function, absolute_import, division
import cobra
import optlang
import numpy as np
import timeit
from matplotlib import pyplot as plt
from six import iteritems


def benchmark(model, lp_solver, n_repeat=10, f_sim="simulate", **kwargs):
    """ Benchmark the simulate function with provided simulation parameters.

    See simulate arguments for available kwargs.

    :return: numpy array of times
    """
    # set the solver
    model.solver = lp_solver
    print(model.solver.interface)

    timings = np.zeros(shape=(n_repeat, 1))

    for k in range(n_repeat):
        t_start = timeit.default_timer()

        globals()[f_sim](model=model, **kwargs)
        # simulate(model=model, lp_solver=lp_solver, **kwargs)
        timings[k] = timeit.default_timer() - t_start
        print('\t[{}/{}] {:2.3}'.format(k, n_repeat, timings[k,0]))

    print('-' * 40)
    print('N={}, mean+-SD'.format(n_repeat))
    print('\t{:.5f} +- {:.5f}'.format(np.mean(timings), np.std(timings)))
    print('-' * 40)
    return timings


def simulate(model, n_bounds=100):
    """ Calling every time pfba.
    
    This has the overhead of the objective generation which takes up most of the time.
    :param model: 
    :param n_bounds: 
    :return: 
    """
    # step wise shut down of glucose
    glc_bounds = np.linspace(-10, -0.5, n_bounds)
    for lb_glc in glc_bounds:
        # set the lower bound (uptake direction) of the exchange reaction
        model.reactions.get_by_id("EX_glc__D_e").lower_bound = lb_glc
        # pfba
        cobra.flux_analysis.pfba(model)


def simfast(model, n_bounds=100):
    """ Adding pfba objective only once. 
    
    :param model: 
    :param n_bounds: 
    :return: 
    """
    # step wise shut down of glucose
    glc_bounds = np.linspace(-10, -0.5, n_bounds)
    for lb_glc in glc_bounds:
        # set the lower bound (uptake direction) of the exchange reaction
        model.reactions.get_by_id("EX_glc__D_e").lower_bound = lb_glc
        # pfba (objective already added to model)
        model.optimize()


def simfaster(model, n_bounds=100):
    """ Adding pfba objective only once, don't construct solution object. 

    :param model: 
    :param n_bounds: 
    :return: 
    """
    # step wise shut down of glucose
    glc_bounds = np.linspace(-10, -0.5, n_bounds)
    for lb_glc in glc_bounds:
        # set the lower bound (uptake direction) of the exchange reaction
        model.reactions.get_by_id("EX_glc__D_e").lower_bound = lb_glc
        # pfba (objective already added to model)
        model.solver.optimize()
        get_fluxes_fast(model)


def get_fluxes_fast(model, reactions=None):
    """
    Generates fast solution representation of the current solver state.

    """
    cobra.core.model.check_solver_status(model.solver.status)
    if reactions is None:
        reactions = model.reactions

    rxn_index = [rxn.id for rxn in reactions]

    # FIXME: this should be numpy arrays, no OrderedDict (would allow fast calculation of fluxes via array operation)
    # dicts would also improve the runtime
    # just get the order of reactions once, and the order of variables an reuse (we know it does not change)

    var_primals = model.solver.primal_values
    var_duals = model.solver.reduced_costs

    reduced = np.zeros(len(reactions))
    fluxes = np.zeros(len(reactions))

    # reduced costs are not always defined, e.g. for integer problems
    if var_duals[rxn_index[0]] is None:
        reduced.fill(np.nan)
        for (i, rxn) in enumerate(reactions):
            fluxes[i] = var_primals[rxn.id] - var_primals[rxn.reverse_id]
    else:
        for (i, rxn) in enumerate(reactions):
            forward = rxn.id
            reverse = rxn.reverse_id
            fluxes[i] = var_primals[forward] - var_primals[reverse]
            reduced[i] = var_duals[forward] - var_duals[reverse]

    return dict(zip(rxn_index, fluxes))



if __name__ == "__main__":
    print('optlang:', optlang.__version__)
    print('cobra:', cobra.__version__)

    # run timings
    timings = {}
    for solver in ['glpk', 'cplex', 'gurobi']:
        for f_sim in ['simulate', 'simfast', 'simfaster']:
            sbml_path = "ecoli_fba.xml"
            model = cobra.io.read_sbml_model(sbml_path)

            if f_sim in ["sim_fast", 'sim_faster']:
                # add pfba once
                cobra.flux_analysis.parsimonious.add_pfba(model)

            t_solver = benchmark(model=model, lp_solver=solver, f_sim=f_sim, n_repeat=10)
            timings[solver + ' [' + f_sim + ']'] = t_solver

    # plot results
    ccolors = {'glpk': 'darkgreen',
               'cplex': 'darkred',
               'gurobi': 'darkblue'}

    plot = True
    if plot:
        fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(7, 7))

        for key, times in iteritems(timings):
            ax1.plot(times, '-s', linewidth=2, label=key)


        ax1.set_xlabel("repeat")
        ax1.set_ylabel("duration [s]")
        ax1.set_title("Timing of solver (repeated simulation)")
        ax1.set_ylim(bottom=0)
        ax1.legend()

        fig.savefig('solver_timings.png')





