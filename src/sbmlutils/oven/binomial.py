"""Example for binomial distribution."""

from pathlib import Path

import numpy as np
import roadrunner


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


n_samples = 20
# fast
data_distrib_roadrunner = simulate_distrib_roadrunner(
    Path("model_distrib.xml"), n_samples=n_samples
)
# unusable slow
data_distrib_roadrunner = simulate_distrib_roadrunner(
    Path("model_binomial.xml"), n_samples=n_samples
)
