import os
import re
import roadrunner
from roadrunner import SelectionRecord
from pprint import pprint
import pandas as pd
import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
from IPython.display import Image
from IPython.core.display import HTML
import tellurium as te
import logging
import coloredlogs


from pylimax.models.glucose_pkpd import model_factory
from pylimax.models.glucose_pkpd.glucose_pkpd_model import mid, version, SUBSTANCES_BODY

# -----------------------------
# Logging
# -----------------------------
coloredlogs.install(
    level='INFO',
    fmt="%(pathname)s:%(lineno)s %(funcName)s %(levelname) -10s %(message)s"
    # fmt="%(levelname) -10s %(asctime)s %(module)s:%(lineno)s %(funcName)s %(message)s"
)

# -----------------------------
# Data access
# -----------------------------
path_dir = os.path.dirname(os.path.realpath(__file__))
results_dir = os.path.abspath(os.path.join(path_dir, './_results/'))
data_dir = os.path.abspath(os.path.join(path_dir, '../digitize/'))


def load_glc_data(fid, sep="\t", data_dir=data_dir, show=True):
    """ Loads data from given figure/table id."""
    study = fid.split('_')[0]
    path = os.path.join(data_dir, study, '{}.csv'.format(fid))
    df = pd.read_csv(path, sep=sep, comment="#")
    if show is True:
        print(df.head())
        print(fid)
    return df


# -----------------------------
# Plotting
# -----------------------------
# arguments for plot without error
kwargs_data = {'marker': 's', 'linestyle': '--', 'linewidth': 1, 'capsize': 3}
kwargs_sim = {'marker': None, 'linestyle': '-', 'linewidth': 2}
kwargs_data_plt = kwargs_data.copy()
del kwargs_data_plt['capsize']


def save_glc_fig(fig, fid):
    fig.savefig(os.path.join(results_dir, "{}.png".format(fid)), dpi=300, bbox_inches="tight")
    # fig.savefig(os.path.join(results_dir, "{}.svg".format(fid)), bbox_inches="tight")
    plt.show()


# global settings for plots
plt.rcParams.update({
    'axes.labelsize': 'large',
    'axes.labelweight': 'bold',
    'axes.titlesize': 'medium',
    'axes.titleweight': 'bold',
    'legend.fontsize': 'small',
    'xtick.labelsize': 'large',
    'ytick.labelsize': 'large',
    'figure.facecolor': '1.00'
})


# -----------------------------
# Simulation
# -----------------------------
def load_model(info=True):
    """ Loads the latest model version. """
    path = model_path()
    logging.info(f'Model:{path}')
    r = roadrunner.RoadRunner(path)
    set_selections(r)
    return r


def model_path():
    """ Model path of latest model version."""
    return os.path.join(model_factory.target_dir, f'{mid}_{version}.xml')


def set_selections(r):
    """ Sets the full model selections. """
    r.timeCourseSelections = ["time"] + r.model.getFloatingSpeciesIds() + r.model.getBoundarySpeciesIds() + r.model.getGlobalParameterIds() + r.model.getReactionIds()
    r.timeCourseSelections += [f'[{key}]' for key in (r.model.getFloatingSpeciesIds() + r.model.getBoundarySpeciesIds())]


def simulate(r, start=None, end=None, steps=None, points=None, **kwargs):
    s = r.simulate(start=start, end=end, steps=steps, points=points, **kwargs)
    return pd.DataFrame(s, columns=s.colnames)


# -----------------------------
# Initial values
# -----------------------------
def get_species_keys(sid, species_ids):
    """ Get keys of species in given ids.
    Relies on naming patterns of ids. This does not get the species ids of the submodels, but only of the
    main model.
    """
    keys = []
    for species_id in species_ids:
        # use regular expression
        # pattern = r'[A-Z]*[\_]*A[a-z]+(_blood)*\_{}'.format(sid)
        pattern = r'^A[a-z]+(_blood)*\_{}$'.format(sid)
        match = re.search(pattern, species_id)
        if match:
            # print("match:", species_id)
            keys.append(species_id)

    return keys


