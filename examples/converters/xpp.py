"""Conversion of an XPP/XPPAUT ode file to SBML.

`sbmlutils.converters.xpp` converts the `.ode` files of
[XPP](http://www.math.pitt.edu/~bard/xpp/xpp.html) to SBML. The example
converts one of the packaged ode files, simulates the resulting model with
roadrunner and plots the time courses.

Run it from the root of the repository:

```bash
python -m examples.converters.xpp
```

The model and the figure are written into the current working directory.
"""

import logging
from pathlib import Path

import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Figure

from sbmlutils.converters import xpp
from sbmlutils.resources import TESTDATA_DIR


logger = logging.getLogger(__name__)

#: the packaged ode files, see `sbmlutils.resources`
XPP_DIR: Path = TESTDATA_DIR / "xpp"


def example(model_id: str, output_dir: Path) -> Figure:
    """Convert an ode file to SBML and simulate the model.

    Args:
        model_id: name of the ode file in `XPP_DIR`, without the suffix
        output_dir: directory the SBML model is written to

    Returns:
        The figure with the time courses, nothing is shown, so that the example
        does not open a window when it runs unattended.
    """
    xpp_file = XPP_DIR / f"{model_id}.ode"
    sbml_file = output_dir / f"{model_id}.xml"
    xpp.xpp2sbml(xpp_file=xpp_file, sbml_file=sbml_file)

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

    return fig


if __name__ == "__main__":
    output = Path.cwd()
    figure = example(model_id="PLoSCompBiol_Fig1", output_dir=output)
    figure_path = output / "PLoSCompBiol_Fig1.png"
    figure.savefig(figure_path, bbox_inches="tight")
    logger.info("Figure written to '%s'", figure_path)
