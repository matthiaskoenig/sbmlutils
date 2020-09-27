
import os
import roadrunner
from roadrunner import SelectionRecord
from collections import namedtuple
import pandas as pd
import numpy as np
import pandas as pd
import matplotlib
from matplotlib import pyplot as plt
import pylimax
from IPython.display import display
from os.path import join as pjoin

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

# consistent plotting styles
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
kwargs_data = {'marker': 's', 'linestyle': '--', 'linewidth': 1, 'capsize': 3}
kwargs_sim = {'marker': None, 'linestyle': '-', 'linewidth': 2}

substances = ["gal"]
titles = ["galactose"]
color_codes = {'gal': 'black'}
doses_keys = ['PODOSE_{}'.format(key) for key in substances] + ['IVDOSE_{}'.format(key) for key in substances]


class Dosing(object):
    def __init__(self, substance, route, dose, unit):
        self.substance = substance
        self.route = route
        self.dose = dose
        self.unit = unit

    def __repr__(self):
        return "{} [{}] {}".format(self.dose, self.unit, self.route)


def get_color(key, codes=color_codes, default="grey"):
    """ Get color for given substance key"""
    return codes.get(key, default)


def load_model(info=True):
    """ Loads the latest model version. """

    model_path = get_model_path()
    if info:
        print('Model:', model_path)

    r = roadrunner.RoadRunner(model_path)
    set_selections(r)
    return r

def get_model_path():
    """ Model path of latest LiMAx model."""
    from pylimax.models.galactose_pkpd import model_factory
    from pylimax.models.galactose_pkpd.galactose_pkpd_model import mid, version

    # latest model version
    return os.path.join(model_factory.target_dir, '{}_{}.xml'.format(mid, version))


def set_selections(r):
    """ Sets the full model selections. """
    r.timeCourseSelections = ["time"] + r.model.getFloatingSpeciesIds() + r.model.getGlobalParameterIds()

Result = namedtuple("Result", ['base', 'mean', 'std', 'min', 'max'])

def simulate(r, tend, steps, dosing, changes={}, parameters=None, sensitivity=0.1, selections=None, yfun=None):
    """ Performs model simulation simulation with option on fallback.

    Does not support changes to the model yet.
    """
    # set selections
    if selections == None:
        set_selections(r)
    else:
        r.timeCourseSelections = selections

    if changes is None:
        changes = {}

    # reset all
    resetAll(r)
    reset_doses(r)

    # get bodyweight
    if "BW" in changes:
        bodyweight = changes["BW"]
    else:
        bodyweight = r.BW

    # dosing
    if dosing:
        set_dosing(r, dosing, bodyweight=bodyweight)

    # general changes
    for key, value in changes.items():
        r[key] = value
    s = r.simulate(start=0, end=tend, steps=steps)
    s_base = pd.DataFrame(s, columns=s.colnames)

    if yfun:
        # conversion functio
        yfun(s_base)


    if parameters is None:
        return s_base
    else:
        # baseline
        Np = 2 * len(parameters)
        (Nt, Ns) = s_base.shape
        shape = (Nt, Ns, Np)

        # empty array for storage
        s_data = np.empty(shape) * np.nan

        # all parameter changes
        idx = 0
        for pid in parameters.keys():
            for change in [1.0 + sensitivity, 1.0 - sensitivity]:
                resetAll(r)
                reset_doses(r)
                # dosing
                if dosing:
                    set_dosing(r, dosing, bodyweight=bodyweight)
                # general changes
                for key, value in changes.items():
                    r[key] = value
                # parameter changes
                value = r[pid]
                new_value = value * change
                r[pid] = new_value

                s = r.simulate(start=0, end=tend, steps=steps)
                if yfun:
                    # conversion function
                    s = pd.DataFrame(s, columns=s.colnames)
                    yfun(s)
                    s_data[:, :, idx] = s
                else:
                    s_data[:, :, idx] = s
                idx += 1

        s_mean = pd.DataFrame(np.mean(s_data, axis=2), columns=s_base.columns)
        s_std = pd.DataFrame(np.std(s_data, axis=2), columns=s_base.columns)
        s_min = pd.DataFrame(np.min(s_data, axis=2), columns=s_base.columns)
        s_max = pd.DataFrame(np.max(s_data, axis=2), columns=s_base.columns)

        # return {'base': s_base, 'mean': s_mean, 'std': s_std, 'min': s_min, 'max': s_max}
        return Result(base=s_base, mean=s_mean, std=s_std, min=s_min, max=s_max)


def add_line(xid, yid, ax, s, color='black', label='', xf=1.0):
    """

    :param xid:
    :param yid:
    :param ax:
    :param s: namedtuple Result from simulate
    :param color:
    :return:
    """
    x = s.mean[xid]*xf

    ax.fill_between(x, s.min[yid], s.mean[yid] - s.std[yid], color=color, alpha=0.3, label="__nolabel__")
    ax.fill_between(x, s.mean[yid] + s.std[yid], s.max[yid], color=color, alpha=0.3, label="__nolabel__")
    ax.fill_between(x, s.mean[yid] - s.std[yid], s.mean[yid] + s.std[yid], color=color, alpha=0.5, label="__nolabel__")

    ax.plot(x, s.mean[yid], '-', color=color, label="sim {}".format(label), **kwargs_sim)


def resetAll(r):
    """ Reset all model variables to CURRENT init(X) values.

    This resets all variables, S1, S2 etc to the CURRENT init(X) values. It also resets all
    parameters back to the values they had when the model was first loaded.
    """
    r.reset(roadrunner.SelectionRecord.TIME |
            roadrunner.SelectionRecord.RATE |
            roadrunner.SelectionRecord.FLOATING |
            roadrunner.SelectionRecord.GLOBAL_PARAMETER)