def set_initial_values(r, sid, value, method="concentration"):
    """ Setting the initial concentration of a distributing substance.
    Takes care of all the compartment values so starting close/in steady state.

    Units are in model units

    return: species keys which have been set
    """
    if method not in ["amount", "concentration"]:
        raise ValueError

    species_ids = r.getFloatingSpeciesIds() + r.getBoundarySpeciesIds()
    species_keys = get_species_keys(sid, species_ids)
    for key in species_keys:
        if 'urine' in key:
            logging.warning("urinary values are not set")
            continue
        if method == "concentration":
            rkey = f'init([{key}])'
        elif method == "amount":
            rkey = f'init({value})'
        # print(f'{rkey} <- {value}')

        r.setValue(rkey, value)

    return species_keys


def set_initial_concentrations(r, sid, value):
    return set_initial_values(r, sid, value, method="concentration")


def set_initial_amounts(r, sid, value):
    return set_initial_values(r, sid, value, method="amount")


# -----------------------------
# Dosing
# -----------------------------
class Dosing(object):
    def __init__(self, substance, route, dose, unit):
        self.substance = substance
        self.route = route
        self.dose = dose
        self.unit = unit

    def __repr__(self):
        return "{} [{}] {}".format(self.dose, self.unit, self.route)


def get_doses_keys():
    substances = SUBSTANCES_BODY.keys()
    return ['PODOSE_{}'.format(key) for key in substances] + ['IVDOSE_{}'.format(key) for key in substances]


def set_dosing(r, dosing, bodyweight=None, show=False):
    """ Sets dosing for simulation.

    Doses per bodyweight are scaled with given body weight, or body weight of the respective model.
    Doses are in the units of the dosing keys.
    """
    if dosing.route == "oral":
        pid = "PODOSE_{}".format(dosing.substance)
    elif dosing.route == "iv":
        pid = "IVDOSE_{}".format(dosing.substance)
    else:
        raise ValueError("Invalid dosing route: {}".format(dosing.route))

    # get dose in [mg]
    dose = dosing.dose
    if dosing.unit.endswith("kg"):
        if bodyweight is None:
            # use bodyweight from model
            bodyweight = r.BW
        dose = dose * bodyweight

    # reset the model
    r.reset()
    r.setValue('init({})'.format(pid), dose)  # set dose in [mg]
    r.reset(SelectionRecord.GLOBAL_PARAMETER)
    r.reset()

    if show:
        print_doses(r)


def print_doses(r, name=None):
    """ Prints the complete dose information of the model. """
    if name:
        print('***', name, '***')
    for key in get_doses_keys():
        print('{}\t{}'.format(key, r.getValue(key)))

def var_range(s, keys, unit="None"):
    if not isinstance(keys, (list, tuple)):
        keys = [keys]

    for key in keys:
        data = s[key]
        N = len(data)
        print(f"{key:<20} {data[0]:>5.3f} ... {data[N-1]:>5.3f} [{unit}]\t:\trange {data.min():>5.3f} - {data.max():>5.3f}")


# -------------------------------
# Plotting functions
# -------------------------------
def plot_body_concentrations(r, s):
    # full timecourse
    f, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(2, 4, figsize=(14, 8))
    f.subplots_adjust(wspace=.3, hspace=.3)
    axes = (ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8)
    for k, skey in enumerate(sorted(SUBSTANCES_BODY.keys())):
        ax, title = axes[k], skey
        time = s["time"]

        # print('skey', skey)
        species_keys = get_species_keys(skey, r.timeCourseSelections)
        for key in species_keys:
            # print('key', key)
            ckey = f'[{key}]'  # concentration
            # print('ckey', ckey)
            ax.plot(time, s[ckey], label=key)

        title = "Body: {}".format(title)
        ax.set_title(title)
        ax.set_ylabel('concentration [mM]')
        # ax.legend()

    for ax in axes:
        ax.set_xlabel('time [h]')
    # save_glc_fig(f, "glucose_distribution")

    plt.show()


