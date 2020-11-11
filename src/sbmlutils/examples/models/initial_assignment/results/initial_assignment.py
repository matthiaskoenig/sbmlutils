from pathlib import Path

import pandas as pd
import roadrunner
from matplotlib import pyplot as plt


def plot_results(s: pd.DataFrame, title=None) -> None:
    fig = plt.figure()
    ax = fig.gca()
    ax.plot(s.time, s.A1, label="A1")
    ax.legend()
    ax.set_title(title)
    ax.set_ylabel("amount")
    ax.set_xlabel("time")
    plt.show()


if __name__ == "__main__":
    model_path = str(Path(__file__).parent / "initial_assignment.xml")

    # default simulations
    r = roadrunner.RoadRunner(model_path)  # type: roadrunner.ExecutableModel
    r.selections = (
        ["time"]
        + r.model.getGlobalParameterIds()
        + r.model.getFloatingSpeciesIds()
        + [f"[{key}]" for key in r.model.getFloatingSpeciesIds()]
    )
    s = r.simulate(0, 10, 100)
    s = pd.DataFrame(s, columns=s.colnames)

    # change of parameter before simulation
    r2 = roadrunner.RoadRunner(str(model_path))  # type: roadrunner.ExecutableModel
    r2.selections = (
        ["time"]
        + r2.model.getGlobalParameterIds()
        + r2.model.getFloatingSpeciesIds()
        + [f"[{key}]" for key in r2.model.getFloatingSpeciesIds()]
    )
    r2[
        "D"
    ] = 10  # ! InitialAssignment must be recalculated according to SBML specification !
    # FIXME: or at least a manual reevaluation of InitialAssignments must be possible !
    s2 = r.simulate(0, 10, 100)
    s2 = pd.DataFrame(s2, columns=s2.colnames)
    # A1 is 10, but should be 20

    plot_results(s, title="s")
    plot_results(s2, title="s2")
