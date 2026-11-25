# Distributions and Uncertainties (distrib)

Distrib records uncertainty about a model element and adds probability distributions to SBML formulas. An uncertainty can preserve the statistics from a fit. A distribution function in an initial assignment tells a compatible simulator to draw a starting value.

## Record summary statistics

A fit estimates a concentration of 5 mM from 25 observations. Store the mean, standard deviation, standard error of the mean, variance and sample size on the estimated parameter. Use `value` to give a statistic directly or `var` to refer to another model element by its SBML ID. Here the standard deviation refers to a named model parameter that already carries the concentration unit.

Run the examples on this page in order. The first block defines the units and a helper that writes, validates and reloads each SBML Level 3 Version 1 document.

```python
from pathlib import Path

import libsbml

from sbmlutils.factory import (
    InitialAssignment,
    Model,
    Package,
    Parameter,
    UncertParameter,
    UncertSpan,
    Uncertainty,
    UnitDefinition,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml


class U(Units):
    """Units for a concentration estimate and its variance."""

    mM = UnitDefinition("mM", "mmole/litre")
    mM_squared = UnitDefinition("mM_squared", "(mmole/litre)**2")


def write_distrib(model: Model) -> libsbml.SBMLDocument:
    """Write and validate an uncertainty model, then reload it."""
    result = create_model(model, Path(f"{model.sid}.xml"), raise_on_error=True)
    return read_sbml(result.sbml_path)


estimate = Parameter(
    "estimate",
    value=5.0,
    unit=U.mM,
    uncertainties=[
        Uncertainty(
            uncertParameters=[
                UncertParameter(libsbml.DISTRIB_UNCERTTYPE_MEAN, value=5.0, unit=U.mM),
                UncertParameter(
                    libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION, var="fitted_sd"
                ),
                UncertParameter(
                    libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR, value=0.06, unit=U.mM
                ),
                UncertParameter(
                    libsbml.DISTRIB_UNCERTTYPE_VARIANCE, value=0.09, unit=U.mM_squared
                ),
                UncertParameter(
                    libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE,
                    value=25,
                    unit=U.dimensionless,
                ),
            ]
        )
    ],
)
fit = Model(
    "concentration_fit",
    packages=[Package.DISTRIB_V1],
    units=U,
    parameters=[Parameter("fitted_sd", value=0.3, unit=U.mM), estimate],
)
doc = write_distrib(fit)
sbml_model = doc.getModel()
uncertainty = sbml_model.getParameter("estimate").getPlugin("distrib").getUncertainty(0)
statistics = {item.getType(): item for item in uncertainty.getListOfUncertParameters()}
assert statistics[libsbml.DISTRIB_UNCERTTYPE_MEAN].getValue() == 5.0
sd = statistics[libsbml.DISTRIB_UNCERTTYPE_STANDARDDEVIATION]
assert sd.getVar() == "fitted_sd"
sd_parameter = sbml_model.getParameter(sd.getVar())
assert (sd_parameter.getValue(), sd_parameter.getUnits()) == (0.3, "mM")
assert statistics[libsbml.DISTRIB_UNCERTTYPE_STANDARDERROR].getValue() == 0.06
variance = statistics[libsbml.DISTRIB_UNCERTTYPE_VARIANCE]
assert (variance.getValue(), variance.getUnits()) == (0.09, "mM_squared")
assert statistics[libsbml.DISTRIB_UNCERTTYPE_SAMPLESIZE].getValue() == 25
```

Other single-value types include median, mode, coefficient of variation, skewness and kurtosis. Use the type that matches the reported statistic. For example, standard deviation describes spread, while standard error here describes precision of the estimated mean.

## Add intervals and reference their bounds

Extend the fit with a measured range and a 95% confidence interval for the mean. A range records two numerical endpoints using `valueLower` and `valueUpper`. The confidence interval uses `varLower` and `varUpper` to look up its endpoints in model parameters. The interval's name supplies the confidence level.

```python
fit.parameters.extend(
    [
        Parameter("ci_lower", value=4.88, unit=U.mM),
        Parameter("ci_upper", value=5.12, unit=U.mM),
    ]
)
estimate.uncertainties[0].uncertParameters.extend(
    [
        UncertSpan(
            libsbml.DISTRIB_UNCERTTYPE_RANGE,
            valueLower=4.3,
            valueUpper=5.7,
            unit=U.mM,
            sid="observed_range",
        ),
        UncertSpan(
            libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL,
            varLower="ci_lower",
            varUpper="ci_upper",
            sid="mean_ci",
            name="95% confidence interval for the mean",
        ),
    ]
)
fit.sid = "concentration_intervals"
doc = write_distrib(fit)
sbml_model = doc.getModel()
uncertainty = sbml_model.getParameter("estimate").getPlugin("distrib").getUncertainty(0)
children = uncertainty.getListOfUncertParameters()
observed_range = children.get("observed_range")
assert observed_range.getType() == libsbml.DISTRIB_UNCERTTYPE_RANGE
assert (observed_range.getValueLower(), observed_range.getValueUpper()) == (4.3, 5.7)
assert observed_range.getUnits() == "mM"
interval = children.get("mean_ci")
assert interval.getType() == libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL
assert (interval.getVarLower(), interval.getVarUpper()) == ("ci_lower", "ci_upper")
assert sbml_model.getParameter(interval.getVarUpper()).getValue() == 5.12
```

