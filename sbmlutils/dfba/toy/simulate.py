"""
Create all files and run the simulations.
"""
from __future__ import print_function, division
import timeit

from toysettings import *
from sbmlutils.dfba.simulator import SimulatorDFBA


def simulate_toymodel(directory, tend=50.0, steps=500):
    """ Simulate the model.

    :param tend:
    :param steps:
    :return:
    """
    # Run simulation of the hybrid model
    top_level_path = os.path.join(out_dir, top_file)
    sim = SimulatorDFBA(sbml_top_path=top_level_path)
    start_time = timeit.default_timer()
    df = sim.simulate(tstart=0.0, tend=tend, steps=steps)
    elapsed = timeit.default_timer() - start_time
    print("Simulation time: {}".format(elapsed))

    # Create outputs
    sim.plot_reactions(os.path.join(directory, "reactions.png"), df, rr_comp=sim.rr_comp)
    sim.plot_species(os.path.join(directory, "species.png"), df, rr_comp=sim.rr_comp)
    sim.save_csv(os.path.join(directory, "simulation.csv"), df)

if __name__ == "__main__":

    # TODO: create SED-ML and OMEX for toy model
    simulate_toymodel(out_dir, tend=50.0, steps=500)
