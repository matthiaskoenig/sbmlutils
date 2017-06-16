from __future__ import print_function, absolute_import
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

results_file = "./xpp_results.tsv"
def make_plot():

    df = pd.read_csv(results_file, sep="\t")
    print(df.head())

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 7))
    axes = (ax1, ax2)

    ax1.bar(0, df.shape[0], label="All (xpp ModelDB)")
    ax1.bar(1, np.nansum(df.success), label="SBML generated")
    ax1.bar(2, np.nansum(df.valid), label="SBML valid")
    ax1.bar(3, np.nansum(df.simulates), label="SBML simulates (roadrunner)")

    ax1.legend()
    ax1.set_xlabel('Category')
    ax1.set_ylabel('Model count')


    plt.show()
    # fig.savefig("xpp_results.png", bbox_inches='tight')

if __name__ == "__main__":
    make_plot()