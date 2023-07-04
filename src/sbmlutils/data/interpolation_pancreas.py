"""Example demonstrating the interpolation of data."""
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Axes, Figure

from sbmlutils import log
from sbmlutils.data import interpolation as ip


logger = log.get_logger(__name__)


def interpolate_data(
    data: pd.DataFrame,
    xid: str,
    yid: str,
    xid_model: Optional[str] = None,
    yid_model: Optional[str] = None,
    title: Optional[str] = None,
) -> None:
    """Interpolate given data.yid ~ data.xid.

    Two main use cases:
    - interpolate timecourse data (added via a parameter and rule)
    - interpolate data dependencies (added via a parameter and rule)

    TODO: support units in formula creation.
    """
    x: np.ndarray = data[xid].values
    y: np.ndarray = data[yid].values

    data1 = pd.DataFrame({xid_model: x, yid_model: y})
    print(data1)

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
            print("-" * 80)
            print(f"*** {method}: {yid_model} ~ {xid_model}***")
            interpolators = interpolation.create_interpolators(
                data=data1, method=method
            )
            for interpolator in interpolators:
                print(interpolator.formula())

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
    plt.show()


if __name__ == "__main__":
    interpolate_data(
        data=pd.read_csv("atp_adp_mean.tsv", sep="\t"),
        xid="dose",
        yid="atp_adp",
        xid_model="glc",
        yid_model="atp_adp_total",
        title="Interpolation: atp_adp_mean",
    )

    # interpolate_data(
    #     data=pd.read_csv("atp_adp_normalized.tsv", sep="\t"),
    #     xid="dose", yid="atp_adp", xid_model="time", yid_model="atp_adp_total",
    #     title="Interpolation: atp_adp_normalized",
    # )
