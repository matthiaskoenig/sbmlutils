"""
Run toy_atp model simulations.
"""
from __future__ import print_function, division
import os
import logging
import pandas as pd
from matplotlib import pyplot as plt

from sbmlutils.dfba.toy_atp import settings, model_factory
from sbmlutils.dfba.simulator import simulate_dfba, analyse_uniqueness
from sbmlutils.dfba.analysis import DFBAAnalysis
from sbmlutils.dfba.utils import versioned_directory
from sbmlutils.dfba.analysis import set_matplotlib_parameters

set_matplotlib_parameters()


def print_species(dfs, filepath=None, **kwargs):
    """ Print toy atp species.

    :param filepath:
    :param df:
    :return:
    """
    if 'marker' not in kwargs:
        kwargs['marker'] = 's'
    if 'linestyle' not in kwargs:
        kwargs['linestyle'] = '-'

    # check if single DataFrame
    if type(dfs) == pd.DataFrame:
        dfs = [dfs]

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 7))
    for k, df in enumerate(dfs):
        for ax in (ax1, ax2):
            if k == 0:
                ax.plot(df.time, df['atp_tot'], color='black', label="[atp] + [adp]", **kwargs)
                ax.plot(df.time, df['c3_tot'], color='gray', label="2*[glc] + [pyr]", **kwargs)
                ax.plot(df.time, df['[atp]'], color='darkred', label="[atp]", **kwargs)
                ax.plot(df.time, df['[adp]'], color='darkblue', label="[adp]", **kwargs)
                ax.plot(df.time, df['[glc]'], color='darkgreen', label="[glc]", **kwargs)
                ax.plot(df.time, df['[pyr]'], color='darkorange', label="[pyr]", **kwargs)
            else:
                ax.plot(df.time, df['[atp]'] + df['[adp]'], color='black', label="_nolegend_", **kwargs)
                ax.plot(df.time, df['c3_tot'], color='gray', label="_nolegend_", **kwargs)
                ax.plot(df.time, df['[atp]'], color='darkred', label="_nolegend_", **kwargs)
                ax.plot(df.time, df['[adp]'], color='darkblue', label="_nolegend_", **kwargs)
                ax.plot(df.time, df['[glc]'], color='darkgreen', label="_nolegend_", **kwargs)
                ax.plot(df.time, df['[pyr]'], color='darkorange', label="_nolegend_", **kwargs)
    ax2.set_yscale('log')

    for ax in (ax1, ax2):
        ax.set_ylabel('Concentration [mM]')

    for ax in (ax1, ax2):
        ax.set_title('toy_atp')
        ax.set_xlabel('time [h]')
        ax.legend()
    if filepath is not None:
        fig.savefig(filepath, bbox_inches='tight')
    else:
        plt.show()
    logging.info("print_species: {}".format(filepath))


def print_fluxes(dfs, filepath=None, **kwargs):
    """ Print exchange & internal fluxes with respective bounds.

    :param filepath:
    :param df:
    :return:
    """
    if 'marker' not in kwargs:
        kwargs['marker'] = 's'
    if 'linestyle' not in kwargs:
        kwargs['linestyle'] = '-'

    fig, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(nrows=2, ncols=4,
                                                                    figsize=(18, 9))
    fig.subplots_adjust(wspace=0.4, hspace=0.3)

    mapping = {
        'fba__R1': ax1,
        'fba__R2': ax2,
        'fba__R3': ax3,
        'R4': ax4,
        'EX_A': ax5,
        'EX_C': ax6,
        'update__update_A': ax7,
        'update__update_C': ax8,
    }
    colors = {
        'fba__R1': 'darkgreen',
        'fba__R2': 'darkred',
        'fba__R3': 'orange',
        'R4': 'darkblue',
        'EX_A': 'magenta',
        'EX_C': 'black',
        'update__update_A': 'lightblue',
        'update__update_C': 'lightgreen',
    }

    for k, df in enumerate(dfs):
        for key, ax in mapping.items():
            if k == 0:
                ax.plot(df.time, df[key], label=key, color=colors[key], **kwargs)
            else:
                ax.plot(df.time, df[key], label='_nolegend_', color=colors[key], **kwargs)
            ax.set_ylabel('Flux [?]')
            ax.legend()

    for key, ax in mapping.items():
        ax.set_xlabel('time')
        ax.legend()

    if filepath is not None:
        fig.savefig(filepath, bbox_inches='tight')
    else:
        plt.show()

    logging.info("print_fluxes: {}".format(filepath))


