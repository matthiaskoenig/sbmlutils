"""
Run toy model simulations.
"""
from __future__ import print_function, division
import os
import logging
from six import iteritems
import numpy as np
import pandas as pd

from sbmlutils.dfba.toy_wholecell import settings, model_factory
from sbmlutils.dfba.simulator import simulate_dfba
from sbmlutils.dfba.analysis import DFBAAnalysis

from sbmlutils.dfba.utils import versioned_directory
from sbmlutils.dfba.analysis import set_matplotlib_parameters
from matplotlib import pyplot as plt
set_matplotlib_parameters()


def print_species(dfs, filepath=None, **kwargs):
    """ Print toy species.

    :param filepath:
    :param df:
    :return:
    """
    if 'marker' not in kwargs:
        kwargs['marker'] = 's'
    if 'linestyle' not in kwargs:
        kwargs['linestyle'] = '-'

    # check if single DataFrame
    if type(dfs) == pd.DataFrame:
        dfs = [dfs]

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 7))
    for k, df in enumerate(dfs):
        for ax in (ax1, ax2):
            if k == 0:
                ax.plot(df.time, df['[A]'], color='darkred', label="[A]", **kwargs)
                ax.plot(df.time, df['[C]'], color='darkblue', label="[C]", **kwargs)
                ax.plot(df.time, df['[D]'], color='darkgreen', label="[D]", **kwargs)
                ax.plot(df.time, df['[A]']+df['[C]']+df['[D]'], color='black', label="[A]+[C]+[D]", **kwargs)
            else:
                ax.plot(df.time, df['[A]'], color='darkred', label='_nolegend_', **kwargs)
                ax.plot(df.time, df['[C]'], color='darkblue', label='_nolegend_', **kwargs)
                ax.plot(df.time, df['[D]'], color='darkgreen', label='_nolegend_', **kwargs)
                ax.plot(df.time, df['[A]'] + df['[C]'] + df['[D]'], color='black', label='_nolegend_', **kwargs)

    ax2.set_yscale('log')

    for ax in (ax1, ax2):
        ax.set_ylabel('Concentration [?]')

    for ax in (ax1, ax2):
        ax.set_title('Toy model')
        ax.set_xlabel('time [h]')
        ax.legend()
    if filepath is not None:
        fig.savefig(filepath, bbox_inches='tight')
    else:
        plt.show()
    logging.info("print_species: {}".format(filepath))


def print_fluxes(dfs, filepath=None, **kwargs):
    """ Print exchange & internal fluxes with respective bounds.

    :param filepath:
    :param df:
    :return:
    """
    if 'marker' not in kwargs:
        kwargs['marker'] = 's'
    if 'linestyle' not in kwargs:
        kwargs['linestyle'] = '-'

    fig, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(nrows=2, ncols=4,
                                                                    figsize=(18, 9))
    fig.subplots_adjust(wspace=0.4, hspace=0.3)

    mapping = {
        'fba__R1': ax1,
        'fba__R2': ax2,
        'fba__R3': ax3,
        'R4': ax4,
        'EX_A': ax5,
        'EX_C': ax6,
        'update__update_A': ax7,
        'update__update_C': ax8,
    }
    colors = {
        'fba__R1': 'darkgreen',
        'fba__R2': 'darkred',
        'fba__R3': 'orange',
        'R4': 'darkblue',
        'EX_A': 'magenta',
        'EX_C': 'black',
        'update__update_A': 'lightblue',
        'update__update_C': 'lightgreen',
    }

    for k, df in enumerate(dfs):
        for key, ax in iteritems(mapping):
            if k == 0:
                ax.plot(df.time, df[key], label=key, color=colors[key], **kwargs)
            else:
                ax.plot(df.time, df[key], label='_nolegend_', color=colors[key], **kwargs)
            ax.set_ylabel('Flux [?]')
            ax.legend()

    for key, ax in iteritems(mapping):
        ax.set_xlabel('time')
        ax.legend()

    if filepath is not None:
        fig.savefig(filepath, bbox_inches='tight')
    else:
        plt.show()

    logging.info("print_fluxes: {}".format(filepath))


def simulate_toy(sbml_path, out_dir, dts=[0.1, 1.0, 5.0], figures=True, tend=50):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """
    plot_kwargs = {
        'markersize': 4,
        'marker': 's',
        'alpha': 0.5
    }
    dfs = []
    for dt in dts:
        df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=tend, dt=dt)
        dfs.append(df)

        # generic analysis
        analysis = DFBAAnalysis(df=df, ode_model=dfba_simulator.ode_model)

        if figures:
            analysis.plot_reactions(os.path.join(out_dir, "fig_reactions_generic_dt{}.png".format(dt)),
                                    **plot_kwargs)
            analysis.plot_species(os.path.join(out_dir, "fig_species_generic_dt{}.png".format(dt)),
                                  **plot_kwargs)
            analysis.save_csv(os.path.join(out_dir, "data_simulation_generic_dt{}.csv".format(dt)))

    # custom model plots
    if figures:
        print_species(dfs=dfs, filepath=os.path.join(out_dir, "fig_species.png"), **plot_kwargs)
        print_fluxes(dfs=dfs, filepath=os.path.join(out_dir, "fig_fluxes.png"), **plot_kwargs)
    return dfs


if __name__ == "__main__":
    directory = versioned_directory(settings.out_dir, model_factory.version)
    sbml_path = os.path.join(directory, settings.top_file)

    import logging
    logging.basicConfig(level=logging.DEBUG)

    from sbmlutils.dfba.model import DFBAModel
    dfba_model = DFBAModel(sbml_path=sbml_path)

    # simulate_toy(sbml_path, out_dir=directory, dts=[5.0], tend=10)
    simulate_toy(sbml_path, out_dir=directory)