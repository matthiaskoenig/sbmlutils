from pathlib import Path
import roadrunner
import numpy as np


def simulate_distrib_roadrunner(sbml_path: Path, n_samples: int):
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
data_distrib_roadrunner = simulate_distrib_roadrunner("model_distrib.xml", n_samples=n_samples)
# unusable slow
data_distrib_roadrunner = simulate_distrib_roadrunner("model_binomial.xml",n_samples=n_samples)
