"""
Runs ODE and FBA simulation with the model.

memote model report can be generated via:
memote report snapshot --filename tiny_example_10_memote.html tiny_example_10.xml

Requires the cobra functionality

"""
from pathlib import Path

import pandas as pd
import roadrunner
from matplotlib import pylab as plt

from sbmlutils.examples.tiny_model import factory as tiny_factory
from sbmlutils.examples.tiny_model.model import tiny_model
from sbmlutils.fbc.cobra import read_cobra_model


def tiny_simulation() -> None:
    """Analysis of the tiny model.

    Creates model and runs simulation.
    """
    # -----------------------------------------------------------------------------
    # create model
    # -----------------------------------------------------------------------------
    factory_result = tiny_factory.create()

    # -----------------------------------------------------------------------------
    # run ode simulation
    # -----------------------------------------------------------------------------
    # tiny_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
    #                         'results',
    #                         '{}_{}.xml'.format(model.mid, model.version))

    tiny_dir = Path(__file__).parent
    r = roadrunner.RoadRunner(str(factory_result.sbml_path))
    r.timeCourseSelections = (
        ["time"]
        + r.model.getBoundarySpeciesIds()
        + r.model.getFloatingSpeciesIds()
        + r.model.getReactionIds()
        + r.model.getGlobalParameterIds()
    )
    r.timeCourseSelections += [
        "[{}]".format(key) for key in r.model.getFloatingSpeciesIds()
    ]
    # print(r)
    s = r.simulate(0, 400, steps=400)
    df = pd.DataFrame(s, columns=s.colnames)
    # r.plot()

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

    plt.show()
    f.savefig(
        tiny_dir / "results" / f"{tiny_model.sid}_roadrunner.png",
        bbox_inches="tight",
    )

    # -----------------------------------------------------------------------------
    # fba simulation
    # -----------------------------------------------------------------------------
    model = read_cobra_model(factory_result.sbml_path)
    print(model)

    # Iterate through the the objects in the model
    print("Reactions")
    print("---------")
    for x in model.reactions:
        print("%s : %s [%s<->%s]" % (x.id, x.reaction, x.lower_bound, x.upper_bound))

    print("")
    print("Metabolites")
    print("-----------")
    for x in model.metabolites:
        print(
            "%9s (%s) : %s, %s, %s"
            % (x.id, x.compartment, x.formula, x.charge, x.annotation)
        )

    print("")
    print("Genes")
    print("-----")
    for x in model.genes:
        associated_ids = (i.id for i in x.reactions)
        print(
            "%s is associated with reactions: %s"
            % (x.id, "{" + ", ".join(associated_ids) + "}")
        )

    solution = model.optimize()
    print(solution)


if __name__ == "__main__":
    tiny_simulation()
