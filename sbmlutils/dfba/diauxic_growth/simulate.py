"""
Simulate the diauxic growth model.
"""
from __future__ import print_function, division, absolute_import
import os
import numpy as np
import warnings
import logging

from matplotlib import pyplot as plt

from sbmlutils.dfba.utils import versioned_directory

from sbmlutils.dfba.diauxic_growth import settings
from sbmlutils.dfba.diauxic_growth import model_factory
from sbmlutils.dfba.diauxic_growth import analyse
from sbmlutils.dfba.simulator import simulate_dfba, analyse_uniqueness


def simulate_diauxic_growth(sbml_path, out_dir, dts=[0.01, 0.1], figures=True):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """
    tend = 15
    dfs = []
    for dt in dts:
        df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=tend, dt=dt, pfba=False)
        dfs.append(df)

        # uniqueness of solution
        analyse_uniqueness(dfba_simulator)

        # generic analysis
        # analysis = DFBAAnalysis(df=df, rr_comp=dfba_simulator.ode_model)
        # analysis.plot_reactions(os.path.join(out_dir, "fig_reactions_generic_dt{}.png".format(dt)),
        #                         **plot_kwargs)
        # analysis.plot_species(os.path.join(out_dir, "fig_species_generic_dt{}.png".format(dt)),
        #                       **plot_kwargs)
        # analysis.save_csv(os.path.join(out_dir, "data_simulation_generic_dt{}.csv".format(dt)))

    if figures:
        # custom model plots
        plot_kwargs = {
            'markersize': 4,
            'marker': 'None',
            'alpha': 0.5
        }
        analyse.print_species(filepath=os.path.join(out_dir, "fig_species.png"), dfs=dfs, **plot_kwargs)
        analyse.print_fluxes(filepath=os.path.join(out_dir, "fig_fluxes.png"), dfs=dfs, **plot_kwargs)
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
    from sbmlutils.dfba.model import DFBAModel
    from sbmlutils.dfba.simulator import DFBASimulator

    directory = versioned_directory(settings.OUT_DIR, settings.VERSION)
    sbml_path = os.path.join(directory, settings.TOP_LOCATION)

    dfba_model = DFBAModel(sbml_path=sbml_path)
    print(dfba_model)

    # logging.getLogger().setLevel(logging.INFO)
    simulate_diauxic_growth(sbml_path, out_dir=directory, dts=[0.01])

    # benchmark simulation
    if False:

        for solver in ['glpk', 'cplex']:
        # for solver in ['glpk', 'cplex', 'gurobi']:
        # for solver in ['glpk']:
            dfba_model = DFBAModel(sbml_path=sbml_path)
            dfba_simulator = DFBASimulator(dfba_model, lp_solver=solver)
            print(dfba_simulator.cobra_model.solver.interface)
            dfba_simulator.benchmark(n_repeat=20, tend=10, dt=0.05)

    # create COMBINE archive
    from tellurium.utils import omex
    creators = [
        omex.Creator(givenName="Matthias", familyName="Koenig", organization="Humboldt University Berlin", email="konigmatt@googlemail.com"),
        omex.Creator(givenName="Leandro", familyName="Watanabe", organization="University of Utah",
                     email="leandrohw@gmail.com")
    ]
    omex_path = os.path.join(settings.OUT_DIR, "{}_v{}.omex".format(settings.MODEL_ID, settings.VERSION))
    omex.combineArchiveFromDirectory(directory=directory,
                                     omexPath=omex_path,
                                     creators=creators,
                                     creators_for_all=True)

    omex.printArchive(omex_path)

