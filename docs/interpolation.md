# Interpolation

A model often has to follow measured data: a plasma concentration over time, a dose response curve, an input which was recorded rather than computed. `sbmlutils.data.interpolation` turns a table of data points into an SBML model which evaluates the interpolation, so the data can be used inside a simulation like any other quantity.

## From a data frame

```python
import pandas as pd

from sbmlutils.data.interpolation import INTERPOLATION_LINEAR, Interpolation

data = pd.DataFrame({
    "time": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0],
    "y": [0.0, 2.0, 1.0, 1.5, 2.5, 3.5],
    "z": [10.0, 5.0, 2.5, 1.25, 0.6, 0.3],
})

interpolation = Interpolation(data=data, method=INTERPOLATION_LINEAR)
interpolation.write_sbml_to_file("interpolation.xml")
```

The first column is the independent variable, every other column is interpolated against it. Each becomes a parameter with an assignment rule which evaluates the interpolation, so simulating the model at time `t` gives the interpolated `y` and `z`.

`from_csv` and `from_tsv` read the data from a file:

```python
interpolation = Interpolation.from_csv("data.csv", method="linear")
interpolation = Interpolation.from_tsv("data.tsv")
```

`write_sbml_to_string()` returns the SBML instead of writing a file.

## The methods

The methods are the module constants of `sbmlutils.data.interpolation`:

| method | value | what it does |
| --- | --- | --- |
| `INTERPOLATION_CONSTANT` | `"constant"` | the value of the previous data point, a step function |
| `INTERPOLATION_LINEAR` | `"linear"` | a straight line between two data points |
| `INTERPOLATION_CUBIC_SPLINE` | `"cubic spline"` | a natural cubic spline through all data points |

All three go exactly through the data points; they differ in what happens between them. The formulas are piecewise expressions over the independent variable, so the model is valid SBML which any simulator evaluates.

The data is checked when the `Interpolation` is created: it needs at least two columns and three rows, and the first column has to be ascending. A table which is not sorted is sorted, with a warning.

## Simulating an interpolation

```python
import roadrunner

interpolation.write_sbml_to_file("interpolation.xml")

r = roadrunner.RoadRunner("interpolation.xml")
r.timeCourseSelections = ["time", "y", "z"]
s = r.simulate(0, 5, steps=50)
```

## Examples

`examples/interpolation/` interpolates the same data with all three methods and plots the simulated result against the data points:

```bash
python -m examples.interpolation.interpolation
python -m examples.interpolation.pancreas
```

Both write their figure into the current working directory; no window is opened.
