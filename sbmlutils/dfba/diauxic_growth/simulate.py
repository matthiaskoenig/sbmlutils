"""
Simulate the diauxic growth model.
"""
from __future__ import print_function, division, absolute_import
import os
import warnings
import logging

from sbmlutils.dfba.diauxic_growth import dgsettings
from sbmlutils.dfba.diauxic_growth import model_factory
from sbmlutils.dfba.diauxic_growth import analyse

from sbmlutils.dfba.model import DFBAModel
from sbmlutils.dfba.simulator import DFBASimulator
from sbmlutils.dfba.analysis import DFBAAnalysis
import numpy as np

# TODO: fix the DT setting, i.e allow setting of step size

directory = os.path.join(dgsettings.out_dir, 'v{}'.format(model_factory.version))
sbml_top_path = os.path.join(directory, dgsettings.top_file)


def simulate_diauxic_growth(sbml_top_path, tend):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """

    dfs = []
    for dt in [0.1]:  # [0.1, 1.0]:
        print("*** {} ***".format(dt))
        # Load model in simulator
        dfba_model = DFBAModel(sbml_path=sbml_top_path)
        # Run simulation of hybrid model
        sim = DFBASimulator(dfba_model)
        sim.simulate(tstart=0.0, tend=tend, dt=dt)
        dfs.append(sim.solution)

    print("\nSimulation time: {}\n".format(sim.time))

    '''
    # generic analysis (for all DFBA models)
    dfba_analysis = DFBAAnalysis(df=sim.solution, rr_comp=sim.ode_model)
    dfba_analysis.plot_reactions(os.path.join(directory, "dg_reactions_generic.png"),
                            linewidth=2, alpha=0.8)
    dfba_analysis.plot_species(os.path.join(directory, "dg_species_generic.png"),
                          linewidth=2, alpha=0.8)
    dfba_analysis.save_csv(os.path.join(directory, "dg_simulation_generic.csv"))
    '''
    # custom model plots & analysis
    plot_kwargs = {
        'markersize': 5,
        'marker': 'square',
        'alpha': 0.6
    }
    analyse.print_species(os.path.join(directory, "dg_species.png"), dfs, **plot_kwargs)
    analyse.print_fluxes(os.path.join(directory, "dg_fluxes.png"), dfs, **plot_kwargs)
    return dfs


def benchmark(simulator, tend, dt=0.1, Nrepeat=10):
    """ Benchmark the simulation.

    :param simulator
    :param tend:
    :param Nrepeat
    :return:
    """
    simulator.benchmark(Nrepeat=Nrepeat, tstart=0, tend=tend, dt=dt)


if __name__ == "__main__":
    print('Model:', sbml_top_path)

    logging.getLogger().setLevel(logging.INFO)
    simulate_diauxic_growth(sbml_top_path, tend=20)

    # benchmarking
    if False:
        dfba_model = DFBAModel(sbml_path=sbml_top_path)
        dfba_sim = DFBASimulator(dfba_model, lp_solver='glpk')
        print(dfba_sim.cobra_model.solver.interface)
        benchmark(dfba_sim, tend=10)
        benchmark(dfba_sim, tend=20)

        dfba_sim = DFBASimulator(dfba_model, lp_solver='cplex')
        print(dfba_sim.cobra_model.solver.interface)
        benchmark(dfba_sim, tend=10)
        benchmark(dfba_sim, tend=20)

