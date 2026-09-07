"""Interpolation of measured pancreas data as an SBML model.

The measured ATP/ADP ratios of `atp_adp_mean.tsv` are interpolated with all
three methods of `sbmlutils.data.interpolation` and the resulting models are
simulated with roadrunner.

Run it from the root of the repository:

```bash
python -m examples.interpolation.pancreas
```

The figure is written into the current working directory.
"""

import logging
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Axes, Figure

from sbmlutils.console import console
from sbmlutils.data import interpolation as ip

logger = logging.getLogger(__name__)

#: the measured data, next to this module
DATA_DIR: Path = Path(__file__).parent


def interpolate_data(
    data: pd.DataFrame,
    xid: str,
    yid: str,
    xid_model: str | None = None,
    yid_model: str | None = None,
    title: str | None = None,
) -> Figure:
    """Interpolate `data.yid ~ data.xid` and simulate the interpolation.

    Two main use cases:

    - interpolate timecourse data (added via a parameter and rule)
    - interpolate data dependencies (added via a parameter and rule)

    Args:
        data: the measured data
        xid: column of the independent variable
        yid: column of the dependent variable
        xid_model: identifier of the independent variable in the model
        yid_model: identifier of the dependent variable in the model
        title: title of the figure

    Returns:
        The figure with the data points and the simulated interpolations,
        nothing is shown, so that the example does not open a window when it
        runs unattended.
    """
    x: np.ndarray = data[xid].values
    y: np.ndarray = data[yid].values

    data1 = pd.DataFrame({xid_model: x, yid_model: y})

    # plot results
    f: Figure
    ax1: Axes
    f, ax1 = plt.subplots(nrows=1, ncols=1)
    ax1.set_xlabel(f"{xid_model} [AU]")
    ax1.set_ylabel(f"{yid_model} [AU]")
    if title:
        ax1.set_title(title)
    ax1.plot(x, y, "o", color="black", label="y")

    colors = ["tab:red", "tab:green", "tab:blue"]
    for k, method in enumerate(
        [
            ip.INTERPOLATION_CONSTANT,
            ip.INTERPOLATION_LINEAR,
            ip.INTERPOLATION_CUBIC_SPLINE,
        ]
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_f = Path(tmpdir, "tests.xml")

            interpolation = ip.Interpolation(data=data1, method=method)
            console.rule(f"{method}: {yid_model} ~ {xid_model}", style="white")
            interpolators = interpolation.create_interpolators(
                data=data1, method=method
            )
            for interpolator in interpolators:
                console.print(interpolator.formula())

            interpolation.write_sbml_to_file(tmp_f)

            r = roadrunner.RoadRunner(str(tmp_f))
            r.timeCourseSelections = [xid_model, yid_model]

            # timecourse
            if xid_model == "time":
                s = r.simulate(0, x.max(), steps=200)
                # plot interpolation
                ax1.plot(
                    s["time"],
                    s[yid_model],
                    label=f"{yid_model} {method}",
                    color=colors[k],
                )
                ax1.plot(
                    s["time"],
                    s[yid_model],
                    label=f"{yid_model} {method}",
                    color=colors[k],
                    linestyle="--",
                )

            # parameter scan
            else:
                xvec = np.linspace(start=np.min(x), stop=np.max(x), num=50)
                xvec_model = np.zeros_like(xvec)
                yvec_model = np.zeros_like(xvec)
                for kv, xvalue in enumerate(xvec):
                    r.resetAll()
                    r.setValue(xid_model, xvalue)
                    s = r.simulate(0, 1, steps=2)
                    df: pd.DataFrame = pd.DataFrame(s, columns=s.colnames)
                    xvec_model[kv] = df[xid_model].values[-1]
                    yvec_model[kv] = df[yid_model].values[-1]

                ax1.plot(
                    xvec_model,
                    yvec_model,
                    label=f"{yid_model} {method}",
                    color=colors[k],
                )
                ax1.plot(
                    xvec_model,
                    yvec_model,
                    label=f"{yid_model} {method}",
                    color=colors[k],
                    linestyle="--",
                )

    ax1.legend()
    return f


if __name__ == "__main__":
    figure = interpolate_data(
        data=pd.read_csv(DATA_DIR / "atp_adp_mean.tsv", sep="\t"),
        xid="dose",
        yid="atp_adp",
        xid_model="glc",
        yid_model="atp_adp_total",
        title="Interpolation: atp_adp_mean",
    )
    figure_path = Path.cwd() / "interpolation_pancreas.png"
    figure.savefig(figure_path, bbox_inches="tight", dpi=150)
    logger.info("Figure written to '%s'", figure_path)

    # interpolate_data(
    #     data=pd.read_csv("atp_adp_normalized.tsv", sep="\t"),
    #     xid="dose", yid="atp_adp", xid_model="time", yid_model="atp_adp_total",
    #     title="Interpolation: atp_adp_normalized",
    # )
