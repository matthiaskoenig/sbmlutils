from pathlib import Path
from typing import Any

from libsedml import SedDocument
from matplotlib import pyplot as plt

import libopencor
import pandas as pd
from sbmlutils.console import console


def run_cellml_timecourse(cellml_path: Path) -> pd.DataFrame:
    """Runs cellml uniform timecourse"""
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
    simulation.output_start_time
    simulation.output_end_time
    simulation.number_of_steps = 1000

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
    voi = instance_task.voi  # variable of integration
    voi_name = instance_task.voi_name
    voi_unit = instance_task.voi_unit

    # access state variables
    # FIXME: how to get access to ids
    n_state = instance_task.state_count
    data_dict: dict[str, Any] = {}
    unit_dict: dict[str, str] = {}
    for k in range(n_state):
        name = instance_task.state_name(k)
        data = instance_task.state(k)
        unit = instance_task.state_unit(k)
        data_dict[name] = data
        unit_dict[name] = unit

    fig, ax = plt.subplots(nrows=1, ncols=1)
    for name, data in data_dict.items():
        ax.plot(voi, data, label=f"{name}[{unit_dict[name]}]")

    ax.set_xlabel(f"voi ({voi_name}) [{voi_unit}]")
    ax.set_ylabel('states')
    ax.legend()

    plt.show()


if __name__ == "__main__":
    run_cellml_timecourse(cellml_path="test_model.cellml")
