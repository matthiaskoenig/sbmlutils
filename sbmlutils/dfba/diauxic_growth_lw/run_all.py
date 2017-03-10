from __future__ import print_function, division

# directory to write files to
import os
import timeit
out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

from sbmlutils.dfba.simulator import DFBASimulator

if __name__ == "__main__":

    top_level_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_ibiosim/growth_top.xml')
    tend = 100
    steps = 100

    # Run simulation of the hybrid model
    sim = DFBASimulator(out_dir, top_level_file=top_level_file)
    start_time = timeit.default_timer()
    df = sim.simulate(tstart=0.0, tend=tend, steps=steps)
    elapsed = timeit.default_timer() - start_time
    print("Simulation time: {}".format(elapsed))

    # Create outputs
    sim.plot_reactions(df, rr_comp=sim.rr_comp)
    sim.plot_species(df, rr_comp=sim.rr_comp)
    sim.save_csv(df)

    print(df)
