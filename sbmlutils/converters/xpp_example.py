"""
Test xpp file
"""
from __future__ import print_function, absolute_import
import os
from sbmlutils.report import sbmlreport
from sbmlutils.converters import xpp
import roadrunner
from matplotlib import pyplot as plt

def example0():
    # convert xpp to sbml
    out_dir = './xpp_example'
    model_id = "SkM_AP_KCa"
    xpp_file = os.path.join(out_dir, "{}.ode".format(model_id))
    sbml_file = os.path.join(out_dir, "{}.xml".format(model_id))
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
    sbmlreport.create_sbml_report(sbml_file, out_dir=out_dir, validate=False)

    # test simulation
    r = roadrunner.RoadRunner(sbml_file)
    s = r.simulate(start=0, end=1000, steps=100)


def example1():
    # convert xpp to sbml
    out_dir = './xpp_example'
    xpp_file = os.path.join(out_dir, "PLoSCompBiol_Fig1.ode")
    sbml_file = os.path.join(out_dir, "PLoSCompBiol_Fig1.xml")
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
    sbmlreport.create_sbml_report(sbml_file, out_dir=out_dir, validate=False)

    # test simulation
    r = roadrunner.RoadRunner(sbml_file)
    s = r.simulate(start=0, end=1000, steps=100)

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 7))
    axes = (ax1, ax2)

    for ax in axes:
        for sid in r.timeCourseSelections[1:]:
            ax.plot(s['time'], s[sid], label=sid)
    ax2.set_yscale('log')
    for ax in axes:
        ax.set_ylabel('Value [?]')
        ax.set_xlabel('Time [?]')
        ax.legend()

    fig.savefig(os.path.join(out_dir, "PLoSCompBiol_Fig1.png"),
                bbox_inches='tight')


if __name__ == "__main__":
    example0()
    example1()




