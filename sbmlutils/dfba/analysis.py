"""
Generic analysis and plots of DFBA simulations.
"""
from __future__ import print_function, absolute_import
import logging
import warnings
from matplotlib import pyplot as plt

# TODO: update plots
def set_matplotlib_parameters():
    """ Sets default plot parameters.

    :return:
    """
    plt.rcParams.update({
        'axes.labelsize': 'large',
        'axes.labelweight': 'bold',
        'axes.titlesize': 'large',
        'axes.titleweight': 'bold',
        'legend.fontsize': 'small',
        'xtick.labelsize': 'large',
        'ytick.labelsize': 'large',
    })


class DFBAAnalysis(object):
    """ Plot and analysis functions for given results. """

    def __init__(self, df, rr_comp):
        self.df = df
        self.rr_comp = rr_comp

    def save_csv(self, filepath):
        """ Save results to csv. """
        if filepath is None:
            raise ValueError("filepath required")

        self.df.to_csv(filepath, sep="\t", index=False)

    def plot_species(self, filepath, **kwargs):
        """ Plot species.

        :param filepath: filepath to save figure, if None plot is shown
        :return:
        :rtype:
        """
        species_ids = ["[{}]".format(s) for s in self.rr_comp.model.getFloatingSpeciesIds()] \
            + ["[{}]".format(s) for s in self.rr_comp.model.getBoundarySpeciesIds()]
        self.plot_ids(ids=species_ids, ylabel="species", title="DFBA species timecourse",
                      filepath=filepath, **kwargs)

    def plot_reactions(self, filepath, **kwargs):
        """ Plot species.

        :param filepath: filepath to save figure, if None plot is shown
        :return:
        :rtype:
        """
        reaction_ids = self.rr_comp.model.getReactionIds()
        self.plot_ids(ids=reaction_ids, ylabel="reactions", title="DFBA reaction timecourse",
                      filepath=filepath, **kwargs)

    def plot_ids(self, ids, filepath=None, ylabel=None, title=None, **kwargs):
        """ Plot given ids against time

        :param filepath:
        :param ids: subset of ids to plot
        :param title:
        :param ylabel:
        :return:
        """
        fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(10, 10))
        x_time = self.df['time']
        for oid in ids:
            ax1.plot(x_time, self.df[oid], label=oid, **kwargs)

        ax1.set_xlabel('time')
        if ylabel:
            ax1.set_ylabel(ylabel)
        if title:
            ax1.set_title(title)
        ax1.legend()

        if filepath:
            fig.savefig(filepath, bbox_inches='tight')
            logging.info("plot_ids: {}".format(filepath))
        else:
            plt.show()


