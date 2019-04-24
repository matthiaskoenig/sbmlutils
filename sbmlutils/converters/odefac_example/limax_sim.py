"""
Test scipy ode file.
"""
import os

import roadrunner
from roadrunner import SelectionRecord
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt

from scipy.integrate import odeint

in_dir = '.'
out_dir = './results'


def example_roadrunner(model_id):
    # ----------------------
    # roadrunner simulation
    # ----------------------
    # load the model
    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))
    r = roadrunner.RoadRunner(sbml_file)
    r.timeCourseSelections = ["time"] + r.model.getFloatingSpeciesIds() + r.model.getGlobalParameterIds() + ['Exhalation_co2c13']

    # ---------------------
    # apap_simulation
    # ---------------------
    r.reset()
    r.setValue('init(PODOSE_apap)', 5600)  # set dose in [mg]: 80 [mg/kg] * 70 [kg]
    r.reset(SelectionRecord.GLOBAL_PARAMETER)
    r.reset()
    s = r.simulate(start=0, end=24, steps=300)
    s = pd.DataFrame(s, columns=s.colnames)

    # plot results
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time, s.Mve_apap, color="black", label="APAP roadrunner")
    ax1.set_ylabel('Paracetamol [mg/l]')

    for ax in (ax1,):
        ax.set_title(model_id)
        ax.set_xlabel('time [h]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "{}_apap_roadrunner.png".format(model_id)), dpi=300, bbox_inches="tight")
    plt.show()

    # ---------------------
    # bicarbonate_simulation
    # ---------------------
    r.resetToOrigin()
    r.reset()
    r.setValue('init(IVDOSE_co2c13)', 46.5)
    r.reset(SelectionRecord.GLOBAL_PARAMETER)
    r.reset()
    s = r.simulate(start=0, end=5, steps=500)
    s = pd.DataFrame(s, columns=s.colnames)

    # plot results
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time*60, s.DOB, color="black", label="bicarbonate roadrunner")
    ax1.set_ylabel('DOB []')

    for ax in (ax1,):
        ax.set_title(model_id)
        ax.set_xlabel('time [min]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "{}_bicarbonate_roadrunner.png".format(model_id)), dpi=300, bbox_inches="tight")
    plt.show()

    # ---------------------
    # MBT_simulation
    # ---------------------
    r.resetToOrigin()
    r.reset()
    dose_metc13 = 75  # [mg]
    r.setValue('init(PODOSE_metc13)', dose_metc13)
    r.reset(SelectionRecord.GLOBAL_PARAMETER)
    r.reset()
    s = r.simulate(start=0, end=2.5, steps=300)
    s = pd.DataFrame(s, columns=s.colnames)

    recovery = s.Exhalation_co2c13 / (dose_metc13/s.Mr_metc13) * 100  # [% dose/h] momentary recovery
    cum = s.Abreath_co2c13 / (dose_metc13 / s.Mr_metc13) * 100  # [% dose] cummulative recovery

    # plot results
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time*60, recovery, color="black", label="mom recovery roadrunner")
    ax1.set_ylabel('Momentary 13C recovery [% dose]')

    ax2.plot(s.time*60, cum, color="black", label="cum recovery roadrunner")
    ax2.set_ylabel('Cummulative 13C recovery [% dose]')

    for ax in (ax1, ax2):
        ax.set_title(model_id)
        ax.set_xlabel('time [min]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "{}_mbt_roadrunner.png".format(model_id)), dpi=300, bbox_inches="tight")
    plt.show()


def example_scipy(model_id):

    # ----------------------
    # import odes
    # ----------------------
    py_file = os.path.join(in_dir, "{}.py".format(model_id))
    from importlib.machinery import SourceFileLoader
    ode = SourceFileLoader("module.name", py_file).load_module()

    # ----------------------
    # APAP simulation
    # ----------------------
    # Simulation time
    T = np.arange(0, 24, 0.01)

    x0 = np.empty_like(ode.x0)
    x0[:] = ode.x0
    p = np.empty_like(ode.p)
    p[:] = ode.p

    # set PODOSE_apap
    x0[ode.xids.index("PODOSE_apap")] = 5600

    # Integration
    X = odeint(ode.f_dxdt, x0, T, args=(p, ))
    # Solution DataFrame
    s = ode.f_z(X, T, p)

    # plot results
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time, s.Mve_apap, color="black", label="scipy")
    ax1.set_ylabel('Paracetamol [mg/l]')

    for ax in (ax1,):
        ax.set_title(model_id)
        ax.set_xlabel('time [h]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "{}_apap_scipy.png".format(model_id)), dpi=300, bbox_inches="tight")
    plt.show()

    # ----------------------
    # bicarbonate simulation
    # ----------------------
    T = np.arange(0, 5, 0.01)

    # Change parameters & initial amount/concentration (in copy)
    x0 = np.empty_like(ode.x0)
    x0[:] = ode.x0
    p = np.empty_like(ode.p)
    p[:] = ode.p

    # set PODOSE_apap
    x0[ode.xids.index("IVDOSE_co2c13")] = 46.5

    # Integration
    X = odeint(ode.f_dxdt, x0, T, args=(p,))
    # Solution DataFrame
    s = ode.f_z(X, T, p)

    # plot results
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time*60, s.DOB, color="black", label="bicarbonate scipy")
    ax1.set_ylabel('DOB []')

    for ax in (ax1,):
        ax.set_title(model_id)
        ax.set_xlabel('time [min]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "{}_bicarbonate_scipy.png".format(model_id)), dpi=300, bbox_inches="tight")
    plt.show()

    # ----------------------
    # MBT simulation
    # ----------------------
    # Simulation time
    T = np.arange(0, 2.5, 0.01)

    # Change parameters & initial amount/concentration (in copy)
    x0 = np.empty_like(ode.x0)
    x0[:] = ode.x0
    p = np.empty_like(ode.p)
    p[:] = ode.p

    # set PODOSE_apap
    dose_metc13 = 75
    x0[ode.xids.index("PODOSE_metc13")] = dose_metc13

    # Integration
    X = odeint(ode.f_dxdt, x0, T, args=(p, ))
    # Solution DataFrame
    s = ode.f_z(X, T, p)

    print(ode.pids)
    Mr_metc13 = ode.p[ode.pids.index("Mr_metc13")]
    recovery = s.Exhalation_co2c13 / (dose_metc13 / Mr_metc13) * 100  # [% dose/h] momentary recovery
    cum = s.Abreath_co2c13 / (dose_metc13 / Mr_metc13) * 100  # [% dose] cummulative recovery

    # plot results
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time*60, recovery, color="black", label="mom recovery scipy")
    ax1.set_ylabel('Momentary 13C recovery [% dose]')

    ax2.plot(s.time*60, cum, color="black", label="cum recovery scipy")
    ax2.set_ylabel('Cummulative 13C recovery [% dose]')

    for ax in (ax1, ax2):
        ax.set_title(model_id)
        ax.set_xlabel('time [min]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "{}_mbt_scipy.png".format(model_id)), dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    model_id = "limax_pkpd_v50"
    example_roadrunner(model_id)
    example_scipy(model_id)
