"""Drive a model with measured data, in place and through comp.

A model of glucose uptake has the plasma glucose `glc_ext` as a species. The
measured plasma glucose of `glucose_timecourse.tsv` drives it: once in place,
which changes the model, and once through a comp model, which leaves the model
untouched and holds the data on top of it. Both are simulated with roadrunner
and give the same result.

Run it from the root of the repository:

```bash
python -m examples.interpolation.driving
```

The models and the figure are written into the current working directory.
"""

import logging
from pathlib import Path

import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Axes, Figure

from sbmlutils.comp import flatten_sbml
from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import (
    Compartment,
    Model,
    Parameter,
    Reaction,
    Species,
    create_model,
)
from sbmlutils.validation import ValidationOptions

logger = logging.getLogger(__name__)

#: the measured plasma glucose, next to this module
DATA_PATH: Path = Path(__file__).parent / "glucose_timecourse.tsv"

#: glucose uptake from the plasma into the liver and its use there
model = Model(
    "uptake",
    name="glucose uptake",
    compartments=[Compartment("plasma", 1.0), Compartment("liver", 0.5)],
    species=[
        Species("glc_ext", initialConcentration=5.0, compartment="plasma"),
        Species("glc", initialConcentration=5.0, compartment="liver"),
    ],
    parameters=[
        Parameter("Vmax", 2.0),
        Parameter("Km", 5.0),
        Parameter("k_use", 0.2),
    ],
    reactions=[
        Reaction("GLCIM", "glc_ext -> glc", formula="Vmax * glc_ext / (Km + glc_ext)"),
        Reaction("GLCUSE", "glc -> ", formula="k_use * glc"),
    ],
)


def driving_example(directory: Path) -> Figure:
    """Drive the uptake model with the measured glucose, in place and via comp.

    Args:
        directory: where the models are written

    Returns:
        The figure of the data and both simulations; nothing is shown, so
        that the example does not open a window when it runs unattended.
    """
    model_path = directory / "uptake.xml"
    create_model(
        model,
        filepath=model_path,
        validation_options=ValidationOptions(units_consistency=False),
    )
    interpolation = Interpolation.from_tsv(DATA_PATH, method="cubic spline")

    # (A) in place: the model itself is changed, glc_ext follows the data
    in_place = directory / "uptake_driven.xml"
    interpolation.drive(model_path, filepath=in_place)

    # (B) comp: a model on top of the untouched original, flattened to simulate
    comp = directory / "uptake_driven_comp.xml"
    interpolation.drive_comp(model_path, filepath=comp)
    flat = directory / "uptake_driven_flat.xml"
    flatten_sbml(comp, flat)

    data = interpolation.data
    f: Figure
    ax: Axes
    f, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(data["time"], data["glc_ext"], "o", color="black", label="glc_ext data")
    # the elements of the original are prefixed with the submodel after
    # flattening; in place is drawn wide and light, comp dashed on top of it,
    # so that both are visible where they agree
    for path, glc, label, linewidth, alpha, linestyle in [
        (in_place, "[glc]", "in place", 4.0, 0.35, "-"),
        (flat, "[uptake__glc]", "comp", 1.5, 1.0, "--"),
    ]:
        r = roadrunner.RoadRunner(str(path))
        s = r.simulate(0, 240, 241, selections=["time", "[glc_ext]", glc])
        for sid, color in [("[glc_ext]", "tab:blue"), (glc, "tab:red")]:
            ax.plot(
                s["time"],
                s[sid],
                color=color,
                linewidth=linewidth,
                alpha=alpha,
                linestyle=linestyle,
                label=f"{sid.strip('[]').removeprefix('uptake__')} {label}",
            )
    ax.set_xlabel("time [min]")
    ax.set_ylabel("glucose [mM]")
    ax.set_title("Glucose uptake driven by measured plasma glucose")
    ax.legend()
    return f


if __name__ == "__main__":
    from sbmlutils import log

    log.enable_rich_logging()

    figure = driving_example(Path.cwd())
    figure_path = Path.cwd() / "driving.png"
    figure.savefig(figure_path, bbox_inches="tight", dpi=150)
    logger.info("Figure written to '%s'", figure_path)
