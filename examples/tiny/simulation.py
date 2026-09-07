"""ODE and FBA simulation of the tiny model.

The model is created with `examples.tiny.tiny`, simulated with roadrunner and,
if cobrapy is installed, optimized as a flux balance model.

Run it from the root of the repository:

```bash
python -m examples.tiny.simulation
```

The model and the figure are written into the current working directory. The
memote report of the model is created with

```bash
memote report snapshot --filename tiny_example_memote.html tiny_example.xml
```
"""

import logging
from pathlib import Path

import pandas as pd
import roadrunner
from matplotlib import pyplot as plt
from matplotlib.pyplot import Figure

from examples.tiny import tiny
from sbmlutils.console import console
from sbmlutils.fbc.cobra import cobra, read_cobra_model

logger = logging.getLogger(__name__)


def tiny_simulation(output_dir: Path) -> Figure:
    """Create the tiny model and simulate it.

    Args:
        output_dir: directory the model is written to

    Returns:
        The figure with the species and reaction time courses, nothing is
        shown, so that the example does not open a window when it runs
        unattended.
    """
    sbml_path = tiny.create(output_dir=output_dir).sbml_path

    r = roadrunner.RoadRunner(str(sbml_path))
    r.timeCourseSelections = [
        "time",
        *r.model.getBoundarySpeciesIds(),
        *r.model.getFloatingSpeciesIds(),
        *r.model.getReactionIds(),
        *r.model.getGlobalParameterIds(),
    ]
    r.timeCourseSelections += [f"[{key}]" for key in r.model.getFloatingSpeciesIds()]
    s = r.simulate(0, 400, steps=400)
    df = pd.DataFrame(s, columns=s.colnames)

    f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
    ax1.set_title("SBML species")
    ax1.plot(df.time, df["[glc]"])
    ax1.plot(df.time, df["[g6p]"])
    ax1.plot(df.time, df["[atp]"])
    ax1.plot(df.time, df["[adp]"])
    ax1.plot(df.time, df["a_sum"], color="grey", linestyle="--", label="[atp]+[adp]")
    ax1.set_ylabel("concentration [mmole/litre]=[mM]")

    ax2.set_title("SBML reactions")
    ax2.plot(df.time, 1e6 * df.GK)
    ax2.plot(df.time, 1e6 * df.ATPPROD)
    ax2.set_ylabel("reaction rate 1E-6[mmole/s]")

    for ax in (ax1, ax2):
        ax.legend()
        ax.set_xlabel("time [s]")

    if cobra is not None:
        fba_simulation(sbml_path)
    else:
        logger.warning("cobrapy is not installed, the fba simulation is skipped")

    return f


def fba_simulation(sbml_path: Path) -> None:
    """Optimize the model as a flux balance model with cobrapy.

    Args:
        sbml_path: the SBML model to optimize
    """
    model = read_cobra_model(sbml_path)
    console.print(model)

    console.rule("Reactions", style="white")
    for reaction in model.reactions:
        console.print(
            f"{reaction.id} : {reaction.reaction} "
            f"[{reaction.lower_bound}<->{reaction.upper_bound}]"
        )

    console.rule("Metabolites", style="white")
    for metabolite in model.metabolites:
        console.print(
            f"{metabolite.id:>9} ({metabolite.compartment}) : "
            f"{metabolite.formula}, {metabolite.charge}, {metabolite.annotation}"
        )

    console.rule("Genes", style="white")
    for gene in model.genes:
        associated_ids = ", ".join(reaction.id for reaction in gene.reactions)
        console.print(f"{gene.id} is associated with reactions: {{{associated_ids}}}")

    console.rule(style="white")
    console.print(model.optimize())


if __name__ == "__main__":
    output = Path.cwd()
    figure = tiny_simulation(output_dir=output)
    figure_path = output / f"{tiny.model.sid}_roadrunner.png"
    figure.savefig(figure_path, bbox_inches="tight")
    logger.info("Figure written to '%s'", figure_path)
