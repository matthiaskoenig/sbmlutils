"""Exmpample demonstrating the interpolation of data."""
import logging
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Axes, Figure

from sbmlutils.manipulation import interpolation as ip


logger = logging.getLogger(__name__)


def interpolation_example() -> None:
    """Demonstrate interpolation functionality."""
    x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    y = [0.0, 2.0, 1.0, 1.5, 2.5, 3.5]
    z = [10.0, 5.0, 2.5, 1.25, 0.6, 0.3]
    data1 = pd.DataFrame({"x": x, "y": y, "z": z})

    f: Figure
    ax1: Axes
    f, ax1 = plt.subplots(nrows=1, ncols=1)
    ax1.set_xlabel("time [AU]")
    ax1.set_ylabel("data [AU]")
    ax1.set_title("Interpolation Example")
    ax1.plot(x, y, "o", color="black", label="y")
    ax1.plot(x, z, "s", color="black", label="z")

    colors = ["red", "green", "blue"]
    for k, method in enumerate(
        [
            ip.INTERPOLATION_CONSTANT,
            ip.INTERPOLATION_LINEAR,
            ip.INTERPOLATION_CUBIC_SPLINE,
        ]
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_f = Path(tmpdir, "test.xml")

            interpolation = ip.Interpolation(data=data1, method=method)
            interpolation.write_sbml_to_file(tmp_f)

            r = roadrunner.RoadRunner(str(tmp_f))
            r.timeCourseSelections = ["time", "y", "z"]
            s = r.simulate(0, 5, steps=50)
            ax1.plot(s["time"], s["y"], label=f"y {method}", color=colors[k])
            ax1.plot(
                s["time"], s["z"], label=f"z {method}", color=colors[k], linestyle="--"
            )

    ax1.legend()
    plt.show()


if __name__ == "__main__":
    interpolation_example()
