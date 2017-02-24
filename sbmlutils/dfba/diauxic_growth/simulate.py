from __future__ import print_function, division

# directory to write files to
import os
import timeit
from pprint import pprint
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

from sbmlutils.dfba.simulator import Simulator


def simulate_diauxic_growth(tend=12, steps=120):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """
    sbml_top_path = os.path.join(out_dir, 'diauxic_top.xml')

    # Load model in simulator
    sim = Simulator(sbml_top_path=sbml_top_path)

    # Run simulation of hybrid model
    start_time = timeit.default_timer()
    df = sim.simulate(tstart=0.0, tend=tend, steps=steps)
    elapsed = timeit.default_timer() - start_time

    print("\nSimulation time: {}\n".format(elapsed))

    sim.plot_reactions(os.path.join(out_dir, "reactions.png"), df, rr_comp=sim.rr_comp)
    sim.plot_species(os.path.join(out_dir, "species.png"), df, rr_comp=sim.rr_comp)
    sim.save_csv(os.path.join(out_dir, "simulation.csv"), df)

    print_species(df)
    return df


def print_species(df):
    """ Print diauxic species.

    :param df:
    :return:
    """
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

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2, figsize=(14, 14))

    for ax in (ax1, ax3):
        ax.plot(df.time, df['[Ac]'],
                 linestyle='-', marker='s', color='darkred', label="Ac")
        ax.plot(df.time, df['[Glcxt]'],
             linestyle='-', marker='s', color='darkblue', label="Glcxt")
        ax.plot(df.time, df['[O2]'],
             linestyle='-', marker='s', color='darkgreen', label="O2")
    ax3.set_yscale('log')
    ax3.set_ylim([10E-12, 15])

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

    fig.savefig(os.path.join(out_dir, "species_growth.png"))

if __name__ == "__main__":
    tend = 12
    steps = tend
    df = simulate_diauxic_growth(tend, steps)


