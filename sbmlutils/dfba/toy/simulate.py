"""
Create all files and run the simulations.
"""
from __future__ import print_function, division
import timeit
import os
import numpy as np
from matplotlib import pylab as plt

from sbmlutils.dfba.model import DFBAModel
from sbmlutils.dfba.simulator import DFBASimulator
from sbmlutils.dfba.analysis import DFBAAnalysis
from sbmlutils.dfba.toy import toysettings
from sbmlutils.dfba.toy import model_factory

plt.rcParams.update({
    'axes.labelsize': 'large',
    'axes.labelweight': 'bold',
    'axes.titlesize': 'large',
    'axes.titleweight': 'bold',
    'legend.fontsize': 'small',
    'xtick.labelsize': 'large',
    'ytick.labelsize': 'large',
})

version = model_factory.version

directory = os.path.join(toysettings.out_dir, 'v{}'.format(version))
sbml_top_path = os.path.join(directory, toysettings.top_file)
print(sbml_top_path)


def simulate_toy(sbml_top_path, tend):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """
    steps = np.round(tend / model_factory.DT_SIM)  # 10*tend

    # Load model in simulator
    dfba_model = DFBAModel(sbml_top_path=sbml_top_path)

    # Run simulation of hybrid model
    sim = DFBASimulator(dfba_model)
    sim.simulate(tstart=0.0, tend=tend, steps=steps)
    df = sim.solution

    print("\nSimulation time: {}\n".format(sim.time))

    # generic analysis
    analysis = DFBAAnalysis(df=sim.solution, rr_comp=sim.ode_model)
    analysis.plot_reactions(os.path.join(directory, "dg_reactions_generic.png"))
    analysis.plot_species(os.path.join(directory, "dg_species_generic.png"))
    analysis.save_csv(os.path.join(directory, "dg_simulation_generic.csv"))

    # custom model plots
    # print_species(os.path.join(directory, "dg_species.png"), sim.solution)
    # print_fluxes(os.path.join(directory, "dg_fluxes.png"), sim.solution)
    return df


if __name__ == "__main__":

    # TODO: create SED-ML and OMEX for toy model
    simulate_toy(sbml_top_path, tend=50.0)