def plot_body_fluxes(r, s):
    # full timecourse
    f, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(2, 4, figsize=(14, 8))
    f.subplots_adjust(wspace=.3, hspace=.3)
    axes = (ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8)
    for k, skey in enumerate(sorted(SUBSTANCES_BODY.keys())):
        ax, title = axes[k], skey
        time = s["time"]

        # print('skey', skey)
        species_keys = get_species_keys(skey, r.timeCourseSelections)

        reaction_keys = []
        for reaction_id in r.model.getReactionIds():
            # use regular expression
            # pattern = r'[A-Z]*[\_]*A[a-z]+(_blood)*\_{}'.format(sid)
            pattern = r'^Flow_[a-z\_]+\_{}$'.format(skey)
            match = re.search(pattern, reaction_id)
            if match:
                # print("match:", species_id)
                reaction_keys.append(reaction_id)

        for key in reaction_keys:
            ax.plot(time, s[key], label=key)

        title = "Body: {}".format(title)
        ax.set_title(title)
        ax.set_ylabel('flux [mmole/h]')
        # ax.legend()

    for ax in axes:
        ax.set_xlabel('time [h]')
    # save_glc_fig(f, "glucose_distribution")

    plt.show()


def plot_overview(r, s):
    """ Overview plot of whole-body glucose metabolism"""
    s_iter = s
    if not isinstance(s_iter, (list, dict)):
        s_iter = [s_iter]
    if isinstance(s_iter, dict):
        s_iter = s_iter.values()

    f, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(2, 4, figsize=(14, 8))
    f.subplots_adjust(wspace=.3, hspace=.3)
    axes = (ax1, ax2, ax3, ax4, ax5, ax6, ax7, ax8)

    for ax in (ax1, ax2, ax3, ax4):
        ax.set_ylabel('c [mmole/l]')

    for s in s_iter:
        ax1.set_title("Plama glucose")
        ax1.plot(s.time, s.Cve_glc, color="black")
        ax1.plot(s.time, s.Car_glc, color="black", linestyle="--")

        ax2.set_title("Plasma lactate")
        ax2.plot(s.time, s.Cve_lac, color="black")
        ax2.plot(s.time, s.Car_lac, color="black", linestyle="--")

        ax3.set_title("Plasma alanine")
        ax3.plot(s.time, s.Cve_ala, color="black")
        ax3.plot(s.time, s.Car_ala, color="black", linestyle="--")

        ax4.set_title("Plasma FFA")
        ax4.plot(s.time, s.Cve_ffa, color="black")
        ax4.plot(s.time, s.Car_ffa, color="black", linestyle="--")

    for ax in (ax5, ax6, ax8):
        ax.set_ylabel('c [pmole/l]')

    for ax in (ax7,):
        ax.set_ylabel('Glucagon/insulin [-]')

    for s in s_iter:
        ax5.set_title("Plasma Insulin")
        ax5.plot(s.time, s.Cve_ins * 1E6, color="black")
        ax5.plot(s.time, s.Car_ins * 1E6, color="black", linestyle="--")

        ax6.set_title("Plasma Glucagon")
        ax6.plot(s.time, s.Cve_glu * 1E6, color="black")
        ax6.plot(s.time, s.Car_glu * 1E6, color="black", linestyle="--")

        ax7.set_title("Plasma Glucagon/Insulin")
        ax7.plot(s.time, s.Cve_glu / s.Cve_ins, color="black")
        ax7.plot(s.time, s.Car_glu / s.Car_ins, color="black", linestyle="--")

        ax8.set_title("Epinephrine")
        ax8.plot(s.time, s.Cve_epi * 1E6, color="black")
        ax8.plot(s.time, s.Car_epi * 1E6, color="black", linestyle="--")

    for ax in axes:
        ax.legend()
        ax.set_xlabel('time [h]')
        ylim = ax.get_ylim()
        if ylim[0] > 0:
            ax.set_ylim(bottom=0)
        ax.set_ylim(bottom=0, top=1.1 * (ax.get_ylim()[1]))
    return f
