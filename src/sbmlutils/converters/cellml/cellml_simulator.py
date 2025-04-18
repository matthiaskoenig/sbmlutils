"""CellML simulator using libopencor."""

from pathlib import Path
from typing import Any, Tuple

from libsedml import SedDocument
from matplotlib import pyplot as plt

import libopencor
import pandas as pd
from sbmlutils.console import console


def plot_cellml_timecourse(df: pd.DataFrame, units: dict[str, str]) -> None:
    """Plot the results of the timecourse integration."""
    fig, ax = plt.subplots(nrows=1, ncols=1)
    columns = df.columns

    # independent variable
    voi_name = columns[0]
    voi = df[voi_name]

    # plot all dependent variables
    for name in columns[1:]:
        y = df[name]
        ax.plot(voi, y, label=f"{name}[{units[name]}]")

    ax.set_xlabel(f"voi ({voi_name}) [{units[voi_name]}]")
    ax.set_ylabel('states')
    ax.legend()

    plt.show()

def run_cellml_timecourse(cellml_path: Path, start: float=0, end: float = 100, steps: int = 100) -> Tuple[pd.DataFrame, dict[str, str]]:
    """Runs cellml uniform timecourse.

    Returns pandas data frame with the timecourse and a dictionary with the units.
    """
    # load model
    file = libopencor.File(str(cellml_path))
    if len(file.issues) != 0:
        console.print(file.issues[0].description)
    else:
        console.print('File: all good!')

    # SED-ML document
    document = libopencor.SedDocument(file)
    if len(document.issues) != 0:
        print(document.issues[0].description)
    else:
        print('Document: all good!')

    # Modify the timecourse settings of the simulation
    simulation: libopencor.SedUniformTimeCourse = libopencor.SedUniformTimeCourse(document)

    # FIXME: this is not working
    simulation.initial_time = start
    simulation.output_start_time = start
    simulation.output_end_time = end
    simulation.number_of_steps = steps

    instance: SedDocument = document.instantiate()
    if len(instance.issues) != 0:
        print(instance.issues[0].description)
    else:
        print('Instance: all good!')

    # run simulation based on simulation experiment description
    instance.run()
    if len(instance.issues) != 0:
        print(instance.issues[0].description)
    else:
        print('Instance running: all good!')

    # get access to task results
    instance_task: libopencor.SedInstanceTask = instance.tasks[0]

    # access to variable of integration
    voi: list[float] = instance_task.voi  # variable of integration
    voi_name = instance_task.voi_name
    voi_unit = instance_task.voi_unit

    # access state variables
    # FIXME: how to get access to ids
    n_state = instance_task.state_count
    data_dict: dict[str, Any] = {
        voi_name: voi,
    }
    units: dict[str, str] = {
        voi_name: voi_unit,
    }

    # add all the dependent variables
    for k in range(n_state):
        name = instance_task.state_name(k)
        data_dict[name] = instance_task.state(k)
        units[name] = instance_task.state_unit(k)

    return pd.DataFrame(data_dict), units


if __name__ == "__main__":
    # cellml_path="test_model.cellml"
    cellml_path = "glimepiride_kidney.cellml"

    # simulation
    df, units = run_cellml_timecourse(
        cellml_path=cellml_path,
        start=0,
        end=200,
        steps=20,
    )
    console.rule("results", style="white")
    console.print(df)
    console.rule(style="white")

    # plotting
    plot_cellml_timecourse(df=df, units=units)

