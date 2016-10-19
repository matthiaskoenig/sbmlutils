"""
Create all files and run the simulations.
"""
from __future__ import print_function, division
import timeit

from toysettings import out_dir, fba_file, ode_bounds_file, ode_update_file, ode_model_file, top_level_file, flattened_file
import model_factory
import comp_factory

from sbmlutils.dfba.simulator import Simulator


def create_toy_model(directory):
    """ Create the model.

    :return:
    """
    # Create single models
    model_factory.create_fba(fba_file, directory)
    model_factory.create_ode_bounds(ode_bounds_file, directory)
    model_factory.create_ode_update(ode_update_file, directory)
    model_factory.create_ode_model(ode_model_file, directory)

    # Create top level model
    comp_factory.create_top_level_model(top_level_file, directory)


def simulate_model(directory, tend=50.0, steps=500):
    """ Simulate the model.

    :param tend:
    :param steps:
    :return:
    """
    # Run simulation of the hybrid model
    sim = Simulator(top_level_file=top_level_file)
    start_time = timeit.default_timer()
    df = sim.simulate(tstart=0.0, tend=tend, steps=steps)
    elapsed = timeit.default_timer() - start_time
    print("Simulation time: {}".format(elapsed))

    # Create outputs
    sim.plot_reactions(directory, df, rr_comp=sim.rr_comp)
    sim.plot_species(directory, df, rr_comp=sim.rr_comp)
    sim.save_csv(directory, df)

    print(df)

if __name__ == "__main__":
    create_toy_model(out_dir)
    # simulate_model(tend=50.0, steps=500)
