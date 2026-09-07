# Distributions and uncertainties

A parameter of a model is rarely a single number. It is a mean with a standard deviation, a range from the literature, or a value drawn from a distribution. The SBML [distrib](https://sbml.org/documents/specifications/level-3/version-1/distrib/) package records this next to the value instead of in a comment ([Smith *et al.* 2020](references.md#sbml-packages)).

## Uncertainty on an element

Every element accepts `uncertainties`, a list of `Uncertainty` objects. An uncertainty holds `UncertParameter` values (a mean, a standard deviation, a variance) and `UncertSpan` values (a range, a confidence interval):

```python
import libsbml

from sbmlutils.factory import (
    Model,
    Package,
    Parameter,
    UncertParameter,
    UncertSpan,
    Uncertainty,
)

model = Model(
    sid="uncertainty_example",
    packages=[Package.DISTRIB_V1],
    parameters=[
        Parameter(
            "p1",
            value=5.0,
            uncertainties=[
                Uncertainty(
                    sid="p1_uncertainty",
                    uncertParameters=[
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.0
                        ),
                        UncertParameter(
                            type=libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, value=0.3
                        ),
                    ],
                    uncertSpans=[
                        UncertSpan(
                            type=libsbml.DISTRIB_UNCERTTYPE_RANGE,
                            valueLower=2.0,
                            valueUpper=8.0,
                        ),
                    ],
                )
            ],
        ),
    ],
)
```

The types are the `libsbml.DISTRIB_UNCERTTYPE_*` constants: `MEAN`, `MEDIAN`, `STANDARDDEVIATION`, `VARIANCE`, `COEFFIACIENTOFVARIATION`, `SKEWNESS`, `RANGE`, `INTERQUARTILERANGE`, `CONFIDENCEINTERVAL`, `CREDIBLEINTERVAL`, `DISTRIBUTION` and `EXTERNALPARAMETER`.

An uncertainty also carries a definition URL, which is how a distribution from [ProbOnto](https://probonto.org) is referenced:

```python
UncertParameter(
    type=libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER,
    value=0.4,
    definitionURL="http://www.probonto.org/ontology#PROB_k0000789",
)
```

## Distributions in formulas

distrib also adds distribution functions to MathML, which are written in a formula like any other function:

```python
from sbmlutils.factory import InitialAssignment, Model, Package, Parameter

model = Model(
    sid="distrib_assignment",
    packages=[Package.DISTRIB_V1],
    parameters=[Parameter("p1", value=0.0)],
    assignments=[InitialAssignment("p1", "normal(0, 1)")],
)
```

The supported functions are `normal`, `uniform`, `bernoulli`, `binomial`, `cauchy`, `chisquare`, `exponential`, `gamma`, `laplace`, `lognormal`, `poisson` and `rayleigh`, with the truncated forms taking the bounds as additional arguments, e.g. `normal(0, 1, -2, 2)`.

The unit of the arguments matters as much as anywhere else, so a value with a unit is written as `normal(0 mM, 1 mM)`.

## Examples

- `examples/distrib/distrib_distributions.py` — every distribution function in an assignment
- `examples/distrib/distrib_uncertainties.py` — uncertainties on the elements of a model
- `examples/distrib/distrib_comp.py` — uncertainties in a hierarchical model
- `examples/distrib/distrib_packages_examples.py` — the raw libsbml distrib elements