def simulate_toy_atp(sbml_path, out_dir, dts=[0.1], figures=True, tend=15):
    """ Simulate the diauxic growth model.

    :return: solution data frame
    """
    plot_kwargs = {
        'markersize': 4,
        'marker': 's',
        'alpha': 0.5
    }
    dfs = []
    for dt in dts:
        # perform simulation
        df, dfba_model, dfba_simulator = simulate_dfba(sbml_path, tend=tend, dt=dt)
        dfs.append(df)

        analyse_uniqueness(dfba_simulator=dfba_simulator)

        # generic analysis
        analysis = DFBAAnalysis(df=df, ode_model=dfba_simulator.ode_model)

        if figures:
            analysis.plot_reactions(os.path.join(out_dir, "fig_reactions_generic_dt{}.png".format(dt)),
                                    **plot_kwargs)
            analysis.plot_species(os.path.join(out_dir, "fig_species_generic_dt{}.png".format(dt)),
                                  **plot_kwargs)
            analysis.save_csv(os.path.join(out_dir, "data_simulation_generic_dt{}.csv".format(dt)))

    # custom model plots
    if figures:
        print_species(dfs=dfs, filepath=os.path.join(out_dir, "fig_species.png"), **plot_kwargs)
        # print_fluxes(dfs=dfs, filepath=os.path.join(out_dir, "fig_fluxes.png"), **plot_kwargs)
    return dfs


def create_sedml(sedml_location, sbml_location, directory, dt, tend, species_ids, reactions_ids):
    import phrasedml
    phrasedml.setWorkingDirectory(directory)
    steps = int(1.0 * tend / dt)

    # species_ids = self.rr_comp.model.getFloatingSpeciesIds() + self.rr_comp.model.getBoundarySpeciesIds()]
    species_ids = ", ".join(['atp', 'adp', 'glc', 'pyr', 'dummy_S', 'atp + adp'])
    reaction_ids = ", ".join(['RATP', 'pEX_atp', 'pEX_atp', 'pEX_glc', 'pEX_pyr'])

    # TODO: load SBML

    # TODO: log plot

    p = """
          model1 = model "{}"
          sim1 = simulate uniform(0, {}, {})
          sim1.algorithm = kisao.500
          task1 = run sim1 on model1
          plot "Figure 1: DFBA species vs. time" time vs {}
          plot "Figure 2: DFBA fluxes vs. time" time vs {}
          report "Report 1: DFBA species vs. time" time vs {}
          report "Report 2: DFBA fluxes vs. time" time vs {}

    """.format(sbml_location, tend, steps, species_ids, reaction_ids, species_ids, reaction_ids)

    # TODO: add DFBA kisao
    # TODO: save sedml


    return_code = phrasedml.convertString(p)
    if return_code is None:
        print(phrasedml.getLastError())

    # getPhrasedWarnings()
    # getLastPhrasedError()
    sedml = phrasedml.getLastSEDML()
    print(sedml)

    sedml_file = os.path.join(directory, sedml_location)
    with open(sedml_file, "w") as f:
        f.write(sedml)



if __name__ == "__main__":
    directory = versioned_directory(settings.OUT_DIR, settings.VERSION)
    sbml_path = os.path.join(directory, settings.TOP_LOCATION)

    # create SED-ML
    create_sedml(settings.SEDML_LOCATION, settings.TOP_LOCATION, directory=directory, dts=[0.1], tend=15)



    import logging
    # logging.basicConfig(level=logging.DEBUG)

    from sbmlutils.dfba.model import DFBAModel
    dfba_model = DFBAModel(sbml_path=sbml_path)

    # simulate_toy(sbml_path, out_dir=directory, dts=[5.0], tend=10)
    simulate_toy_atp(sbml_path, out_dir=directory)
