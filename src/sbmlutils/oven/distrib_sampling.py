"""Distrib example demonstrating distributions."""
from pathlib import Path

import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import roadrunner
from matplotlib.figure import Figure

from sbmlutils.utils import timeit


@timeit
def simulate_distrib_roadrunner(sbml_path: Path, n_samples: int) -> np.ndarray:
    """Sample the initial values."""
    r: roadrunner.RoadRunner = roadrunner.RoadRunner(str(sbml_path))
    model: roadrunner.ExecutableModel = r.model
    r.selections = model.getGlobalParameterIds()
    print(r.selections)
    data = np.zeros(shape=(n_samples, len(r.selections)))

    # sample & simulate using roadrunner distrib support
    for k in range(n_samples):
        r.resetToOrigin()
        _s = r.simulate(start=0, end=1, steps=1)
        data[k, :] = _s[0, :]

    return data


@timeit
def simulate_distrib_numpy(sbml_path: Path, n_samples: int) -> np.ndarray:
    """Sample the initial values."""
    r: roadrunner.RoadRunner = roadrunner.RoadRunner(str(sbml_path))
    model: roadrunner.ExecutableModel = r.model
    r.selections = model.getGlobalParameterIds()
    pid = r.selections[0]
    print(r.selections)
    data = np.zeros(shape=(n_samples, len(r.selections)))
    # sample & simulate using roadrunner distrib support
    for k in range(n_samples):
        r.resetToOrigin()
        # set parameter
        r.setValue(pid, np.random.normal(0, 1))
        _s = r.simulate(start=0, end=1, steps=1)
        data[k, :] = _s[0, :]

    return data


if __name__ == "__main__":
    # loading model once for fair caching in comparison
    roadrunner.RoadRunner(str("model_normal.xml"))
    roadrunner.RoadRunner(str("model_no_distrib.xml"))

    # compare normal distribution
    n_samples = 5000
    # model with normal
    data_normal_roadrunner = simulate_distrib_roadrunner(
        "model_normal.xml", n_samples=n_samples
    )
    data_normal_numpy = simulate_distrib_numpy("model_normal.xml", n_samples=n_samples)
    # model without distrib
    data_no_roadrunner = simulate_distrib_roadrunner(
        "model_no_distrib.xml", n_samples=n_samples
    )
    data_no_numpy = simulate_distrib_numpy("model_no_distrib.xml", n_samples=n_samples)

    # ---
    f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(ncols=2, nrows=2, figsize=(10, 10))
    hist_kwargs = {
        "alpha": 0.8,
        "color": "black",
        "bins": 20,
        "density": True,
    }
    ax1.hist(data_normal_roadrunner, **hist_kwargs)
    ax2.hist(data_normal_numpy, **hist_kwargs)
    ax3.hist(data_no_roadrunner, **hist_kwargs)
    ax4.hist(data_no_numpy, **hist_kwargs)

    ax1.set_title("roadrunner")
    ax2.set_title("numpy")
    plt.show()
    f.savefig("p_normal.png", bbox_inches="tight")
    # ---

    data_distrib_roadrunner = simulate_distrib_roadrunner(
        "model_distrib.xml", n_samples=n_samples
    )
    # data_distrib_roadrunner = simulate_distrib_roadrunner("model_binomial.xml",n_samples=n_samples)

    # create plots
    r: roadrunner.RoadRunner = roadrunner.RoadRunner("model_distrib.xml")
    model: roadrunner.ExecutableModel = r.model
    r.selections = model.getGlobalParameterIds()

    f, axs = plt.subplots(ncols=5, nrows=4, figsize=(15, 15), squeeze=False)
    axes = axs.reshape(-1)
    f.subplots_adjust(hspace=0.3, wspace=0.3)
    for kd, distribution in enumerate(r.selections):
        ax: matplotlib.axes.Axes = axes[kd]

        ax.hist(data_distrib_roadrunner[:, kd], **hist_kwargs)
        ax.set_title(f"{distribution}")
        ax.set_ylabel("Density")
        ax.set_xlabel("Value")
    plt.show()
    plt.savefig("distributions.png", bbox_inches="tight")
