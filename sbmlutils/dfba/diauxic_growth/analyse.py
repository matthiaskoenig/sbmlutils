"""
Analysis functions.
"""
from __future__ import print_function, absolute_import
from six import iteritems
import logging
import warnings
import os
import numpy as np
import pandas as pd

from sbmlutils.dfba.analysis import set_matplotlib_parameters
from matplotlib import pyplot as plt
set_matplotlib_parameters()


def print_species(dfs, filepath=None, **kwargs):
    """ Print diauxic species.

    :param filepath:
    :param df:
    :return:
    """
    if 'marker' not in kwargs:
        kwargs['marker'] = 's'
    if 'linestyle' not in kwargs:
        kwargs['linestyle'] = '-'

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, figsize=(14, 14))
    for df in dfs:
        for ax in (ax1, ax3):
            ax.plot(df.time, df['[Ac]'],
                    color='darkred', label="Ac", **kwargs)
            ax.plot(df.time, df['[Glcxt]'],
                    color='darkblue', label="Glcxt", **kwargs)
            ax.plot(df.time, df['[O2]'],
                    color='darkgreen', label="O2", **kwargs)

        for ax in (ax2, ax4):
            ax.plot(df.time, df['[X]'],
                    color='black', label="X biomass", **kwargs)

    ax3.set_yscale('log')
    ax3.set_ylim([10E-5, 15])
    ax4.set_yscale('log')

    for ax in (ax1, ax3):
        ax.set_ylabel('Concentration [?]')

    for ax in (ax2, ax4):
        ax.set_ylabel('Biomass [?]')

    for ax in (ax1, ax2, ax3, ax4):
        ax.set_title('Diauxic Growth')
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

    fig, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8), (ax9, ax10, ax11, ax12)) = plt.subplots(nrows=3, ncols=4,
                                                                                              figsize=(18, 15))
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
    for df in dfs:
        # internal fluxes (v1, v2, v3, v4)
        for key, ax in iteritems(mapping1):
            ax.plot(df.time, df['fba__{}'.format(key)], label=labels1[key], color='k', **kwargs)
            ax.set_ylabel('Flux [mmol]')
            ax.set_title("{}: Flux".format(key))
            ax.legend()

        # exchange fluxes with bounds
        ax7.plot(df.time, df['vO2_transfer'.format(key)], color='green', label="vO2_transfer")

        for key, ax in iteritems(mapping2):
            ax.fill_between(df.time, df['lb_EX_{}'.format(key)], np.zeros(len(df.time)), facecolor=colors[key], alpha=0.3,
                            interpolate=False, step='post')
            ax.fill_between(df.time, np.zeros(len(df.time)), df['ub_EX_{}'.format(key)], facecolor=colors[key], alpha=0.2,
                            interpolate=False, step='post')
            ax.plot(df.time, df['EX_{}'.format(key)], color=colors[key], label="EX_{}".format(key), **kwargs)
            # ax.plot(df.time, df['dummy_EX_{}'.format(key)], color=colors[key], label="dummy_EX_{}".format(key), **kwargs)
            ax.plot(df.time, df['update__update_{}'.format(key)], color="black",
                    label="update_{}".format(key), **kwargs)

            ax.set_ylabel('Flux [mmol/l/h]')
            ax.set_title('{}: Flux'.format(key))
            #ax.set_ylim(np.min(np.min(df['EX_{}'.format(key)]), np.min(df['update__update_{}'.format(key)])),
            #            np.max(np.max(df['EX_{}'.format(key)]), np.max(df['update__update_{}'.format(key)])) )
                        # ax.set_xlabel('time [h]')
            ax.set_ylim(-15.1, 10)
            ax.legend()



        # concentrations
        for key, ax in iteritems(mapping3):
            ax.plot([0, np.max(df.time)], [0, 0], color='gray', linestyle='-', linewidth=1)
            ax.plot(df.time, df['[{}]'.format(key)], color=colors[key], label="{}".format(key), **kwargs)
            ax.set_ylabel('Concentration [mmol/l]')
            ax.set_title('{}: Concentration'.format(key))
            ax.set_xlabel('time [h]')

    # experimentell data
    cur_dir = os.path.dirname(os.path.abspath(__file__))  # directory of test files
    Varma1994_Fig7 = pd.read_csv(os.path.join(cur_dir, 'data/Varma1994_Fig7.csv'), sep='\t')
    inds = Varma1994_Fig7.substance == 'cell_density'
    ax12.scatter(Varma1994_Fig7.time[inds], Varma1994_Fig7.value[inds], color='black', label='data')
    ax12.set_ylabel('X [g/l]')

    inds = Varma1994_Fig7.substance == 'glucose'
    ax10.set_title("Varma1994 Fig7")
    ax10.scatter(Varma1994_Fig7.time[inds], Varma1994_Fig7.value[inds], color='black', label='data')

    inds = Varma1994_Fig7.substance == 'acetate'
    ax9.set_title("Varma1994 Fig7")
    ax9.scatter(Varma1994_Fig7.time[inds], Varma1994_Fig7.value[inds], color='black', label='data')

    for key, ax in iteritems(mapping3):
        ax.legend()

    if filepath is not None:
        fig.savefig(filepath, bbox_inches='tight')
    else:
        plt.show()

    logging.info("print_fluxes: {}".format(filepath))
