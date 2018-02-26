"""
Test scipy ode file.
"""
from __future__ import print_function, absolute_import
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
    r.timeCourseSelections = ["time"] + r.model.getFloatingSpeciesIds() + r.model.getGlobalParameterIds()

    # perform simulation
    r.reset()
    r.setValue('init(PODOSE_apap)', 5600)  # set dose in [mg]: 80 [mg/kg] * 70 [kg]
    r.reset(SelectionRecord.GLOBAL_PARAMETER)
    r.reset()

    s = r.simulate(start=0, end=24, steps=300)
    s = pd.DataFrame(s, columns=s.colnames)

    # ---------------------
    # plot results
    # ---------------------
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time, s.Mve_apap, color="black", label="roadrunner")
    ax1.set_ylabel('Paracetamol [mg/l]')

    for ax in (ax1,):
        ax.set_title(model_id)
        ax.set_xlabel('time [h]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "roadrunner.png"), dpi=300, bbox_inches="tight")
    plt.show()


def example_scipy(model_id):

    # ----------------------
    # import odes
    # ----------------------
    py_file = os.path.join(in_dir, "{}.py".format(model_id))
    from importlib.machinery import SourceFileLoader
    ode = SourceFileLoader("module.name", py_file).load_module()

    # ----------------------
    # scipy simulation
    # ----------------------
    # Simulation time
    T = np.arange(0, 24, 0.01)

    # Change parameters & initial amount/concentration (in copy)
    x0 = np.empty_like(ode.x0)
    x0[:] = ode.x0
    p = np.empty_like(ode.p)
    p[:] = ode.p

    # set PODOSE_apap
    x0[38] = 5600

    # Integration
    X = odeint(ode.f_dxdt, x0, T, args=(p, ))
    # Solution DataFrame
    s = ode.f_z(X, T, p)

    # ---------------------
    # plot results
    # ---------------------
    fig, (ax1) = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)
    ax1.plot(s.time, s.Mve_apap, color="black", label="scipy")
    ax1.set_ylabel('Paracetamol [mg/l]')

    for ax in (ax1,):
        ax.set_title(model_id)
        ax.set_xlabel('time [h]')
        ax.legend()
    fig.savefig(os.path.join(out_dir, "scipy.png"), dpi=300, bbox_inches="tight")
    plt.show()


if __name__ == "__main__":
    model_id = "limax_pkpd_39"
    example_roadrunner(model_id)
    example_scipy(model_id)





