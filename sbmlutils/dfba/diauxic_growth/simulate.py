from __future__ import print_function, division

# directory to write files to
import os
import timeit
from pprint import pprint
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

from sbmlutils.dfba.simulator import Simulator


def simulate_diauxic_growth():
    """ Simulate the diauxic growth model.

    :return:
    """
    sbml_top_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results/diauxic_top.xml')

    # Load model in simulator
    sim = Simulator(sbml_top_path=sbml_top_path)

    # Run simulation of hybrid model
    tend = 100
    steps = 100
    start_time = timeit.default_timer()
    df = sim.simulate(tstart=0.0, tend=tend, steps=steps)
    elapsed = timeit.default_timer() - start_time
    print("Simulation time: {}".format(elapsed))

    pprint(df)

    '''
    # Create outputs
    sim.plot_reactions(df, rr_comp=sim.rr_comp)
    sim.plot_species(df, rr_comp=sim.rr_comp)
    sim.save_csv(df)
    '''



if __name__ == "__main__":
    simulate_diauxic_growth()


