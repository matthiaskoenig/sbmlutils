"""
Create all files and run the simulations.
"""
from __future__ import print_function, division
from sbmlutils import comp
from simulator import Simulator
from simsettings import *
import model_factory
import comp_factory

import os
os.chdir(out_dir)  # set working dir to models

###########################################
# Create single models
###########################################
model_factory.create_fba(fba_file)
model_factory.create_ode_bounds(ode_bounds_file)
model_factory.create_ode_update(ode_update_file)
model_factory.create_ode_model(ode_model_file)

###########################################
# Create top level model
###########################################
comp_factory.create_top_level_model(top_level_file)
# flatten the combined model

comp.flattenSBMLFile(top_level_file, output_file=flattened_file)


###########################################
# Simulate the comp models
###########################################
def simulate_model(tend=50.0, step_size=0.1):
    # Run simulation of the hybrid model
    from simsettings import top_level_file, out_dir
    import timeit

    # Simulate
    simulator = Simulator(top_level_file=top_level_file)
    start_time = timeit.default_timer()
    df = simulator.simulate(tstart=0.0, tend=tend, step_size=step_size)
    elapsed = timeit.default_timer() - start_time

    print("Simulation time: {}".format(elapsed))
    simulator.plot_reactions(df)
    simulator.plot_species(df)
    simulator.save_csv(df)

    print(df)

simulate_model(tend=50.0, step_size=0.1)
