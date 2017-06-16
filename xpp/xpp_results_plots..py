from __future__ import print_function, absolute_import
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


def make_plot():

    df_normal = pd.read_csv("./xpp_results.tsv", sep="\t")
    df_lower = pd.read_csv("./xpp_results_lower.tsv", sep="\t")

    def barplot(ax, df):
        ax.bar(0, df.shape[0], label="All (xpp ModelDB)")
        ax.bar(1, np.nansum(df.success), label="SBML generated")
        ax.bar(2, np.nansum(df.valid), label="SBML valid")
        ax.bar(3, np.nansum(df.simulates), label="SBML simulates (roadrunner)")

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 7))
    axes = (ax1, ax2)

    ax1.set_title('Case sensitive')
    barplot(ax1, df_normal)

    ax2.set_title('xpp lowercase')
    barplot(ax2, df_lower)

    for ax in axes:
        ax.set_xlabel('Category')
        ax.set_ylabel('Model count')
        ax.legend()

    plt.show()
    # fig.savefig("xpp_results.png", bbox_inches='tight')

if __name__ == "__main__":
    make_plot()
