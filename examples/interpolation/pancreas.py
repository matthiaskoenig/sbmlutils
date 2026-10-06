"""Drive a dose response with measured pancreas data.

The measured ATP/ADP ratio of beta cells over the glucose dose of
`atp_adp_mean.tsv` drives the ATP/ADP ratio `atp_adp_total` of a model by its
glucose `glc`: x of the interpolation is a quantity of the model, not the time.
The model is driven with all three methods of `sbmlutils.data.interpolation`
and the dose response is scanned with roadrunner, a little beyond the data on
both sides, where the first and the last value are held.

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
from sbmlutils.factory import Model, Parameter, create_model
from sbmlutils.validation import ValidationOptions

logger = logging.getLogger(__name__)

#: the measured data, next to this module
DATA_DIR: Path = Path(__file__).parent


def interpolate_data(
    data: pd.DataFrame,
    xid: str,
    yid: str,
    xid_model: str,
    yid_model: str,
    title: str | None = None,
) -> Figure:
    """Drive `yid_model` of a model by `xid_model` with the data `yid ~ xid`.

    Args:
        data: the measured data
        xid: column of the independent variable
        yid: column of the dependent variable
        xid_model: identifier of the independent variable in the model
        yid_model: identifier of the dependent variable in the model
        title: title of the figure

    Returns:
        The figure with the data points and the driven dose responses,
        nothing is shown, so that the example does not open a window when it
        runs unattended.
    """
    x: np.ndarray = data[xid].to_numpy(dtype=float)
    y: np.ndarray = data[yid].to_numpy(dtype=float)
    data_model = pd.DataFrame({xid_model: x, yid_model: y})
    model = Model(
        "pancreas",
        parameters=[
            Parameter(xid_model, float(x[0])),
            Parameter(yid_model, 0.0, constant=False),
        ],
    )
    margin = 0.1 * (x.max() - x.min())
    xvec = np.linspace(x.min() - margin, x.max() + margin, num=100)

    f: Figure
    ax: Axes
    f, ax = plt.subplots(nrows=1, ncols=1)
    ax.set_xlabel(f"{xid_model} [AU]")
    ax.set_ylabel(f"{yid_model} [AU]")
    if title:
        ax.set_title(title)
    ax.plot(x, y, "o", color="black", label="data")

    colors = ["tab:red", "tab:green", "tab:blue"]
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "pancreas.xml"
        create_model(
            model,
            filepath=model_path,
            validation_options=ValidationOptions(units_consistency=False),
        )
        for k, method in enumerate(ip.InterpolationMethod):
            interpolation = ip.Interpolation(data=data_model, method=method)
            console.rule(f"{method}: {yid_model} ~ {xid_model}", style="white")
            for interpolator in interpolation.interpolators:
                console.print(interpolator.formula())

            driven = Path(tmpdir) / f"pancreas_{k}.xml"
            interpolation.drive(model_path, filepath=driven)
            r = roadrunner.RoadRunner(str(driven))
            yvec = np.zeros_like(xvec)
            for kv, xvalue in enumerate(xvec):
                # the assignment rule is evaluated when the value is read
                r[xid_model] = xvalue
                yvec[kv] = r[yid_model]
            ax.plot(xvec, yvec, label=f"{method}", color=colors[k])

    ax.legend()
    return f


if __name__ == "__main__":
    from sbmlutils import log

    log.enable_rich_logging()

    figure = interpolate_data(
        data=pd.read_csv(DATA_DIR / "atp_adp_mean.tsv", sep="\t"),
        xid="dose",
        yid="atp_adp",
        xid_model="glc",
        yid_model="atp_adp_total",
        title="ATP/ADP ratio driven by glucose: atp_adp_mean",
    )
    figure_path = Path.cwd() / "interpolation_pancreas.png"
    figure.savefig(figure_path, bbox_inches="tight", dpi=150)
    logger.info("Figure written to '%s'", figure_path)
