from __future__ import print_function, division, absolute_import

import os
import timeit
import numpy as np
from sbmlutils.dfba.simulator import DFBASimulator
from sbmlutils.dfba.model import DFBAModel
from sbmlutils.dfba.analysis import DFBAAnalysis


def simulate_toy(sbml_top_path, out_dir, dt, tend):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """
    steps = np.round(1.0 * tend / dt)  # 10*tend

    # Load model in simulator
    dfba_model = DFBAModel(sbml_path=sbml_top_path)

    # Run simulation of hybrid model
    sim = DFBASimulator(dfba_model)
    sim.simulate(tstart=0.0, tend=tend, steps=steps)
    df = sim.solution

    print("\nSimulation time: {}\n".format(sim.time))

    # generic analysis
    analysis = DFBAAnalysis(df=sim.solution, ode_model=sim.ode_model)
    analysis.plot_reactions(os.path.join(out_dir, "reactions_generic.png"))
    analysis.plot_species(os.path.join(out_dir, "species_generic.png"))
    analysis.save_csv(os.path.join(out_dir, "simulation_generic.csv"))

    return df


if __name__ == "__main__":
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diauxic_lw_v3')
    out_dir = os.path.join(model_dir, 'results')
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        print('making directory: ', out_dir)

    print('model_dir:', model_dir)
    print('out_dir:', out_dir)

    sbml_top_path = os.path.join(model_dir, 'growth_top.xml')
    print('sbml_top_path:', sbml_top_path)


    # Model validation
    # TODO: validation of top model and all external model definitions

    # Model reports

    # Simulation
    simulate_toy(sbml_top_path, out_dir, dt=0.01, tend=10.0)
