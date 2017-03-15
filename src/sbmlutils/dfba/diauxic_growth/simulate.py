"""
Simulate the diauxic growth model.
"""
from __future__ import print_function, division

import os

import dgsettings
import model_factory
import numpy as np
import pandas as pd
from matplotlib import pylab as plt
from sbmlutils.dfba.model import DFBAModel
from sbmlutils.dfba.simulator import DFBASimulator
from sbmlutils.dfba.analysis import DFBAAnalysis

plt.rcParams.update({
    'axes.labelsize': 'large',
    'axes.labelweight': 'bold',
    'axes.titlesize': 'large',
    'axes.titleweight': 'bold',
    'legend.fontsize': 'small',
    'xtick.labelsize': 'large',
    'ytick.labelsize': 'large',
})

version = model_factory.version

directory = os.path.join(dgsettings.out_dir, 'v{}'.format(version))
sbml_top_path = os.path.join(directory, dgsettings.top_file)

from model_factory import DT_SIM


def simulate_diauxic_growth(sbml_top_path, tend):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """
    steps = np.round(tend / DT_SIM)  # 10*tend

    # Load model in simulator
    dfba_model = DFBAModel(sbml_top_path=sbml_top_path)

    # Run simulation of hybrid model
    sim = DFBASimulator(dfba_model)
    sim.simulate(tstart=0.0, tend=tend, steps=steps)
    df = sim.solution

    print("\nSimulation time: {}\n".format(sim.time))

    # generic analysis
    analysis = DFBAAnalysis(df=sim.solution, rr_comp=sim.ode_model)
    analysis.plot_reactions(os.path.join(directory, "dg_reactions_generic.png"))
    analysis.plot_species(os.path.join(directory, "dg_species_generic.png"))
    analysis.save_csv(os.path.join(directory, "dg_simulation_generic.csv"))

    # custom model plots
    print_species(os.path.join(directory, "dg_species.png"), sim.solution)
    print_fluxes(os.path.join(directory, "dg_fluxes.png"), sim.solution)
    return df


def benchmark(simulator, tend, Nrepeat=10):
    """ Benchmark the simulation.

    :param sbml_top_path:
    :param tend:
    :return:
    """
    steps = np.round(tend / DT_SIM)  # 10*tend
    dfba_sim.benchmark(Nrepeat=Nrepeat, tstart=0, tend=tend, steps=steps)


def print_species(filepath, df):
    """ Print diauxic species.

    :param df:
    :return:
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, figsize=(14, 14))

    for ax in (ax1, ax3):
        ax.plot(df.time, df['[Ac]'],
                 linestyle='-', marker='s', color='darkred', label="Ac")
        ax.plot(df.time, df['[Glcxt]'],
             linestyle='-', marker='s', color='darkblue', label="Glcxt")
        ax.plot(df.time, df['[O2]'],
             linestyle='-', marker='s', color='darkgreen', label="O2")
    ax3.set_yscale('log')
    ax3.set_ylim([10E-5, 15])

    for ax in (ax2, ax4):
        ax.plot(df.time, df['[X]'],
             linestyle='-', marker='s', color='black', label="X biomass")
    ax4.set_yscale('log')

    for ax in (ax1, ax3):
        ax.set_ylabel('Concentration [?]')

    for ax in (ax2, ax4):
        ax.set_ylabel('Biomass [?]')

    for ax in (ax1, ax2, ax3, ax4):
        ax.set_title('Diauxic Growth')
        ax.set_xlabel('time [h]')
        ax.legend()

    fig.savefig(filepath, bbox_inches='tight')


