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

The types are the `libsbml.DISTRIB_UNCERTTYPE_*` constants. An `UncertParameter` takes the types of a single value, `MEAN`, `MEDIAN`, `MODE`, `STANDARDDEVIATION`, `STANDARDERROR`, `VARIANCE`, `COEFFIENTOFVARIATION`, `SKEWNESS`, `KURTOSIS`, `SAMPLESIZE`, `DISTRIBUTION` and `EXTERNALPARAMETER`; an `UncertSpan` takes the types of an interval, `RANGE`, `INTERQUARTILERANGE`, `CONFIDENCEINTERVAL` and `CREDIBLEINTERVAL`.

SBML holds the parameters and the spans of an uncertainty in one list, and `uncertParameters` is that list: it takes both kinds and writes them in the order they are given in. `uncertSpans` is the second way of writing the same thing, one list per kind, whose spans are written before `uncertParameters`.

An uncert parameter also carries a definition URL, which is how a distribution or a parameter of one from [ProbOnto](https://probonto.org) is referenced:

```python
UncertParameter(
    type=libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER,
    value=0.4,
    definitionURL="http://www.probonto.org/ontology#PROB_k0000789",
)
```

An external distribution states its own parameters as `uncertParameters` of the uncert parameter which names it, and a distribution of distrib states itself as `math`:

```python
UncertParameter(
    type=libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
    definitionURL="http://www.sbml.org/sbml/symbols/distrib/normal",
    math="normal(1 mole, 3 mole)",
)
```

An `Uncertainty`, an `UncertParameter` and an `UncertSpan` are elements of the model like any other, so each carries its own `sid`, `name`, `metaId`, `sboTerm`, notes and annotations:

```python
UncertParameter(
    type=libsbml.DISTRIB_UNCERTTYPE_MEAN,
    value=5.0,
    sid="p1_mean",
    name="mean of p1",
    metaId="meta_p1_mean",
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

## What round trips

`sbml_to_model` reads the distrib content of a document, so a model with uncertainties can be read, changed in python and written back, see [Reading and writing](io.md#the-packages):

| Construct | After a round trip |
| --- | --- |
| the uncertainties of an element | preserved, in the order of the document |
| uncert parameters and spans | preserved, in the order of the document, with type, value, variable, bounds and unit |
| `definitionURL`, `math` and the nested parameters of a distribution | preserved |
| the metadata of an uncertainty, a parameter and a span | preserved |
| a distribution in a formula, e.g. `normal(0, 1)` | preserved |

SBML lets every element carry an uncertainty, and a few of them have no `uncertainties` in a python model definition: the model itself, a unit definition, a species reference, a key-value pair, and an uncertainty or one of its children. Such an uncertainty is reported while the file is read, where the element is still known, rather than being dropped in silence.

The SBML test suite has no distrib case at all, so the round trip of distrib is verified on the files of this repository under `resources/distrib/` and `resources/examples/`. Those were written to show what `sbmlutils` can express, so they test what their authors already believed; a distrib construct which no file of the repository uses is not covered by a measurement.

## Examples

- `examples/distrib/distrib_distributions.py` - every distribution function in an assignment
- `examples/distrib/distrib_uncertainties.py` - uncertainties on the elements of a model
- `examples/distrib/distrib_comp.py` - uncertainties in a hierarchical model
- `examples/distrib/distrib_packages_examples.py` - the raw libsbml distrib elements
