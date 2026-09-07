"""Interpolation of data points as an SBML model.

`sbmlutils.data.interpolation` turns a table of data points into an SBML model
which evaluates the interpolation, so that the data can be used inside a
simulation. The example interpolates the same two data series with all three
methods and simulates the resulting models with roadrunner.

Run it from the root of the repository:

```bash
python -m examples.interpolation.interpolation
```

The figure is written into the current working directory.
"""

import logging
import tempfile
from pathlib import Path

import pandas as pd
import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Axes, Figure

from sbmlutils.data import interpolation as ip

logger = logging.getLogger(__name__)


def interpolation_example() -> Figure:
    """Interpolate two data series with all interpolation methods.

    Returns:
        The figure with the data points and the simulated interpolations. The
        caller closes it or writes it to a file, nothing is shown, so that the
        example does not open a window when it runs unattended.
    """
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
            tmp_f = Path(tmpdir, "interpolation.xml")

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
    return f


if __name__ == "__main__":
    fig = interpolation_example()
    fig_path = Path.cwd() / "interpolation.png"
    fig.savefig(fig_path, bbox_inches="tight", dpi=150)
    logger.info("Figure written to '%s'", fig_path)
