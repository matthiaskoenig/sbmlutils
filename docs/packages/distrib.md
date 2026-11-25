# Distributions and Uncertainties (distrib)

Distrib represents uncertainty in a model element and adds probability distributions to SBML formulas. Attach an uncertainty to preserve statistics reported with a fitted value. Use a distribution in an initial assignment to request that a compatible tool sample a starting value.

## Record a fitted estimate and define a random initial value

The fitted parameter carries its central value and standard deviation. A separate parameter draws a dimensionless perturbation from a zero-mean normal distribution during model initialization.

```python
from pathlib import Path

import libsbml

from sbmlutils.factory import (
    InitialAssignment,
    Model,
    Package,
    Parameter,
    UncertParameter,
    Uncertainty,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml

model = Model(
    sid="uncertain_fit",
    packages=[Package.DISTRIB_V1],
    parameters=[
        Parameter(
            "estimate",
            value=5.0,
            unit=Units.dimensionless,
            uncertainties=[
                Uncertainty(
                    uncertParameters=[
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
                            value=5.0,
                            unit=Units.dimensionless,
                        ),
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION,
                            value=0.3,
                            unit=Units.dimensionless,
                        ),
                    ]
                )
            ],
        ),
        Parameter("perturbation", value=0.0, unit=Units.dimensionless),
    ],
    assignments=[
        InitialAssignment("perturbation", "normal(0 dimensionless, 0.3 dimensionless)")
    ],
)
result = create_model(model, Path("uncertain_fit.xml"), raise_on_error=True)

doc = read_sbml(result.sbml_path)
sbml_model = doc.getModel()
plugin = sbml_model.getParameter("estimate").getPlugin("distrib")
assert plugin.getUncertainty(0).getNumUncertParameters() == 2
formula = sbml_model.getInitialAssignment(0).getMath()
assert (
    libsbml.formulaToL3String(formula) == "normal(0 dimensionless, 0.3 dimensionless)"
)
```

The uncertainty travels with `estimate` as metadata. Sampling the initial assignment requires a tool that evaluates distrib functions.

See [Distributions and uncertainties](../distrib.md) for spans, truncated distributions and round-trip support.