def set_dosing(r, dosing, bodyweight=None, show=False):
    """ Sets dosing for simulation. """
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
            bodyweight = r.BW
        dose = dose * bodyweight

    # reset the model
    r.reset()
    reset_doses(r)
    r.setValue('init({})'.format(pid), dose)  # set dose in [mg]
    r.reset(SelectionRecord.GLOBAL_PARAMETER)
    r.reset()
    # r.resetAll()?
    if show:
        print_doses(r)


def reset_doses(r):
    """ Sets all doses to zero. """
    for key in doses_keys:
        r.setValue('init({})'.format(key), 0)  # [mg]
    r.reset(SelectionRecord.GLOBAL_PARAMETER)
    r.reset()


def print_doses(r, name=None):
    """ Prints the complete dose information of the model. """
    if name:
        print('***', name, '***')
    for key in doses_keys:
        print('{}\t{}'.format(key, r.getValue(key)))


def parameters_for_sensitivity(r):
    """ Get the parameter ids for the sensitivity analysis.

    This includes all constant parameters (not changed via assignments),
    excluding
    - parameters with value=0 (no effect on model, dummy parameter)
    - parameters which are physical constants, e.g., molecular weights
    """
    model_path = get_model_path()
    try:
        import tesbml as libsbml
    except ImportError:
        import libsbml

    doc = libsbml.readSBMLFromFile(model_path)
    model = doc.getModel()

    # constant parameters in model
    pids_const = []
    for p in model.getListOfParameters():
        if p.getConstant() == True:
            pids_const.append(p.getId())

    # print('constant parameters:', len(pids_const))

    # filter parameters
    parameters = {}
    for pid in pids_const:
        # dose parameters
        if (pid.startswith("IVDOSE_")) or (pid.startswith("PODOSE_")):
            continue

        # physical parameters
        if (pid.startswith("Mr_")) or pid in ["R_PDB"]:
            continue

        # zero parameters
        value = r[pid]
        if np.abs(value) < 1E-8:
            continue

        parameters[pid] = value

    return parameters

# ----------------------------------
# Overview plots
# ----------------------------------

def plot_limax_results(s, name=None):
    # full timecourse
    f, ((ax1, ax2, ax3)) = plt.subplots(1, 3, figsize=(12, 4))
    f.subplots_adjust(wspace=.3)
    axes = (ax1, ax2, ax3)
    for k, skey in enumerate(substances):
        ax, title = axes[k], titles[k]
        time = s["time"]
        ax.plot(time, s['Cli_{}'.format(skey)], label='{} liver'.format(skey), color='black', linestyle="--")
        ax.plot(time, s['Cve_{}'.format(skey)], label='{} venous blood'.format(skey), color='blue', linewidth=2.0)
        ax.plot(time, s['Clu_{}'.format(skey)], label='{} lung'.format(skey), color='red', linewidth=2.0)

        if name is not None:
            title = "{} ({})".format(title, name)
        ax.set_title(title)
        ax.set_ylabel('concentration [mg/l]')
        ax.legend()

    for ax in axes:
        ax.set_xlabel('time [h]')
    plt.show()


def plot_bicarbonate(s, name=None):
    """ Plot the important bicarbonate values of the models.

    Includes concentrations in the main compartments and the respective
    ratios of C13-CO2, C12-CO2 and DOB curves.
    """
    f, ((ax1, ax2, ax3)) = plt.subplots(1, 3, figsize=(12, 4))
    f.subplots_adjust(wspace=.3, hspace=0.3)
    axes = (ax1, ax2, ax3)

    if isinstance(s, list):
        siter = s
    else:
        siter = [s]

    for s in siter:
        time = s["time"] * 60

        # bicarbonate kinetics in body
        skey = "co2c13"
        ax1.plot(time, s['Cli_{}'.format(skey)], label='{} liver'.format(skey), color='black', linestyle="--")
        ax1.plot(time, s['Cve_{}'.format(skey)], label='{} venous blood'.format(skey), color='blue', linewidth=2.0)
        ax1.plot(time, s['Clu_{}'.format(skey)], label='{} lung'.format(skey), color='red', linewidth=2.0)
        ax1.set_title("Concentration ({})".format(name))
        ax1.set_ylabel('concentration [mg/l]')

        # Contributions of
        ax2.plot(time, s['v_VCO2R'], label='13CO2/12CO2', color='black')
        ax2.plot(time, s['v_VCO2Fc13'], label='13CO2/(13CO2 + 12CO2)', color='blue')
        ax2.set_title("C13/C12 ({})".format(name))

        # DOB values
        ax3.plot(time, s['DOB'], label='DOB', color='black')
        ax3.set_title("DOB ({})".format(name))

        for ax in axes:
            ax.set_xlabel('time [min]')
            ax.legend()
    plt.show()



def dob_average(time, values):
    """ Interpolate in second range, time must be provided in seconds. """
    tstart = int(np.ceil(time.iloc[0]))
    tend = int(np.floor(time.iloc[-1]))
    num = tend - tstart + 1
    time_inp = np.linspace(tstart, tend, num=num)
    values_inp = np.interp(time_inp, time, values)

    # calculating DOB average over 25 seconds by convolution
    cfilter = np.ones(shape=(25, 1))
    cfilter = cfilter[:, 0]
    values_av = np.convolve(values_inp, cfilter, mode='full')
    # By default, mode is ‘full’. This returns the convolution at each point of
    # overlap, with an output shape of (N+M-1,). At the end-points of the convolution,
    # the signals do not overlap completely, and boundary effects may be seen.
    values_av = values_av[0:len(time_inp)] / 25

    return time_inp, values_av