"""
Generic analysis and plots of DFBA simulations.
"""
from matplotlib import pyplot as plt


class DFBAAnalysis(object):
    def __init__(self, df, rr_comp):
        self.df = df
        self.rr_comp = rr_comp

    def plot_species(self, filepath):
        """ Plot species.

        :param df:
        :type df:
        :return:
        :rtype:
        """
        species_ids = ["[{}]".format(s) for s in self.rr_comp.model.getFloatingSpeciesIds()] \
            + ["[{}]".format(s) for s in self.rr_comp.model.getBoundarySpeciesIds()]

        ax_s = self.df.plot(x='time', y=species_ids)
        fig = ax_s.get_figure()
        if filepath:
            fig.savefig(filepath)
        else:
            plt.show()

    def plot_reactions(self, filepath):
        """ Create reactions plots.

        :param df: solution pandas DataFrame
        :type df:
        :param filename
        :return:
        :rtype:
        """
        reaction_ids = self.rr_comp.model.getReactionIds()

        ax_r = self.df.plot(x='time', y=reaction_ids)
        fig = ax_r.get_figure()
        if filepath:
            fig.savefig(filepath)
        else:
            plt.show()

    def save_csv(self, filepath):
        """ Save results to csv. """
        self.df.to_csv(filepath, sep="\t", index=False)
