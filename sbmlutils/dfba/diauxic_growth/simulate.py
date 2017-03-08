from __future__ import print_function, division

# directory to write files to
import os
import timeit
from sbmlutils.dfba.simulator import SimulatorDFBA
from sbmlutils.dfba.analysis import AnalysisDFBA

import dgsettings
import model_factory

from matplotlib import pylab as plt

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
    sim = SimulatorDFBA(sbml_top_path=sbml_top_path)

    # Run simulation of hybrid model
    start_time = timeit.default_timer()
    df = sim.simulate(tstart=0.0, tend=tend, steps=steps)
    elapsed = timeit.default_timer() - start_time

    print("\nSimulation time: {}\n".format(elapsed))

    # generic analysis
    analysis = AnalysisDFBA(df=df, rr_comp=sim.rr_comp)
    analysis.plot_reactions(os.path.join(directory, "dg_reactions_generic.png"))
    analysis.plot_species(os.path.join(directory, "dg_species_generic.png"))
    analysis.save_csv(os.path.join(directory, "dg_simulation_generic.csv"))

    # custom model plots
    print_species(os.path.join(directory, "dg_species.png"), df)
    print_fluxes(os.path.join(directory, "dg_fluxes.png"), df)
    return df


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
    fig, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8), (ax9, ax10, ax11, ax12), (ax13, ax14, ax15, ax16)) = plt.subplots(nrows=4, ncols=4, figsize=(18, 18))
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
        ax.plot(df.time, df['lb_EX_{}'.format(key)], linestyle='--', marker='None', color=colors[key], alpha=0.5, label="lb_EX_{}".format(key))
        ax.plot(df.time, df['ub_EX_{}'.format(key)], linestyle='--', marker='None', color=colors[key], alpha=0.5, label="ub_EX_{}".format(key))
        ax.fill_between(df.time, df['lb_EX_{}'.format(key)], df['ub_EX_{}'.format(key)], facecolor=colors[key], alpha=0.3, interpolate=False)

        ax.plot(df.time, df['EX_{}'.format(key)], linestyle='-', marker='s', color=colors[key], label="EX__{}".format(key))

        ax.set_ylabel('Flux [mmol/l/h]')
        ax.set_title('{}: Flux'.format(key))
        # ax.set_xlabel('time [h]')
        ax.legend()

    # concentrations
    for key, ax in mapping3.iteritems():
        ax.plot(df.time, df['[{}]'.format(key)], linestyle='-', marker='s', color=colors[key], label="{}".format(key))
        ax.set_ylabel('Concentration [mmol/l]')
        ax.set_title('{}: Concentration'.format(key))
        ax.legend()

    # transport reactions
    '''
    ax13.plot(df.time, df['fba__vO2'.format(key)], label="v02", color='k', linestyle='-', marker='s')
    ax13.fill_between(df.time, df['fba__zero'], df['fba__ub_vO2'], facecolor='gray', alpha=0.3,
                    interpolate=False)
    ax13.set_title('vO2')
    ax13.set_ylabel('Flux [mmol]')

    ax14.plot(df.time, df['fba__vGlcxt'.format(key)], label="vGlcxt", color='k', linestyle='-', marker='s')
    ax14.fill_between(df.time, df['fba__zero'], df['ub_vGlcxt'], facecolor='gray', alpha=0.3, interpolate=False)
    ax14.set_title('vGlcxt')
    ax14.set_ylabel('Flux [mmol]')

    for ax in (ax13, ax14, ax15, ax16):
        ax.set_xlabel('time [h]')
        ax.legend()
    '''

    fig.savefig(filepath, bbox_inches='tight')



if __name__ == "__main__":
    import numpy as np
    print('Model:', sbml_top_path)

    import logging
    # logging.getLogger().setLevel(logging.INFO)
    df = simulate_diauxic_growth(sbml_top_path, tend=1)


