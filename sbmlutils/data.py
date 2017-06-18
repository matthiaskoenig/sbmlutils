"""
Helper functions for data analysis.
"""
from __future__ import print_function, absolute_import, division
import numpy as np


def overview(data):
    """ Prints overview of data vector.
    
    :param data: vector of data 
    :return: 
    """
    info = "mean  +- std [min|max]\n" \
           "{:2.2f} +- {:2.2f}\t[{:2.2f}|{:2.2f}]".format(np.mean(data), np.std(data),
                                                           np.min(data), np.max(data), )
    print('-' * 80)
    print(data)
    print('-' * 80)
    print(info)
    print('-' * 80)
    print()


if __name__ == "__main__":
    import pandas as pd
    from os.path import join as pjoin
    folder = '/home/mkoenig/git/caffeine/docs/literature/'

    df = pd.read_csv(pjoin(folder, 'Kaplan1997_Tab1.csv'), sep='\t')
    print(df)
    # overview(df.tmax)
    # overview(df.cmax)
    # overview(df.thalf)
    # overview(df.auc)
    # overview(df.cl)
    # overview(df.vd)
    print(df.age.describe())






