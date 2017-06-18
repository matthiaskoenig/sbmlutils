from __future__ import print_function, absolute_import
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

failures = {
    'arrays': [7, 8, 9, 10, 11, 12, 23, 24, 27, 29, 53, 54, 55, 56, 57, 59, 60, 61, 62, 63,
               97, 129, 130, 131, 132, 133, 134, 135, 136, 141],
    'table': [27, 65, 66, 67, 68, 97, 129],
    'shift': [17, 18],
    'sum': [17, 18],
    'global': [23, 53, 54, 58, 70, 71, 77, 97, 112],
    'dist': [73],
    'set': [48],
    'utf8_encoding': [139],
    'bad xpp encoding': [40, 85,
                         '41 (id clash function definition & parameter)',
                         '45 (false encoded as 0, unknown control character !)',
                         '46 (false encoded as 0, unknown control character !)',
                         '47 (unknown control character !)',
                         '64 (number assignment, e.g. aux 1=(t-t2)',
                         '86 (bad numbers: 1e-0.6)',
                         '87 (bad numbers: 1e-0.6)',
                         '88 (circular assignments, aux gkc = gKC*cd*chid)',
                         '89 (circular assignments, aux gkc = gKC*cd*chid)',
                         '96 (invalid statement, d)',
                         '111 (circular assignments, aux gkc = gKC*cd*chid)',
                         '125 (incorrect assignment, Ca[0] instead of Ca(0)',
                         '138 (circular assignments, aux gkc = gKC*cd*chid',
                         ],
    'boundary': [70],
    'bug': [26, 31, 32, 69],
    'unknown': [138],
}

def make_plot():

    df_normal = pd.read_csv("./xpp_results.tsv", sep="\t")
    df_lower = pd.read_csv("./xpp_results_lower.tsv", sep="\t")

    def barplot(ax, df):
        ax.bar(0, df.shape[0], label="All (xpp ModelDB)")
        ax.bar(1, np.nansum(df.success), label="SBML generated")
        ax.bar(2, np.nansum(df.valid), label="SBML valid")
        ax.bar(3, np.nansum(df.simulates), label="SBML simulates (roadrunner)")

    fig, (ax1, ax2, ax3) = plt.subplots(nrows=1, ncols=3, figsize=(20, 7))

    ax1.set_title('Case sensitive')
    barplot(ax1, df_normal)

    ax2.set_title('xpp lowercase')
    barplot(ax2, df_lower)

    for ax in (ax1, ax2):
        ax.set_xlabel('Category')
        ax.set_ylabel('Model count')
        ax.legend()

    ax3.set_title('Problem')
    for k, key in enumerate(sorted(failures.keys())):
        ax3.bar(k, len(failures[key]), label=key)
    ax3.legend()
    ax3.set_xlim(-1, 20)

    # plt.show()
    fig.savefig("xpp_results.png", bbox_inches='tight')

if __name__ == "__main__":
    make_plot()