An `UncertSpan` can also represent a credible interval or an interquartile range. Pass spans and single-value statistics together in `uncertParameters` to preserve their order in SBML.

## Describe a distribution and sample at initialization

`Uncertainty(formula=...)` attaches a distribution to describe a parameter. An `InitialAssignment` containing a distribution function uses a draw as the starting value. This model records a normal distribution on `nominal_concentration`, draws a separate concentration from a normal distribution truncated to the interval from 4 to 6 mM, and draws a dilution fraction uniformly from 0.8 to 1. All arguments to `normal` in this example have concentration units.

```python
sampling = Model(
    "concentration_sampling",
    packages=[Package.DISTRIB_V1],
    units=U,
    parameters=[
        Parameter(
            "nominal_concentration",
            value=5.0,
            unit=U.mM,
            uncertainties=[Uncertainty(formula="normal(5 mM, 0.3 mM)")],
        ),
        Parameter("sampled_concentration", unit=U.mM),
        Parameter("dilution_fraction", unit=U.dimensionless),
    ],
    assignments=[
        InitialAssignment(
            "sampled_concentration", "normal(5 mM, 0.3 mM, 4 mM, 6 mM)", unit=U.mM
        ),
        InitialAssignment(
            "dilution_fraction", "uniform(0.8 dimensionless, 1 dimensionless)"
        ),
    ],
)
doc = write_distrib(sampling)
sbml_model = doc.getModel()
nominal = sbml_model.getParameter("nominal_concentration")
distribution = nominal.getPlugin("distrib").getUncertainty(0).getUncertParameter(0)
assert nominal.getValue() == 5.0
assert distribution.getType() == libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION
assert (
    distribution.getDefinitionURL() == "http://www.sbml.org/sbml/symbols/distrib/normal"
)
assert libsbml.formulaToL3String(distribution.getMath()) == "normal(5 mM, 0.3 mM)"
truncated = sbml_model.getInitialAssignmentBySymbol("sampled_concentration").getMath()
assert truncated.getType() == libsbml.AST_DISTRIB_FUNCTION_NORMAL
assert libsbml.formulaToL3String(truncated) == "normal(5 mM, 0.3 mM, 4 mM, 6 mM)"
uniform = sbml_model.getInitialAssignmentBySymbol("dilution_fraction").getMath()
assert uniform.getType() == libsbml.AST_DISTRIB_FUNCTION_UNIFORM
assert (
    libsbml.formulaToL3String(uniform) == "uniform(0.8 dimensionless, 1 dimensionless)"
)
```

The four arguments to this form of `normal` are the mean, standard deviation, lower truncation bound and upper truncation bound. The simulator must support distrib to evaluate these initial assignments.

## Describe an external distribution with nested parameters

An external distribution can carry its own parameters inside the distribution element. This example uses the Geometric 1 distribution from ProbOnto to describe the wait for a first success. The nested `EXTERNALPARAMETER` stores the success probability. The definition URLs identify the distribution and the meaning of its parameter.

```python
probonto = "http://www.probonto.org/ontology#"
trials = Model(
    "trials_to_success",
    packages=[Package.DISTRIB_V1],
    parameters=[
        Parameter(
            "trials",
            value=3,
            unit=U.dimensionless,
            uncertainties=[
                Uncertainty(
                    uncertParameters=[
                        UncertParameter(
                            libsbml.DISTRIB_UNCERTTYPE_DISTRIBUTION,
                            name="Geometric 1",
                            definitionURL=probonto + "PROB_k0000782",
                            uncertParameters=[
                                UncertParameter(
                                    libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER,
                                    value=0.4,
                                    unit=U.dimensionless,
                                    name="Success probability",
                                    definitionURL=probonto + "PROB_k0000789",
                                )
                            ],
                        )
                    ]
                )
            ],
        )
    ],
)
doc = write_distrib(trials)
parameter = doc.getModel().getParameter("trials")
distribution = parameter.getPlugin("distrib").getUncertainty(0).getUncertParameter(0)
assert distribution.getDefinitionURL() == probonto + "PROB_k0000782"
success_probability = distribution.getUncertParameter(0)
assert success_probability.getType() == libsbml.DISTRIB_UNCERTTYPE_EXTERNALPARAMETER
assert success_probability.getDefinitionURL() == probonto + "PROB_k0000789"
assert success_probability.getValue() == 0.4
```

See [Distributions and uncertainties](../distrib.md) for the supported distributions and round-trip behavior.
