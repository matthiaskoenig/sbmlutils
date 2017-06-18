"""
Test xpp file
"""
from __future__ import print_function, absolute_import
import os
from sbmlutils.report import sbmlreport
from sbmlutils.converters import xpp
import roadrunner
from matplotlib import pyplot as plt

def example(model_id):
    # convert xpp to sbml
    xpp_dir = './xpp_example'
    out_dir = './xpp_example/results'

    xpp_file = os.path.join(xpp_dir, "{}.ode".format(model_id))
    sbml_file = os.path.join(out_dir, "{}.xml".format(model_id))
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

    fig.savefig(os.path.join(out_dir, "{}.png".format(model_id)),
                bbox_inches='tight')


if __name__ == "__main__":
    example(model_id="112836_HH-ext")
    example(model_id="SkM_AP_KCa")
    example(model_id="PLoSCompBiol_Fig1")





