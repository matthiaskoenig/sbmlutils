from __future__ import print_function, absolute_import, division
import cobra
import optlang
import numpy as np
import timeit
from matplotlib import pyplot as plt
from six import iteritems


def benchmark(model, lp_solver, n_repeat=10, **kwargs):
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
        simulate(model=model, lp_solver=lp_solver, **kwargs)
        timings[k] = timeit.default_timer() - t_start
        print('\t[{}/{}] {:2.3}'.format(k, n_repeat, timings[k,0]))

    print('-' * 40)
    print('N={}, mean+-SD'.format(n_repeat))
    print('\t{:.5f} +- {:.5f}'.format(np.mean(timings), np.std(timings)))
    print('-' * 40)
    return timings


def simulate(model, lp_solver, n_bounds=100):

    # step wise shut down of glucose
    glc_bounds = np.linspace(-10, -0.5, n_bounds)
    for lb_glc in glc_bounds:
        # set the lower bound (uptake direction) of the exchange reaction
        model.reactions.get_by_id("EX_glc__D_e").lower_bound = lb_glc
        # pfba
        cobra.flux_analysis.pfba(model)

if __name__ == "__main__":
    print('optlang:', optlang.__version__)
    print('cobra:', cobra.__version__)

    # run timings
    timings = {}
    for solver in ['cplex']:
    # for solver in ['glpk', 'cplex']:
        sbml_path = "ecoli_fba.xml"
        model = cobra.io.read_sbml_model(sbml_path)
        t_solver = benchmark(model=model, lp_solver=solver, n_repeat=10)
        timings[solver] = t_solver

    # plot results
    fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(7, 7))

    for key, times in iteritems(timings):
        ax1.plot(times, '-s', linewidth=2, label=key)


    ax1.set_xlabel("repeat")
    ax1.set_ylabel("duration [s]")
    ax1.set_title("Timing of solver (repeated simulation)")
    ax1.legend()

    fig.savefig('solver_timings.png')





