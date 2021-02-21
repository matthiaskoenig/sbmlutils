"""Test xpp file."""
from pathlib import Path

import roadrunner
from matplotlib import pyplot as plt

from sbmlutils.converters import xpp
from sbmlutils.report import sbmlreport


def example(model_id: str) -> None:
    """XPP example conversion."""
    # convert xpp to sbml
    xpp_dir = Path(__file__).parent / "xpp_example"
    out_dir = xpp_dir / "results"

    xpp_file = xpp_dir / f"{model_id}.ode"
    sbml_file = out_dir / f"{model_id}.xml"
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)
    sbmlreport.create_report(sbml_file, output_dir=out_dir, validate=False)

    # test simulation
    r = roadrunner.RoadRunner(str(sbml_file))
    s = r.simulate(start=0, end=1000, steps=100)

    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(14, 7))
    axes = (ax1, ax2)

    for ax in axes:
        for sid in r.timeCourseSelections[1:]:
            ax.plot(s["time"], s[sid], label=sid)
    ax2.set_yscale("log")
    for ax in axes:
        ax.set_ylabel("Value [?]")
        ax.set_xlabel("Time [?]")
        ax.legend()

    fig.savefig(out_dir / f"{model_id}.png", bbox_inches="tight")


if __name__ == "__main__":
    # example(model_id="112836_HH-ext")
    # example(model_id="SkM_AP_KCa")
    example(model_id="PLoSCompBiol_Fig1")
