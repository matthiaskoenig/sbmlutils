"""
Test scipy ode file.
"""
from __future__ import print_function, absolute_import
import os
from sbmlutils.report import sbmlreport
from sbmlutils.converters import xpp
import roadrunner
from roadrunner import SelectionRecord
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


def example_roadrunner(model_id):
    # convert xpp to sbml
    in_dir = './scipyode_example'
    out_dir = './scipyode_example/results'

    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))

    # ----------------------
    # roadrunner simulation
    # ----------------------
    # load the model
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
    # convert xpp to sbml
    in_dir = './scipyode_example'
    out_dir = './scipyode_example/results'

    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))

    # ----------------------
    # scipy simulation
    # ----------------------
    from scipy.integrate import odeint
    def simple_ode(x, t):

        # define parameters
        c = 1.0
        k = 2.0
        dxdt = c - k * x
        return dxdt

    # intital condition and timespan
    T = np.arange(0, 10, 0.1)
    X0 = 0
    X = odeint(simple_ode, X0, T)
    plt.plot(T, X, linewidth=2)
    plt.show()

    '''
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
    '''



if __name__ == "__main__":
    example_scipy("limax_pkpd_37")