def print_fluxes(filepath, df):
    """ Print exchange & internal fluxes with respective bounds.

    :param df:
    :return:
    """
    fig, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8), (ax9, ax10, ax11, ax12)) = plt.subplots(nrows=3, ncols=4, figsize=(18, 15))
    fig.subplots_adjust(wspace=0.4, hspace=0.3)

    # exchange fluxes
    mapping1 = {'v1': ax1, 'v2': ax2, 'v3': ax3, 'v4': ax4}
    labels1 = {'v1': "v1 (39.43 Ac + 35 O2 -> X)",
                'v2': "v2 (9.46 Glcxt + 12.92 O2 -> X)",
                'v3': "v3 (9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X)",
                'v4': "v4 (19.23 Glcxt -> 12.12 Ac + X)"}

    mapping2 = {'Ac': ax5, 'Glcxt': ax6, 'O2': ax7, 'X': ax8}
    mapping3 = {'Ac': ax9, 'Glcxt': ax10, 'O2': ax11, 'X': ax12}

    colors = {'Ac': 'darkred',
               'Glcxt': 'darkgreen',
               'O2': 'darkblue',
               'X': 'black'}

    # internal fluxes (v1, v2, v3, v4)
    for key, ax in mapping1.iteritems():
        ax.plot(df.time, df['fba__{}'.format(key)], label=labels1[key], color='k', linestyle='-', marker='s')
        ax.set_ylabel('Flux [mmol]')
        ax.set_title("{}: Flux".format(key))
        ax.legend()

    # exchange fluxes with bounds
    for key, ax in mapping2.iteritems():
        ax.fill_between(df.time, df['lb_EX_{}'.format(key)], np.zeros(len(df.time)), facecolor=colors[key], alpha=0.3, interpolate=False, step='post')
        ax.fill_between(df.time, np.zeros(len(df.time)), df['ub_EX_{}'.format(key)], facecolor=colors[key], alpha=0.2, interpolate=False, step='post')
        ax.plot(df.time, df['EX_{}'.format(key)], linestyle='-', marker='s', color=colors[key], label="EX__{}".format(key))

        ax.set_ylabel('Flux [mmol/l/h]')
        ax.set_title('{}: Flux'.format(key))
        ax.set_ylim(np.min(df['EX_{}'.format(key)]), np.max(df['EX_{}'.format(key)]))
        # ax.set_xlabel('time [h]')
        ax.legend()

    # concentrations
    for key, ax in mapping3.iteritems():
        ax.plot([0, np.max(df.time)], [0, 0], color='gray', linestyle='-', linewidth=1)
        ax.plot(df.time, df['[{}]'.format(key)], linestyle='-', marker='s', color=colors[key], label="{}".format(key))
        ax.set_ylabel('Concentration [mmol/l]')
        ax.set_title('{}: Concentration'.format(key))
        ax.set_xlabel('time [h]')

    # experimentell data
    Varma1994_Fig7 = pd.read_csv('./data/Varma1994_Fig7.csv', sep='\t')
    inds = Varma1994_Fig7.substance == 'cell_density'
    ax12.scatter(Varma1994_Fig7.time[inds], Varma1994_Fig7.value[inds], color='black', label='data')
    ax12.set_ylabel('X [g/l]')

    inds = Varma1994_Fig7.substance == 'glucose'
    ax10.set_title("Varma1994 Fig7")
    ax10.scatter(Varma1994_Fig7.time[inds], Varma1994_Fig7.value[inds], color='black', label='data')

    inds = Varma1994_Fig7.substance == 'acetate'
    ax9.set_title("Varma1994 Fig7")
    ax9.scatter(Varma1994_Fig7.time[inds], Varma1994_Fig7.value[inds], color='black', label='data')

    for key, ax in mapping3.iteritems():
        ax.legend()

    fig.savefig(filepath, bbox_inches='tight')


if __name__ == "__main__":

    print('Model:', sbml_top_path)

    import logging
    logging.getLogger().setLevel(logging.ERROR)
    # simulate_diauxic_growth(sbml_top_path, tend=20)

    dfba_model = DFBAModel(sbml_top_path=sbml_top_path)
    dfba_sim = DFBASimulator(dfba_model, lp_solver='glpk')
    print(dfba_sim.cobra_model.solver.interface)
    benchmark(dfba_sim, tend=10)
    benchmark(dfba_sim, tend=20)

    dfba_sim = DFBASimulator(dfba_model, lp_solver='cplex')
    print(dfba_sim.cobra_model.solver.interface)
    benchmark(dfba_sim, tend=10)
    benchmark(dfba_sim, tend=20)

    # dfba_sim = DFBASimulator(dfba_model, lp_solver='gurobi')
    # print(dfba_sim.cobra_model.solver.interface)
    # benchmark(dfba_sim, tend=10)
    # benchmark(dfba_sim, tend=20)

